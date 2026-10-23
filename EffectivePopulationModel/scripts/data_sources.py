"""
data_sources.py
---------------
Optional derivation of model inputs from their original source data.

The R-Shiny app computed two of its defaults at startup rather than hard-coding
them: the regional entry volume (from a StreetLight InSight origin-destination
export) and the second home count (from the Census ACS). This module reproduces
both so a scenario can be re-based on new data instead of a literal number.

All derivations are OFF by default. When a data_sources block is absent or
disabled, the literal values in the config's inputs block are used and nothing
here is imported. That keeps the model runnable with no network access and no
multi-hundred-megabyte StreetLight CSVs on disk.

Supported sources
-----------------
entry_volume
    Sums "Average Daily O-D Traffic (StL Volume)" over StreetLight OD pairs whose
    pass-through flags classify them as the requested trip types. EI (external
    origin, internal destination) is the inbound-to-basin volume the model wants.

second_homes, resident_population
    Sums a census variable across basin geographies from TRPA's Demographics
    census table. The R app queried the Census Bureau API directly and then
    clipped the result to a basin tract shapefile; TRPA's service is already
    basin-scoped, needs no API key, and is the agency's own copy of the same ACS
    tables, so it replaces both steps. The two sources reconcile exactly: for
    2018 the service returns 26,585 seasonal units and 51,577 residents, the same
    values the Census API returns for the basin tracts.

    The handler is generic over variable_code / dataset / sample_level /
    year_sample, so any variable the table carries can drive any model input.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

# TRPA's Demographics census table. Long format: one row per geography, variable
# and vintage. The layer is already limited to basin geographies.
TRPA_CENSUS_SERVICE = "https://maps.trpa.org/server/rest/services/Demographics/MapServer/28"

# The service caps a single response; requests page through with resultOffset.
SERVICE_PAGE_SIZE = 2000

# StreetLight column names, kept as literals because they come from the vendor export.
COL_VOLUME = "Average Daily O-D Traffic (StL Volume)"
COL_O_PASS = "Origin Zone Is Pass-Through"
COL_D_PASS = "Destination Zone Is Pass-Through"
COL_DAY_TYPE = "Day Type"
COL_DAY_PART = "Day Part"


class DataSourceError(RuntimeError):
    """Raised when a data source is enabled but cannot be read or produces no rows."""


# ==============================================================================
# Entry volume from StreetLight
# ==============================================================================

def classify_trip_types(df: pd.DataFrame) -> pd.Series:
    """
    Label each OD pair II / EI / IE / EE from the pass-through flags.

    A pass-through origin means the trip started outside the region, so
    "external origin, internal destination" (EI) is an inbound trip.
    """
    origin_external = df[COL_O_PASS].astype(str).str.strip().str.lower() == "yes"
    dest_external = df[COL_D_PASS].astype(str).str.strip().str.lower() == "yes"
    return pd.Series(
        np.select(
            [
                ~origin_external & ~dest_external,
                origin_external & ~dest_external,
                ~origin_external & dest_external,
                origin_external & dest_external,
            ],
            ["II", "EI", "IE", "EE"],
            default="unknown",
        ),
        index=df.index,
    )


def entry_volume_from_streetlight(spec: dict, data_dir: Path) -> tuple:
    """
    Compute average daily entry volume from a StreetLight OD export.

    Spec keys
    ---------
    od_csv : str
        Path to the OD CSV. Relative paths resolve against <data_dir>/inputs.
    day_type, day_part : str
        Filters on the StreetLight aggregation columns. Defaults select the
        all-days, all-day slice the R app used.
    trip_types : list of str
        Which classified trip types to sum. Defaults to ["EI"].

    Returns
    -------
    (volume, note) : (float, str)
    """
    csv_name = spec.get("od_csv")
    if not csv_name:
        raise DataSourceError("data_sources.entry_volume is enabled but has no 'od_csv'.")

    csv_path = Path(csv_name)
    if not csv_path.is_absolute():
        csv_path = data_dir / "inputs" / csv_path
    if not csv_path.is_file():
        raise DataSourceError(f"StreetLight OD CSV not found: {csv_path}")

    day_type = spec.get("day_type", "0: All Days (M-Su)")
    day_part = spec.get("day_part", "0: All Day (12am-12am)")
    trip_types = spec.get("trip_types", ["EI"])

    df = pd.read_csv(csv_path, low_memory=False)
    required = {COL_VOLUME, COL_O_PASS, COL_D_PASS, COL_DAY_TYPE, COL_DAY_PART}
    missing = sorted(required - set(df.columns))
    if missing:
        raise DataSourceError(f"{csv_path.name} is missing column(s): {', '.join(missing)}")

    df = df[(df[COL_DAY_TYPE] == day_type) & (df[COL_DAY_PART] == day_part)].copy()
    if df.empty:
        raise DataSourceError(
            f"{csv_path.name} has no rows with Day Type '{day_type}' and Day Part '{day_part}'."
        )

    # StreetLight writes "N/A" into numeric columns where a value is suppressed.
    df["volume"] = pd.to_numeric(df[COL_VOLUME], errors="coerce")
    df["trip_type"] = classify_trip_types(df)

    selected = df[df["trip_type"].isin(trip_types)]
    if selected.empty:
        raise DataSourceError(
            f"{csv_path.name} has no {'/'.join(trip_types)} trips after filtering."
        )

    volume = float(selected["volume"].sum())
    note = (
        f"computed from {csv_path.name}: {'+'.join(trip_types)} trips, "
        f"Day Type '{day_type}', Day Part '{day_part}' "
        f"= {volume:,.0f} average daily vehicles"
    )
    return volume, note


# ==============================================================================
# Census variables from the TRPA Demographics service
# ==============================================================================

def _quote(value) -> str:
    """Quote a value for an ArcGIS where clause, escaping embedded apostrophes."""
    return "'" + str(value).replace("'", "''") + "'"


def build_census_where(spec: dict) -> str:
    """
    Assemble the where clause for one census variable and vintage.

    sample_level must be pinned: the table carries the same variable at tract and
    block group level, and summing both would double count.
    """
    variable_code = spec.get("variable_code")
    if not variable_code:
        raise DataSourceError("A TRPA census data source needs a 'variable_code'.")

    clauses = [f"variable_code = {_quote(variable_code)}"]
    for key, field in (("dataset", "dataset"),
                       ("sample_level", "sample_level")):
        if spec.get(key):
            clauses.append(f"{field} = {_quote(spec[key])}")

    if spec.get("year_sample") is not None:
        clauses.append(f"year_sample = {float(spec['year_sample'])}")

    # Soft-deleted rows carry delete_flag = 1; live rows are 0 or null.
    clauses.append("(delete_flag = 0 OR delete_flag IS NULL)")

    if spec.get("where"):
        clauses.append(f"({spec['where']})")

    return " AND ".join(clauses)


def query_census_service(service_url: str, where: str, timeout: float) -> pd.DataFrame:
    """
    Page through an ArcGIS query and return the matching rows.

    ArcGIS caps a single response at the layer's maxRecordCount, so this keeps
    requesting with a growing resultOffset until a page comes back short.
    """
    query_url = service_url.rstrip("/") + "/query"
    rows = []
    offset = 0

    while True:
        params = {
            "f": "json",
            "where": where,
            "outFields": "GEO_ID,value,MarginOfError,year_sample,variable_name,sample_level",
            "returnGeometry": "false",
            "resultOffset": offset,
            "resultRecordCount": SERVICE_PAGE_SIZE,
        }
        url = f"{query_url}?{urllib.parse.urlencode(params)}"

        try:
            with urllib.request.urlopen(url, timeout=timeout) as resp:
                body = resp.read()
        except Exception as e:                       # network or HTTP failure
            raise DataSourceError(f"TRPA census service request failed: {e}") from e

        try:
            payload = json.loads(body)
        except json.JSONDecodeError as e:
            snippet = body[:200].decode("utf-8", "replace").strip().replace("\n", " ")
            raise DataSourceError(
                f"TRPA census service returned a non-JSON response. Check the service URL. "
                f"Response began: {snippet}"
            ) from e

        # ArcGIS reports failures in the body under a 200 status.
        if "error" in payload:
            detail = payload["error"].get("message", payload["error"])
            extra = "; ".join(payload["error"].get("details", []) or [])
            raise DataSourceError(
                f"TRPA census service rejected the query ({detail}{': ' + extra if extra else ''}). "
                f"Where clause was: {where}"
            )

        page = [f["attributes"] for f in payload.get("features", [])]
        rows.extend(page)
        if len(page) < SERVICE_PAGE_SIZE:
            break
        offset += SERVICE_PAGE_SIZE

    return pd.DataFrame(rows)


def census_value_from_trpa_service(spec: dict, data_dir: Path) -> tuple:
    """
    Sum one census variable over the basin geographies in TRPA's census table.

    Spec keys
    ---------
    variable_code : str
        Census variable, including the ACS estimate suffix, e.g. "B25004_006E"
        (seasonal/recreational/occasional use) or "B01003_001E" (total population).
    dataset : str
        Census product, e.g. "acs/acs5". Defaults to the ACS 5-year.
    sample_level : str
        Geography level, e.g. "tract". Defaults to tract. Must be pinned so the
        same variable is not summed at two levels at once.
    year_sample : int
        ACS vintage. The table carries 2011-2024 for the ACS 5-year.
    subtract_units : float
        Units removed after summing, e.g. short-term rentals netted out of the
        seasonal unit count so they are not also counted in the STR segment.
    service_url : str
        Override the default TRPA Demographics census table.
    where : str
        Extra where-clause fragment, e.g. to exclude a specific geography.
    timeout_seconds : float

    Returns
    -------
    (value, note) : (float, str)
    """
    service_url = spec.get("service_url", TRPA_CENSUS_SERVICE)
    timeout = float(spec.get("timeout_seconds", 120))

    # Defaults match the ACS 5-year tract data the R app used.
    spec = {"dataset": "acs/acs5", "sample_level": "tract", **spec}
    where = build_census_where(spec)

    df = query_census_service(service_url, where, timeout)
    if df.empty:
        raise DataSourceError(
            f"TRPA census service returned no rows for: {where}. Check the variable code "
            f"(ACS codes carry an E suffix, e.g. B25004_006E), the dataset, the sample "
            f"level and the vintage."
        )

    # One geography must not appear twice, or the sum double counts.
    duplicated = df["GEO_ID"][df["GEO_ID"].duplicated()].unique()
    if len(duplicated) > 0:
        raise DataSourceError(
            f"TRPA census service returned {len(duplicated)} duplicated geograph(ies) "
            f"for: {where}. Pin 'sample_level', 'dataset' and 'year_sample' so only one "
            f"row per geography matches. First duplicates: {', '.join(duplicated[:5])}"
        )

    values = pd.to_numeric(df["value"], errors="coerce")
    if values.isna().any():
        raise DataSourceError(
            f"{int(values.isna().sum())} of {len(values)} geographies returned a "
            f"non-numeric value for: {where}"
        )

    total = float(values.sum())
    subtract = float(spec.get("subtract_units", 0))
    result = total - subtract

    moe = pd.to_numeric(df.get("MarginOfError"), errors="coerce").sum()
    variable_name = df["variable_name"].dropna().iloc[0] if "variable_name" in df else spec["variable_code"]
    year = spec.get("year_sample", "all years")

    note = (
        f"{spec['variable_code']} ({variable_name}) summed from the TRPA Demographics "
        f"census service: {year} {spec['dataset']}, {len(df)} basin {spec['sample_level']}s, "
        f"{total:,.0f} (summed MOE {moe:,.0f})"
    )
    if subtract:
        note += f" less {subtract:,.0f} = {result:,.0f}"

    return result, note


# ==============================================================================
# Dispatch
# ==============================================================================

# Which handler serves each input. The TRPA census handler is generic, so any
# input that a census variable can supply maps onto it.
HANDLERS = {
    "entry_volume":        entry_volume_from_streetlight,
    "second_homes":        census_value_from_trpa_service,
    "resident_population": census_value_from_trpa_service,
}


def apply_data_sources(inputs: dict, data_sources: dict, data_dir: Path) -> tuple:
    """
    Overwrite inputs with values computed from source data, where enabled.

    Parameters
    ----------
    inputs : dict
        The config's inputs block. Not mutated; a copy is returned.
    data_sources : dict
        Mapping of input name -> spec dict. A spec runs only when its "enabled"
        key is true.
    data_dir : Path
        Root for resolving relative source paths.

    Returns
    -------
    (inputs, provenance, notes) : (dict, dict, list[str])
    """
    inputs = dict(inputs)
    provenance = {}
    notes = []

    unknown = sorted(set(data_sources) - set(HANDLERS))
    if unknown:
        raise DataSourceError(
            f"Unsupported data_sources key(s): {', '.join(unknown)}. "
            f"Supported: {', '.join(sorted(HANDLERS))}."
        )

    for name, spec in data_sources.items():
        if not isinstance(spec, dict) or not spec.get("enabled"):
            continue
        value, note = HANDLERS[name](spec, data_dir)
        previous = inputs.get(name)
        inputs[name] = value
        provenance[name] = "data_source"
        notes.append(f"{name}: {note}")
        if previous is not None:
            notes.append(f"  (config literal {previous:,.0f} overridden by the data source)")

    return inputs, provenance, notes
