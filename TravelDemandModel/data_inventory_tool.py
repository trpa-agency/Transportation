#!/usr/bin/env python
"""
data_inventory_tool.py  —  Data Source Discovery & Archival

Scans every .py and .ipynb file under a target directory, extracts all data
source references it can find, archives them, and writes a master
DataInventory_Record.csv.

Usage
-----
    python data_inventory_tool.py <directory>
        [--archive  <path>]      Output root  (default: <directory>/_inventory)
        [--gdb-name <name>]      GDB filename (default: DataInventory.gdb)
        [--csv-dir  <name>]      CSV subfolder (default: DataInputs)
        [--dry-run]              Discover only; print sources, no fetch/copy

What it archives
----------------
    REST feature services  →  GDB feature class if spatial, otherwise CSV
    JSON web APIs          →  CSV
    SQL Server tables      →  CSV  (geometry columns stripped automatically)
    Local CSV / Parquet / Excel / JSON / Pickle  →  copied to archive

Credentials
-----------
    SQL Server reads require environment variables DB_USER and DB_PASSWORD.
    Feature services and JSON APIs are fetched anonymously (no token).
"""

import argparse
import datetime
import json
import os
import re
import shutil
import sys
from pathlib import Path

import pandas as pd

# ── Optional heavy dependencies (degrade gracefully if absent) ─────────────────
try:
    import arcpy
    HAS_ARCPY = True
except ImportError:
    HAS_ARCPY = False

try:
    from arcgis.features import FeatureLayer
    from arcgis.geometry import Geometry
    HAS_ARCGIS = True
except ImportError:
    HAS_ARCGIS = False

try:
    from sqlalchemy.engine import URL as SqlURL
    from sqlalchemy import create_engine
    HAS_SQL = True
except ImportError:
    HAS_SQL = False

# ── SQL Server settings (mirrors utils.py) ────────────────────────────────────
_SQL_SERVERS = {'sde': 'sql12', 'sde_tabular': 'sql12', 'tahoebmpsde': 'sql14'}
_SQL_DRIVER  = 'ODBC Driver 17 for SQL Server'

# ── File extensions treated as local data sources ─────────────────────────────
_LOCAL_READ_EXTS = {
    '.csv': 'csv', '.parquet': 'parquet', '.geoparquet': 'parquet',
    '.xlsx': 'excel', '.xls': 'excel',
    '.json': 'json_file',
    '.pkl': 'pickle', '.pickle': 'pickle',
}

# ── Substrings that indicate a line is writing, not reading ───────────────────
_WRITE_SIGNALS = (
    '.to_csv(', '.to_parquet(', '.to_excel(', 'to_featureclass(',
    'shutil.copy', '.write(', 'mkdir', 'makedirs', '.save(',
)

# ──────────────────────────────────────────────────────────────────────────────
# DISCOVERY
# ──────────────────────────────────────────────────────────────────────────────

def _extract_code(path: Path) -> str:
    """Return all source code from a .py or .ipynb file as a single string."""
    try:
        if path.suffix == '.ipynb':
            nb = json.loads(path.read_text(encoding='utf-8'))
            return '\n'.join(
                ''.join(c.get('source', []))
                for c in nb.get('cells', [])
                if c.get('cell_type') == 'code'
            )
        return path.read_text(encoding='utf-8')
    except Exception:
        return ''


def _extract_string_vars(code: str) -> dict:
    """
    Extract simple upper-case string variable assignments, e.g.
        BASE_URL = 'https://maps.trpa.org/server/rest/services'
    Returns {VAR_NAME: value}.
    """
    pattern = re.compile(
        r'^([A-Z_][A-Z0-9_]*)\s*=\s*[fF]?[\'"]([^\'"]+)[\'"]',
        re.MULTILINE,
    )
    return {m.group(1): m.group(2) for m in pattern.finditer(code)}


def _substitute(text: str, variables: dict) -> str:
    """Replace {VAR} placeholders in text using variables dict."""
    def _repl(m):
        key = m.group(1).split('.')[0].split('[')[0]
        return variables.get(key, m.group(0))
    return re.sub(r'\{([A-Za-z_]\w*(?:\.\w+|\[\d+\])*)\}', _repl, text)


def _is_output_line(line: str) -> bool:
    return any(sig in line for sig in _WRITE_SIGNALS) or line.lstrip().startswith('#')


def _find_enclosing_line(code: str, pos: int) -> str:
    start = code.rfind('\n', 0, pos) + 1
    end   = code.find('\n', pos)
    return code[start: end if end >= 0 else len(code)]


def _normalize(ref: str) -> str:
    return ref.strip().lower().replace('\\', '/')


def discover_sources(target_dir: Path) -> list[dict]:
    """
    Scan all .py and .ipynb files in target_dir and return a deduplicated list
    of discovered data source dicts.

    Each dict has: type, ref, scripts_used_in, sql_db (sql only)
    """
    scripts = [
        p for p in (list(target_dir.rglob('*.py')) + list(target_dir.rglob('*.ipynb')))
        if not any(skip in p.parts for skip in ('__pycache__', '.ipynb_checkpoints', 'Archive'))
    ]

    raw: list[dict] = []
    for script in scripts:
        raw.extend(_discover_in_file(script, target_dir))

    # Deduplicate by (type, normalized ref)
    seen:    dict[tuple, dict] = {}
    scripts_map: dict[tuple, set] = {}

    for src in raw:
        key = (src['type'], _normalize(src['ref']))
        if key not in seen:
            seen[key] = {k: v for k, v in src.items() if k != 'script'}
            scripts_map[key] = set()
        scripts_map[key].add(src['script'])

    results = []
    for key, src in seen.items():
        src['scripts_used_in'] = sorted(scripts_map[key])
        results.append(src)

    return results


def _discover_in_file(script: Path, target_dir: Path) -> list[dict]:
    code = _extract_code(script)
    if not code:
        return []

    variables = _extract_string_vars(code)
    expanded  = _substitute(code, variables)  # resolve {VAR} placeholders

    sources: list[dict] = []
    seen_refs: set[str] = set()

    def _add(src_type: str, ref: str, **extra):
        ref = ref.strip()
        if not ref or ref in seen_refs:
            return
        seen_refs.add(ref)
        sources.append({'type': src_type, 'ref': ref, 'script': str(script), **extra})

    # ── 1. Feature services ───────────────────────────────────────────────────
    # 1a. Literal URL in FeatureLayer() or get_fs_data*() call
    for pat in (
        re.compile(r"""FeatureLayer\(\s*f?['"]([^'"]+)['"]"""),
        re.compile(r"""get_fs_data(?:_spatial|_query|_spatial_query)?\(\s*f?['"]([^'"]+)['"]"""),
    ):
        for m in pat.finditer(expanded):
            line = _find_enclosing_line(expanded, m.start())
            if _is_output_line(line):
                continue
            url = m.group(1).strip()
            if url.startswith('http'):
                _add('feature_service', url)

    # 1b. URL-shaped variable assignments that look like REST feature services
    #     e.g. PARCEL_URL = f"{BASE_URL}/Existing_Development/MapServer/2"
    #     After substitution, 'expanded' contains the resolved URL string.
    _fs_url_pat = re.compile(
        r"""(https?://[^\s'"}\)]+/rest/services/[^\s'"}\)]+/(?:Map|Feature)Server/\d+)"""
    )
    for m in _fs_url_pat.finditer(expanded):
        url = m.group(1).rstrip(')')
        line = _find_enclosing_line(expanded, m.start())
        if not _is_output_line(line):
            _add('feature_service', url)

    # ── 2. JSON APIs: pd.read_json(http_url) ─────────────────────────────────
    for m in re.finditer(r"""pd\.read_json\(\s*f?['"]((https?://)[^'"]+)['"]""", expanded):
        line = _find_enclosing_line(expanded, m.start())
        if not _is_output_line(line):
            _add('json_api', m.group(1).strip())

    # ── 3. SQL queries: pd.read_sql / read_sql_no_geom with literal string ───
    # Detect which db this script connects to
    sql_db = 'sde'
    db_match = re.search(r"""(?:get_conn|get_sql_engine)\(\s*['"](\w+)['"]""", code)
    if db_match:
        sql_db = db_match.group(1)

    for pat in (
        re.compile(r"""(?:pd\.read_sql|read_sql_no_geom)\(\s*f?['"]([^'"]*(?:SELECT|select)[^'"]+)['"]"""),
        re.compile(r"""(?:pd\.read_sql|read_sql_no_geom)\(\s*f?['"]([^'"]*(?:FROM|from)[^'"]+)['"]"""),
    ):
        for m in pat.finditer(expanded):
            line = _find_enclosing_line(expanded, m.start())
            if not _is_output_line(line):
                query = m.group(1).strip()
                tbl_match = re.search(r'FROM\s+([\w\.\[\]]+)', query, re.IGNORECASE)
                sql_table = tbl_match.group(1).replace('[', '').replace(']', '') if tbl_match else ''
                _add('sql', query, sql_db=sql_db, sql_table=sql_table)

    # ── 4a. Local files: pd.read_*(PATH / 'filename.ext') ────────────────────
    #    Captures the last string component in a Path chain inside read_*()
    path_chain = re.compile(
        r"""pd\.read_(?:csv|parquet|excel)\s*\([^)]*?/\s*['"]([\w.\- ]+\.\w+)['"]\s*\)""",
        re.DOTALL,
    )
    for m in path_chain.finditer(code):
        line = _find_enclosing_line(code, m.start())
        if _is_output_line(line):
            continue
        filename = m.group(1).strip()
        ext = Path(filename).suffix.lower()
        if ext in _LOCAL_READ_EXTS:
            # Try to resolve the full path; fall back to filename-only search
            resolved = _resolve_filename(filename, script.parent, target_dir)
            ref = str(resolved) if resolved else filename
            _add(_LOCAL_READ_EXTS[ext], ref)

    # ── 4b. Local files: pd.read_*('literal/path.ext') ───────────────────────
    literal_read = re.compile(
        r"""pd\.read_(?:csv|parquet|excel)\s*\(\s*[fF]?['"]([^'"]+\.\w+)['"]""",
    )
    for m in literal_read.finditer(expanded):
        line = _find_enclosing_line(expanded, m.start())
        if _is_output_line(line):
            continue
        ref = m.group(1).strip()
        if ref.startswith('http'):
            continue  # already caught as json_api or feature_service
        ext = Path(ref).suffix.lower()
        if ext in _LOCAL_READ_EXTS:
            resolved = _resolve_path(ref, script.parent, target_dir)
            final = str(resolved) if resolved else ref
            _add(_LOCAL_READ_EXTS[ext], final)

    # ── 4c. read_file() / read_excel() custom helpers ────────────────────────
    for pat in (
        re.compile(r"""read_file\(\s*f?['"]([^'"]+)['"]"""),
        re.compile(r"""read_excel\(\s*f?['"]([^'"]+)['"]"""),
    ):
        for m in pat.finditer(expanded):
            line = _find_enclosing_line(expanded, m.start())
            if _is_output_line(line):
                continue
            ref = m.group(1).strip()
            ext = Path(ref).suffix.lower()
            if ext in _LOCAL_READ_EXTS:
                resolved = _resolve_path(ref, script.parent, target_dir)
                final = str(resolved) if resolved else ref
                _add(_LOCAL_READ_EXTS[ext], final)

    # ── 4d. Path / 'filename' division outside of pd.read_* ──────────────────
    #    e.g.  SOME_DIR / 'lookup.csv'  or  NB_DIR / 'Base' / 'data' / 'file.csv'
    path_div = re.compile(r"""\w+\s*/\s*['"]([\w.\- ]+\.\w+)['"]\s*(?:\)|,|\n)""")
    for m in path_div.finditer(code):
        line = _find_enclosing_line(code, m.start())
        if _is_output_line(line):
            continue
        filename = m.group(1).strip()
        ext = Path(filename).suffix.lower()
        if ext not in _LOCAL_READ_EXTS:
            continue
        resolved = _resolve_filename(filename, script.parent, target_dir)
        ref = str(resolved) if resolved else filename
        # Only add if not already captured by 4a/4b
        if _normalize(ref) not in seen_refs and _normalize(filename) not in seen_refs:
            _add(_LOCAL_READ_EXTS[ext], ref)

    # ── 5. JSON config globs: configs_final/*.json ────────────────────────────
    for m in re.finditer(r"""glob\(\s*['"]\*\.json['"]\)""", code):
        # Look for the Path the glob is called on
        line = _find_enclosing_line(code, m.start())
        dir_match = re.search(r'(\w+)\.glob', line)
        if dir_match:
            var_name = dir_match.group(1)
            base = variables.get(var_name, '')
            if base:
                glob_dir = _resolve_path(base, script.parent, target_dir)
                if glob_dir and glob_dir.is_dir():
                    for jf in sorted(glob_dir.glob('*.json')):
                        _add('json_file', str(jf))

    return sources


# ── Path resolution helpers ────────────────────────────────────────────────────

def _resolve_path(ref: str, script_dir: Path, target_dir: Path) -> Path | None:
    """Try to resolve a path reference to an existing file."""
    p = Path(ref)
    # Absolute
    if p.is_absolute() and p.exists():
        return p
    # Relative to script
    candidate = script_dir / p
    if candidate.exists():
        return candidate.resolve()
    # Relative to target dir
    candidate = target_dir / p
    if candidate.exists():
        return candidate.resolve()
    # Search by filename
    return _resolve_filename(p.name, script_dir, target_dir)


def _resolve_filename(filename: str, script_dir: Path, target_dir: Path) -> Path | None:
    """Search target_dir (and script_dir parent) for a file with this name."""
    for search_root in (target_dir, script_dir.parent):
        matches = [
            p for p in search_root.rglob(filename)
            if not any(skip in p.parts for skip in ('__pycache__', '.ipynb_checkpoints', '_inventory'))
        ]
        if matches:
            # Prefer the match closest in depth to script_dir
            return min(matches, key=lambda p: len(p.parts))
    return None


# ──────────────────────────────────────────────────────────────────────────────
# ARCHIVING
# ──────────────────────────────────────────────────────────────────────────────

def _safe_name(ref: str, suffix: str = '') -> str:
    """Turn a URL or path into a safe archive name stem."""
    # Use last URL segment or filename stem
    stem = Path(ref.rstrip('/')).stem or 'data'
    stem = re.sub(r'[^\w]', '_', stem).strip('_')[:50]
    if stem and stem[0].isdigit():
        stem = 'D_' + stem
    return stem + suffix


def _fix_sedf_geometry(sdf):
    """Coerce SHAPE column to ArcGIS Geometry objects (arcgis/geopandas conflict fix)."""
    if 'SHAPE' not in sdf.columns:
        return sdf
    result = sdf.copy()
    def _coerce(g):
        if g is None or isinstance(g, Geometry):
            return g
        if hasattr(g, '__geo_interface__'):
            return Geometry(g.__geo_interface__)
        return g
    result['SHAPE'] = [_coerce(g) for g in result['SHAPE'].to_numpy(dtype=object)]
    return result


def _read_sql_no_geom(query: str, engine) -> pd.DataFrame:
    """Execute a query, stripping geometry/geography columns from SELECT *."""
    with engine.connect() as conn:
        if not re.search(r'SELECT\s+\*', query, re.IGNORECASE):
            return pd.read_sql(query, conn)
        m = re.search(r'FROM\s+([\w\.\[\]]+)', query, re.IGNORECASE)
        if not m:
            return pd.read_sql(query, conn)
        table_ref = m.group(1).replace('[', '').replace(']', '')
        parts  = table_ref.split('.')
        schema = parts[-2] if len(parts) >= 2 else None
        table  = parts[-1]
        s_clause = f"TABLE_SCHEMA = '{schema}' AND " if schema else ''
        col_q = (
            f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
            f"WHERE {s_clause}TABLE_NAME = '{table}' "
            f"AND DATA_TYPE NOT IN ('geometry', 'geography') "
            f"ORDER BY ORDINAL_POSITION"
        )
        df_cols = pd.read_sql(col_q, conn)
        if df_cols.empty:
            return pd.read_sql(query, conn)
        col_list  = ', '.join(f'[{c}]' for c in df_cols['COLUMN_NAME'])
        new_query = re.sub(r'SELECT\s+\*', f'SELECT {col_list}', query, flags=re.IGNORECASE)
        return pd.read_sql(new_query, conn)


def _archive_feature_service(src: dict, gdb_path: Path, csv_dir: Path) -> dict:
    url = src['ref']
    print(f"  [feature_service] {url[:80]}")

    if not HAS_ARCGIS:
        return _err(src, 'arcgis library not available')

    try:
        fl  = FeatureLayer(url)
        sdf = pd.DataFrame.spatial.from_layer(fl)
        has_geom = ('SHAPE' in sdf.columns and sdf['SHAPE'].notna().any())

        if has_geom and HAS_ARCPY:
            fc_name = _safe_name(url)
            out_fc  = str(gdb_path / fc_name)
            sdf = _fix_sedf_geometry(sdf)
            if arcpy.Exists(out_fc):
                arcpy.management.Delete(out_fc)
            sdf.spatial.to_featureclass(out_fc)
            print(f"    → {len(sdf):,} features → GDB:{fc_name}")
            return _ok(src, len(sdf), 'Feature Class (GDB)', out_fc)

        # Tabular fallback
        out = csv_dir / (_safe_name(url, '_svc.csv'))
        sdf.drop(columns=['SHAPE'], errors='ignore').to_csv(out, index=False)
        print(f"    → {len(sdf):,} rows → {out.name}")
        return _ok(src, len(sdf), 'CSV', str(out))

    except Exception as e:
        print(f"    ERROR: {e}")
        return _err(src, str(e))


def _archive_json_api(src: dict, csv_dir: Path) -> dict:
    url = src['ref']
    print(f"  [json_api] {url[:80]}")
    try:
        df  = pd.read_json(url)
        out = csv_dir / (_safe_name(url, '_api.csv'))
        df.to_csv(out, index=False)
        print(f"    → {len(df):,} rows → {out.name}")
        return _ok(src, len(df), 'CSV', str(out))
    except Exception as e:
        print(f"    ERROR: {e}")
        return _err(src, str(e))


def _archive_sql(src: dict, csv_dir: Path) -> dict:
    query = src['ref']
    db    = src.get('sql_db', 'sde')
    table = src.get('sql_table', 'query')
    print(f"  [sql] {query[:80]}")

    if not HAS_SQL:
        return _err(src, 'sqlalchemy not installed')

    db_user = os.environ.get('DB_USER')
    db_pass = os.environ.get('DB_PASSWORD')
    if not db_user:
        print("    SKIP — DB_USER env var not set")
        return _skip(src, 'DB_USER environment variable not set')

    server = _SQL_SERVERS.get(db.lower(), 'sql12')
    try:
        conn_str = (f'DRIVER={_SQL_DRIVER};SERVER={server};DATABASE={db};'
                    f'UID={db_user};PWD={db_pass}')
        engine = create_engine(
            SqlURL.create('mssql+pyodbc', query={'odbc_connect': conn_str})
        )
        df  = _read_sql_no_geom(query, engine)
        out = csv_dir / (_safe_name(table, '_sql.csv'))
        df.to_csv(out, index=False)
        print(f"    → {len(df):,} rows → {out.name}")
        return _ok(src, len(df), 'CSV', str(out))
    except Exception as e:
        print(f"    ERROR: {e}")
        return _err(src, str(e))


def _archive_local(src: dict, csv_dir: Path) -> dict:
    ref  = src['ref']
    path = Path(ref)
    print(f"  [local] {path.name}")

    if not path.exists():
        print(f"    SKIP — not found: {ref}")
        return _skip(src, f'File not found: {ref}')

    # Handle name collisions in archive
    dest = csv_dir / path.name
    if dest.exists() and dest.resolve() != path.resolve():
        i = 1
        while dest.exists():
            dest = csv_dir / f'{path.stem}_{i}{path.suffix}'
            i += 1

    try:
        shutil.copy2(path, dest)
        # Approximate row count for text files
        try:
            rows = max(sum(1 for _ in path.open(encoding='utf-8', errors='replace')) - 1, 0)
        except Exception:
            rows = 0
        print(f"    → {dest.name}")
        return _ok(src, rows, 'File (copy)', str(dest))
    except Exception as e:
        print(f"    ERROR: {e}")
        return _err(src, str(e))


# ── Logging helpers ────────────────────────────────────────────────────────────

def _ok(src, count, archive_type, location):
    return {**src, 'status': 'SUCCESS', 'record_count': count,
            'archive_type': archive_type, 'archive_location': location, 'error': ''}

def _err(src, msg):
    return {**src, 'status': 'ERROR', 'record_count': 0,
            'archive_type': '', 'archive_location': '', 'error': msg}

def _skip(src, msg):
    return {**src, 'status': 'SKIP', 'record_count': 0,
            'archive_type': '', 'archive_location': '', 'error': msg}


# ──────────────────────────────────────────────────────────────────────────────
# INVENTORY
# ──────────────────────────────────────────────────────────────────────────────

_TYPE_LABELS = {
    'feature_service': 'ArcGIS Feature Service',
    'json_api':        'JSON Web API',
    'sql':             'SQL Server Table',
    'csv':             'Local CSV',
    'parquet':         'Local Parquet',
    'excel':           'Local Excel',
    'pickle':          'Local Pickle',
    'json_file':       'Local JSON',
    'gdb_read':        'GDB Feature Class',
}


def build_inventory(results: list[dict], target_dir: Path,
                    snapshot_ts: str, snapshot_date: str) -> pd.DataFrame:
    """Convert archive results to a tidy inventory DataFrame."""
    rows = []
    for i, r in enumerate(results, 1):
        src_type = r.get('type', '')
        scripts  = [
            str(Path(s).relative_to(target_dir))
            for s in r.get('scripts_used_in', [r.get('script', '')])
        ]
        rows.append({
            'source_id':          f'DS_{src_type.upper()}_{i:03d}',
            'source_type':        _TYPE_LABELS.get(src_type, src_type),
            'datasource_ref':     r.get('ref', ''),
            'sql_db':             r.get('sql_db', ''),
            'scripts_used_in':    ' | '.join(scripts),
            'archive_type':       r.get('archive_type', ''),
            'archive_location':   r.get('archive_location', ''),
            'record_count':       r.get('record_count', ''),
            'status':             r.get('status', 'NOT_RUN'),
            'error_message':      r.get('error', ''),
            'snapshot_date':      snapshot_date,
            'snapshot_timestamp': snapshot_ts,
        })
    return pd.DataFrame(rows)


# ──────────────────────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────────────────────

def run(target_dir: Path, archive_root: Path, gdb_name: str,
        csv_dir_name: str, dry_run: bool) -> None:

    ts            = datetime.datetime.now()
    snapshot_date = ts.strftime('%Y-%m-%d')
    snapshot_ts   = ts.strftime('%Y-%m-%d %H:%M:%S')

    print('=' * 60)
    print('  DATA INVENTORY TOOL')
    print('=' * 60)
    print(f'  Target    : {target_dir}')
    print(f'  Archive   : {archive_root}')
    print(f'  Snapshot  : {snapshot_ts}')
    print(f'  arcpy     : {"available" if HAS_ARCPY else "NOT available — spatial archiving disabled"}')
    print(f'  arcgis    : {"available" if HAS_ARCGIS else "NOT available — feature services disabled"}')
    print(f'  sqlalchemy: {"available" if HAS_SQL else "NOT available — SQL disabled"}')
    print()

    # ── Phase 1: Discover ────────────────────────────────────────────────────
    print('Phase 1: Discovering data sources...')
    sources = discover_sources(target_dir)

    type_counts = {}
    for s in sources:
        type_counts[s['type']] = type_counts.get(s['type'], 0) + 1
    for t, n in sorted(type_counts.items()):
        print(f'  {_TYPE_LABELS.get(t, t):30s}  {n}')
    print(f'  {"TOTAL":30s}  {len(sources)}')

    if dry_run:
        print('\n[DRY RUN] Discovered sources:')
        for src in sources:
            scripts = ', '.join(Path(s).name for s in src['scripts_used_in'][:2])
            print(f'  [{src["type"]:16}] {str(src["ref"])[:65]}')
            print(f'                     in: {scripts}')
        print('\nRe-run without --dry-run to archive.')
        return

    # ── Phase 2: Create archive directories ──────────────────────────────────
    print('\nPhase 2: Setting up archive...')
    csv_dir  = archive_root / csv_dir_name
    gdb_path = archive_root / gdb_name

    archive_root.mkdir(parents=True, exist_ok=True)
    csv_dir.mkdir(parents=True, exist_ok=True)
    print(f'  CSV dir : {csv_dir}')

    if HAS_ARCPY:
        if not arcpy.Exists(str(gdb_path)):
            arcpy.management.CreateFileGDB(str(gdb_path.parent), gdb_path.name)
            print(f'  GDB created : {gdb_path}')
        else:
            print(f'  GDB exists  : {gdb_path}')
        arcpy.env.workspace       = str(gdb_path)
        arcpy.env.overwriteOutput = True

    # ── Phase 3: Archive ─────────────────────────────────────────────────────
    print('\nPhase 3: Archiving...')

    # Group by type for cleaner output
    by_type: dict[str, list] = {}
    for src in sources:
        by_type.setdefault(src['type'], []).append(src)

    results: list[dict] = []

    _type_order = ['feature_service', 'json_api', 'sql',
                   'csv', 'parquet', 'excel', 'pickle', 'json_file', 'gdb_read']

    for src_type in _type_order + [t for t in by_type if t not in _type_order]:
        group = by_type.get(src_type, [])
        if not group:
            continue
        label = _TYPE_LABELS.get(src_type, src_type)
        print(f'\n  [{label}]  ({len(group)})')

        for src in group:
            if src_type == 'feature_service':
                results.append(_archive_feature_service(src, gdb_path, csv_dir))
            elif src_type == 'json_api':
                results.append(_archive_json_api(src, csv_dir))
            elif src_type == 'sql':
                results.append(_archive_sql(src, csv_dir))
            else:
                results.append(_archive_local(src, csv_dir))

    # ── Phase 4: Write inventory ──────────────────────────────────────────────
    print('\nPhase 4: Writing inventory record...')
    df = build_inventory(results, target_dir, snapshot_ts, snapshot_date)
    inv_path = archive_root / 'DataInventory_Record.csv'
    df.to_csv(inv_path, index=False)

    # ── Summary ───────────────────────────────────────────────────────────────
    ok   = (df['status'] == 'SUCCESS').sum()
    skip = (df['status'] == 'SKIP').sum()
    err  = (df['status'] == 'ERROR').sum()

    print(f'\n{"=" * 60}')
    print(f'  Sources discovered : {len(sources)}')
    print(f'  Archived OK        : {ok}')
    print(f'  Skipped            : {skip}')
    print(f'  Errors             : {err}')
    print(f'  Inventory record   : {inv_path}')
    print(f'{"=" * 60}')

    if err > 0:
        print('\nFailed sources:')
        for _, row in df[df['status'] == 'ERROR'].iterrows():
            print(f'  {row["source_id"]}  {row["datasource_ref"][:60]}')
            print(f'    {row["error_message"][:100]}')


def main():
    parser = argparse.ArgumentParser(
        description='Scan a directory for data sources and archive them.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        'directory',
        help='Root directory to scan (all .py and .ipynb files scanned recursively)',
    )
    parser.add_argument(
        '--archive',
        default=None,
        help='Archive output root (default: <directory>/_inventory)',
    )
    parser.add_argument(
        '--gdb-name',
        default='DataInventory.gdb',
        help='GDB filename (default: DataInventory.gdb)',
    )
    parser.add_argument(
        '--csv-dir',
        default='DataInputs',
        help='CSV subfolder name (default: DataInputs)',
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Discover and print sources without fetching or copying anything',
    )
    args = parser.parse_args()

    target_dir  = Path(args.directory).resolve()
    if not target_dir.is_dir():
        print(f'ERROR: not a directory: {target_dir}', file=sys.stderr)
        sys.exit(1)

    archive_root = Path(args.archive).resolve() if args.archive else target_dir / '_inventory'

    run(
        target_dir   = target_dir,
        archive_root = archive_root,
        gdb_name     = args.gdb_name,
        csv_dir_name = args.csv_dir,
        dry_run      = args.dry_run,
    )


if __name__ == '__main__':
    main()
