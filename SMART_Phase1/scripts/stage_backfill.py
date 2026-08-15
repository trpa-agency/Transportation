"""
Stage the complete DERQ history as CSVs for a server-side geodatabase load.

Pushing 11+ months through the REST addFeatures endpoint is slow (multi-minute
delete batches on the 450k-row tables), so the backfill path is: this script
fetches everything from DERQ and stages files; the load happens on the server
via ArcGIS Pro / arcpy truncate-and-append into the enterprise geodatabase.

The staged rows go through exactly the same field mapping, boundary-day
trimming, Camera_Status enrichment and daily derivation as the monthly ETL
(scripts/run_etl.py), so a truncate/append leaves the service byte-consistent
with what the ETL would have written -- and the monthly REST job can then take
over incremental updates.

Outputs (under data/staging/<run-name>/):
    full/TTD_SMART_<dataset>.csv        complete history -- for truncate/append
    append_only/TTD_SMART_<dataset>.csv rows after --append-after only
    LOAD_README.md                      row counts, field notes, load guidance

Usage:
    python stage_backfill.py                      # 2025-03-10 -> yesterday
    python stage_backfill.py --start 2025-09-09   # append-window only
    python stage_backfill.py --resume             # reuse cached API responses
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd

import transforms as T
from arcgis_client import ArcGISClient
from derq_client import DerqClient, build_date_chunks
from smart_config import RAW_DIR, ensure_working_dirs, load_settings

logger = logging.getLogger(__name__)

# First day with any data in the published service is 2025-03-12 (UTC);
# start a couple of days earlier so the boundary pad covers the true beginning.
DEFAULT_START = "2025-03-10"

# The published Phase 1 record ends at 2025-09-08 (loaded and verified via the
# ETL); everything after it is the gap the append-only variant covers.
DEFAULT_APPEND_AFTER = "2025-09-08"

# Filenames match the published data-package convention.
EXPORT_NAMES = {
    "safety_insights": "TTD_SMART_SafetyInsights.csv",
    "vehicle_counts": "TTD_SMART_VehicleCounts.csv",
    "vru_counts": "TTD_SMART_VRUCounts.csv",
    "speed": "TTD_SMART_Speed.csv",
    "daily_counts": "TTD_SMART_DailyVehicleCounts.csv",
}


def stage(settings, args) -> dict:
    client = ArcGISClient(settings)
    locations = client.get_locations()
    logger.info("Locations in scope: %s", len(locations))

    derq = DerqClient(settings, cache_dir=RAW_DIR if args.resume else None)

    out_root = Path(args.outdir)
    full_dir = out_root / "full"
    append_dir = out_root / "append_only"
    full_dir.mkdir(parents=True, exist_ok=True)
    append_dir.mkdir(parents=True, exist_ok=True)

    yesterday = datetime.now(tz=timezone.utc).date() - timedelta(days=1)
    start = T.parse_day(args.start)
    end = T.parse_day(args.end) if args.end else yesterday
    append_after = T.parse_day(args.append_after)

    summary: dict[str, dict] = {}
    vehicle_mapped = pd.DataFrame()

    for name in settings.fetched_datasets:
        if args.datasets and name not in args.datasets:
            continue
        cfg = settings.dataset(name)
        logger.info("=" * 60)
        logger.info("Staging %s (%s -> %s)", name, start, end)

        if cfg["load_mode"] == "full_replace":
            chunks = build_date_chunks(start, end, settings.derq["max_days_per_request"])
            frames = [
                derq.fetch_window(name, cfg, locations, cs, ce) for cs, ce in chunks
            ]
            mapped_frames = [
                T.map_to_layer_schema(f, name, cfg, locations)
                for f in frames
                if not f.empty
            ]
            mapped = T.aggregate_speed(mapped_frames, cfg)
        else:
            raw = derq.fetch_window(
                name, cfg, locations, start.isoformat(), end.isoformat()
            )
            mapped = T.map_to_layer_schema(raw, name, cfg, locations)
            if name == "vehicle_counts":
                vehicle_mapped = mapped

        summary[name] = write_outputs(
            name, cfg, mapped, full_dir, append_dir, append_after
        )

    # Derived daily totals, from the same staged vehicle rows.
    daily_cfg = settings.dataset("daily_counts")
    if not args.datasets or "daily_counts" in args.datasets:
        logger.info("=" * 60)
        logger.info("Deriving daily_counts from %s vehicle rows", len(vehicle_mapped))
        daily = T.compute_daily_counts(vehicle_mapped, daily_cfg)
        summary["daily_counts"] = write_outputs(
            "daily_counts", daily_cfg, daily, full_dir, append_dir, append_after
        )

    logger.info("=" * 60)
    logger.info(
        "DERQ requests: %s (cache hits: %s)", derq.request_count, derq.cache_hits
    )
    if derq.failed_chunks:
        logger.error(
            "%s chunk(s) failed after retries -- the staged files have gaps:",
            len(derq.failed_chunks),
        )
        for dataset, location, cs, ce in derq.failed_chunks:
            logger.error("    %s / %s / %s..%s", dataset, location, cs, ce)
        logger.error(
            "Re-run with --resume: successful chunks come from cache, only the "
            "failures are refetched."
        )
        raise RuntimeError(f"{len(derq.failed_chunks)} chunk(s) failed")
    return summary


def write_outputs(name, cfg, mapped, full_dir, append_dir, append_after) -> dict:
    """Write the full and append-only CSVs for one dataset."""
    filename = EXPORT_NAMES[name]
    date_field = cfg.get("date_field")

    frame = mapped.copy()
    date_range = (None, None)
    appendable = pd.DataFrame(columns=frame.columns)

    if date_field and not frame.empty:
        # Dates go out as ISO strings (date-only where the ETL writes UTC
        # midnight; full timestamp for TimeAtSite). The loader must NOT apply
        # a timezone conversion -- see LOAD_README.
        parsed = pd.to_datetime(frame[date_field], errors="coerce")
        date_range = (parsed.min(), parsed.max())
        cutoff = pd.Timestamp(append_after) + pd.Timedelta(days=1)
        appendable = frame[parsed >= cutoff]
        if name == "safety_insights":
            frame[date_field] = parsed.dt.strftime("%Y-%m-%d %H:%M:%S.%f").str[:-3]
            appendable = appendable.assign(
                **{date_field: pd.to_datetime(appendable[date_field])
                   .dt.strftime("%Y-%m-%d %H:%M:%S.%f").str[:-3]}
            )
        else:
            frame[date_field] = parsed.dt.strftime("%Y-%m-%d")
            appendable = appendable.assign(
                **{date_field: pd.to_datetime(appendable[date_field])
                   .dt.strftime("%Y-%m-%d")}
            )

    frame.to_csv(full_dir / filename, index=False, encoding="utf-8-sig")
    appendable.to_csv(append_dir / filename, index=False, encoding="utf-8-sig")

    info = {
        "file": filename,
        "rows_full": len(frame),
        "rows_append": len(appendable),
        "columns": list(frame.columns),
        "min_date": str(date_range[0].date()) if pd.notna(date_range[0]) else None,
        "max_date": str(date_range[1].date()) if pd.notna(date_range[1]) else None,
    }
    logger.info(
        "%s: %s rows full (%s..%s), %s rows append-only",
        name, info["rows_full"], info["min_date"], info["max_date"],
        info["rows_append"],
    )
    return info


def write_readme(out_root: Path, summary: dict, args, settings) -> None:
    lines = [
        "# SMART backfill staging -- load instructions",
        "",
        f"Generated {datetime.now():%Y-%m-%d %H:%M} by scripts/stage_backfill.py "
        f"from the DERQ INSIGHT API ({args.start} through {args.end or 'yesterday'}).",
        "",
        "## Two ways to load",
        "",
        "**Option A -- truncate/append (recommended):** truncate each SDE table",
        "and append the matching CSV from `full/`. This regenerates the entire",
        "history with consistent conventions and heals the partial edge days",
        "that the original 2025 hand-pulled loads carry around their pull-window",
        "boundaries (the DERQ API returns partial first/last days -- verified).",
        "",
        "**Option B -- append only:** append the CSVs from `append_only/`",
        f"(rows after {args.append_after}) onto the existing tables. Smaller",
        "load, but the historical edge-day partials remain.",
        "",
        "Layer 0 (SMART Traffic Camera) is the curated source -- nothing is",
        "staged for it.",
        "",
        "## Load rules",
        "",
        "- **Do not timezone-convert date fields on load.** The monthly ETL and",
        "  the existing rows serve dates as UTC; `Date` columns are date-only",
        "  (midnight), `TimeAtSite` is a full timestamp. If the append tool is",
        "  set to convert from local time, values shift by 7-8 hours and the",
        "  incremental ETL's day-replace logic will mis-match days.",
        "- Field names in the CSVs match the target tables exactly; OBJECTID/",
        "  GlobalID/editor-tracking fields are omitted and populate on insert.",
        "- `Speed` has no date column: always truncate/append (both variants",
        "  ship the same full-history aggregate; append_only holds a copy for",
        "  convenience, do NOT append it on top of existing rows).",
        "- `Daily Vehicle Counts` is derived from the staged vehicle counts --",
        "  load both from the same variant so they stay consistent.",
        "",
        "## After loading",
        "",
        "Run `python scripts/run_etl.py --preflight` then the QA notebook",
        "(notebooks/Data_QAQC.ipynb) -- section 2 must show zero nulls in",
        "ETL-written fields and section 4 must reconcile daily vs 15-minute",
        "totals. Then the monthly scheduled task takes over increments.",
        "",
        "## Staged files",
        "",
        "| dataset | file | rows (full) | rows (append) | date range |",
        "|---|---|---|---|---|",
    ]
    for name, info in summary.items():
        lines.append(
            f"| {name} | {info['file']} | {info['rows_full']} | "
            f"{info['rows_append']} | {info['min_date']} .. {info['max_date']} |"
        )
    lines += [
        "",
        "## Table -> layer mapping",
        "",
        "| CSV | FeatureServer layer | SDE table |",
        "|---|---|---|",
        "| TTD_SMART_SafetyInsights.csv | 1 | Safety Insights |",
        "| TTD_SMART_Speed.csv | 2 | Speed |",
        "| TTD_SMART_VehicleCounts.csv | 3 | Vehicle Counts (TTD_SMART_Vehicle_Counts_All) |",
        "| TTD_SMART_VRUCounts.csv | 4 | VRU Counts |",
        "| TTD_SMART_DailyVehicleCounts.csv | 5 | Daily Vehicle Counts |",
    ]
    (out_root / "LOAD_README.md").write_text("\n".join(lines), encoding="utf-8")
    logger.info("Wrote %s", out_root / "LOAD_README.md")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", default=DEFAULT_START)
    parser.add_argument("--end", help="Last day to stage; default yesterday.")
    parser.add_argument(
        "--append-after", default=DEFAULT_APPEND_AFTER,
        help="append_only/ holds rows AFTER this date (default: %(default)s, "
             "the verified end of the published record).",
    )
    parser.add_argument("--datasets", nargs="*", help="Subset; default all.")
    parser.add_argument(
        "--outdir",
        default=str(Path(__file__).resolve().parents[1] / "data" / "staging"),
    )
    parser.add_argument("--resume", action="store_true",
                        help="Cache raw responses under data/raw for restartability.")
    parser.add_argument("--delay", type=float,
                        help="Seconds between DERQ requests, overriding config. "
                             "Raise this after 429 rate limiting.")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )
    ensure_working_dirs()

    settings = load_settings()
    if args.delay is not None:
        settings.derq["request_delay_seconds"] = args.delay
    try:
        summary = stage(settings, args)
        write_readme(Path(args.outdir), summary, args, settings)
    except Exception as exc:  # noqa: BLE001
        logger.error("Staging failed: %s", exc, exc_info=True)
        return 1

    logger.info("Staging complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
