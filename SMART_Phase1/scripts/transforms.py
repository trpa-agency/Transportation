"""
Pure transforms between the DERQ API payload shape and the published ArcGIS
feature service schema.

Nothing in this module touches the network, so all of it is unit-testable.

The DERQ API and the feature service disagree on field names -- DERQ returns
`count` and `date`, the layers use `counts` and `Date` -- and the service
schema is frozen because it backs a live dashboard and the Tahoe Open Data
page. Every rename is declared in config.yaml and applied here.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta

import pandas as pd

logger = logging.getLogger(__name__)

# Injected onto every DERQ frame by the fetcher; passed through untouched.
PASSTHROUGH_FIELDS = ("LocationId", "LocationName")

_EPOCH = pd.Timestamp("1970-01-01", tz="UTC")


# ---------------------------------------------------------------------------
# Date handling
# ---------------------------------------------------------------------------


def to_epoch_ms(values: pd.Series) -> pd.Series:
    """
    Convert a series of dates/timestamps to epoch milliseconds (UTC), which is
    the only date representation the ArcGIS REST API accepts.

    Naive timestamps are read as UTC, matching how the existing rows were
    loaded. Unparseable values and NaT become NA rather than raising, so one
    bad record cannot fail a whole day.
    """
    parsed = pd.to_datetime(values, utc=True, errors="coerce")
    # Subtracting the epoch keeps NaT as NA. A direct .astype("int64") would
    # turn NaT into INT64_MIN and silently write garbage dates. Int64 (nullable)
    # keeps the result integral even when some values are null.
    return ((parsed - _EPOCH) // pd.Timedelta("1ms")).astype("Int64")


def parse_day(value: str | date | datetime) -> date:
    """Coerce a 'YYYY-MM-DD' string, date, or datetime to a plain date."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()


def iter_days(start: str | date, end: str | date):
    """Yield every date from start to end inclusive."""
    current, last = parse_day(start), parse_day(end)
    while current <= last:
        yield current
        current += timedelta(days=1)


def trim_to_window(
    df: pd.DataFrame, date_field: str, start: str | date, end: str | date
) -> pd.DataFrame:
    """
    Keep only rows whose date falls inside [start, end].

    Required because the DERQ API interprets startDate/endDate as UTC midnight
    while the data is stamped in local Pacific time, so a request for
    [D1, D2] returns a partial D1-1 (evening only, 28 of 96 intervals) and a
    partial D2-1 (morning only, 68 of 96). Loading a partial boundary day would
    make day_replace delete a complete day and write back a fragment.

    Callers pad the request (see DerqClient.fetch_window) and trim here, so only
    whole days ever reach the feature service.
    """
    if df.empty or date_field not in df.columns:
        return df

    first, last = parse_day(start), parse_day(end)
    days = pd.to_datetime(df[date_field], errors="coerce").dt.date
    keep = days.between(first, last)

    dropped = int((~keep).sum())
    if dropped:
        logger.info(
            "  trimmed %s row(s) outside %s..%s (partial API boundary days)",
            dropped, first, last,
        )
    return df[keep].reset_index(drop=True)


def sql_quote(value: str) -> str:
    """Single-quote a SQL string literal, escaping embedded quotes."""
    return "'" + str(value).replace("'", "''") + "'"


def epoch_day_bounds(day: str | date) -> tuple[int, int]:
    """Half-open [start, end) epoch-millisecond bounds of one UTC calendar day."""
    start = pd.Timestamp(parse_day(day), tz="UTC")
    end = start + pd.Timedelta(days=1)
    return int(start.timestamp() * 1000), int(end.timestamp() * 1000)


def candidate_day_clause(
    date_field: str,
    day: str | date,
    scope_field: str | None = None,
    scope_values: list | None = None,
    pad_days: int = 2,
) -> str:
    """
    WHERE clause that over-selects candidates around one calendar day.

    Timestamp literals CANNOT be used for precise day selection on this
    service: the backing database compares stored UTC epochs as PST (UTC-8,
    verified live -- rows written at 2025-09-08T00:00:00Z match the literal
    window [2025-09-07 16:00, 17:00)). So this clause is deliberately wide
    (+/- pad_days, correct under any timezone interpretation within +/-24h);
    the caller then reads each candidate's raw epoch -- which the REST API
    returns in UTC ms regardless of the database timezone -- and filters to
    epoch_day_bounds() exactly.

    `scope_field`/`scope_values` narrow the candidates to the locations that
    actually returned data, so a camera with an API outage keeps its rows.
    """
    start = parse_day(day) - timedelta(days=pad_days)
    end = parse_day(day) + timedelta(days=1 + pad_days)
    clause = (
        f"{date_field} >= timestamp '{start.isoformat()} 00:00:00' "
        f"AND {date_field} < timestamp '{end.isoformat()} 00:00:00'"
    )
    if scope_field and scope_values is not None:
        values = ", ".join(sql_quote(v) for v in sorted(set(scope_values)))
        clause += f" AND {scope_field} IN ({values})"
    return clause


# ---------------------------------------------------------------------------
# Schema mapping
# ---------------------------------------------------------------------------


def target_fields(dataset_cfg: dict) -> list[str]:
    """The ArcGIS field names this dataset writes, in stable order."""
    ordered = list(dict.fromkeys(dataset_cfg.get("field_map", {}).values()))
    for name in PASSTHROUGH_FIELDS:
        if name not in ordered:
            ordered.append(name)
    for name in dataset_cfg.get("enrich_from_locations", {}):
        if name not in ordered:
            ordered.append(name)
    return ordered


def validate_field_map(
    name: str, dataset_cfg: dict, layer_fields: set[str]
) -> list[str]:
    """
    Check every field this dataset intends to write against the live layer
    schema. Returns a list of human-readable problems; empty means valid.

    This is the guard that the previous ETL lacked: it pushed `count` and
    `date` at a layer whose fields are `counts` and `Date`, so every value
    would have landed null.
    """
    problems = []
    for target in target_fields(dataset_cfg):
        if target not in layer_fields:
            problems.append(
                f"{name}: field_map target '{target}' does not exist on layer "
                f"{dataset_cfg['layer_id']}. Available: {sorted(layer_fields)}"
            )

    date_field = dataset_cfg.get("date_field")
    if date_field and date_field not in layer_fields:
        problems.append(
            f"{name}: date_field '{date_field}' does not exist on layer "
            f"{dataset_cfg['layer_id']}."
        )

    for enriched in dataset_cfg.get("enrich_from_locations", {}):
        if enriched in dataset_cfg.get("field_map", {}).values():
            problems.append(
                f"{name}: '{enriched}' is both a field_map target and an "
                "enrich_from_locations target -- the enrichment would overwrite it."
            )
    return problems


def map_to_layer_schema(
    df: pd.DataFrame,
    name: str,
    dataset_cfg: dict,
    locations: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """
    Rename DERQ columns to the ArcGIS layer's field names and drop everything
    that has no target field.

    Columns arriving from the API that are neither mapped, passed through, nor
    listed in `drop_fields` are dropped with a warning -- that combination
    means the API grew a field the config doesn't know about.

    `locations` supplies the values for any `enrich_from_locations` fields --
    layer attributes that are not in the DERQ payload at all, such as
    Camera_Status on Safety Insights.
    """
    if df.empty:
        return pd.DataFrame(columns=target_fields(dataset_cfg))

    field_map = dataset_cfg.get("field_map", {})
    declared_drops = set(dataset_cfg.get("drop_fields", []))

    missing = [src for src in field_map if src not in df.columns]
    if missing:
        logger.warning(
            "%s: expected DERQ field(s) %s absent from response -- "
            "affected columns will be null.",
            name,
            missing,
        )

    unexpected = (
        set(df.columns) - set(field_map) - set(PASSTHROUGH_FIELDS) - declared_drops
    )
    if unexpected:
        logger.warning(
            "%s: dropping unrecognised DERQ field(s) %s. If these matter, add "
            "them to field_map (requires a matching layer field) or to "
            "drop_fields to silence this.",
            name,
            sorted(unexpected),
        )

    keep = {src: dst for src, dst in field_map.items() if src in df.columns}
    out = df[list(keep)].rename(columns=keep)

    for passthrough in PASSTHROUGH_FIELDS:
        if passthrough in df.columns:
            out[passthrough] = df[passthrough]

    out = enrich_from_locations(out, name, dataset_cfg, locations)

    # Reindex to the full target set so a missing DERQ field becomes an
    # explicit null column rather than a silently absent one.
    return out.reindex(columns=target_fields(dataset_cfg))


def enrich_from_locations(
    df: pd.DataFrame, name: str, dataset_cfg: dict, locations: pd.DataFrame | None
) -> pd.DataFrame:
    """
    Fill layer fields that come from the locations layer rather than DERQ.

    Camera_Status on Safety Insights is a denormalized copy of the camera's
    Status, populated on every existing row. Leaving it null on new rows would
    break any dashboard filter that uses it, so it is joined on LocationId.
    """
    enrichment = dataset_cfg.get("enrich_from_locations") or {}
    if not enrichment:
        return df

    if locations is None or locations.empty or "LocationId" not in df.columns:
        logger.warning(
            "%s: cannot enrich %s -- no locations available. Values will be null.",
            name, sorted(enrichment),
        )
        for target in enrichment:
            df[target] = pd.NA
        return df

    lookup = locations.drop_duplicates("LocationId").set_index("LocationId")
    for target, source in enrichment.items():
        if source not in lookup.columns:
            logger.warning(
                "%s: locations layer has no '%s' column; %s will be null.",
                name, source, target,
            )
            df[target] = pd.NA
            continue
        df[target] = df["LocationId"].map(lookup[source])
        unmatched = int(df[target].isna().sum())
        if unmatched:
            logger.warning(
                "%s: %s row(s) had no locations match for %s.", name, unmatched, target
            )
    return df


def to_arcgis_features(df: pd.DataFrame, date_fields: list[str]) -> list[dict]:
    """
    Convert a mapped DataFrame into addFeatures payload dicts.

    Date columns become epoch milliseconds; NaN/NaT become None. Vectorised --
    the previous row-by-row implementation was untenable at 450k rows.
    """
    if df.empty:
        return []

    out = df.copy()
    for column in date_fields:
        if column in out.columns:
            out[column] = to_epoch_ms(out[column])

    # astype(object) turns numpy scalars into plain Python values so the result
    # is JSON-serialisable; the where() replaces every flavour of null with None.
    out = out.astype(object).where(pd.notna(out), None)
    return [{"attributes": record} for record in out.to_dict("records")]


# ---------------------------------------------------------------------------
# Derived datasets
# ---------------------------------------------------------------------------


def compute_daily_counts(df: pd.DataFrame, dataset_cfg: dict) -> pd.DataFrame:
    """
    Roll 15-minute vehicle counts up to daily totals.

    Expects an already-mapped vehicle_counts frame (columns `Date`, `counts`,
    `LocationName`). Grouping keys come from config: layer 5 has no LocationId
    field, so it groups by LocationName only.
    """
    group_by = dataset_cfg["group_by"]
    sum_field = dataset_cfg["sum_field"]
    columns = list(group_by) + [sum_field]

    if df.empty:
        return pd.DataFrame(columns=columns)

    working = df.copy()
    if "Date" in group_by:
        # Strip the time component so 15-minute rows collapse onto one day.
        working["Date"] = pd.to_datetime(working["Date"], errors="coerce").dt.normalize()

    daily = working.groupby(group_by, as_index=False, dropna=False)[sum_field].sum()
    return daily[columns]


def aggregate_speed(frames: list[pd.DataFrame], dataset_cfg: dict) -> pd.DataFrame:
    """
    Sum speed-distribution counts across every 30-day API chunk.

    The Speed layer has no date field, so it holds a single whole-of-record
    distribution per location/interval/approach rather than a time series.
    """
    key = dataset_cfg["aggregate_key"]
    sum_field = dataset_cfg["aggregate_sum_field"]
    columns = list(key) + [sum_field]

    populated = [f for f in frames if f is not None and not f.empty]
    if not populated:
        return pd.DataFrame(columns=columns)

    combined = pd.concat(populated, ignore_index=True)
    missing = [c for c in columns if c not in combined.columns]
    if missing:
        raise ValueError(f"speed aggregation missing column(s): {missing}")

    return combined.groupby(key, as_index=False, dropna=False)[sum_field].sum()[columns]
