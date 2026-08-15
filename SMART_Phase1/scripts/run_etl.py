"""
DERQ -> ArcGIS ETL for the SMART Phase 1 traffic camera data.

Pulls vehicle counts, VRU counts, safety insights and speed distributions from
the DERQ INSIGHT API and publishes them to the Transportation_SMART feature
service, which backs the ArcGIS dashboard and the Tahoe Open Data
"Transportation Patterns" page.

Loads are idempotent: each calendar day is deleted and re-added rather than
appended, scoped to the locations that actually returned data. Re-running the
same window is a no-op, and a partial final day heals on the next run.

Usage
-----
    python run_etl.py --preflight                 validate config, write nothing
    python run_etl.py --dry-run                   simulate the scheduled run
    python run_etl.py --live                      the scheduled monthly run
    python run_etl.py --start 2025-09-07 --end 2025-09-30 --live --resume
    python run_etl.py --datasets vehicle_counts,daily_counts --live

Exits non-zero on any failure so Task Scheduler reports it.
"""

from __future__ import annotations

import argparse
import io
import json
import logging
import smtplib
import sys
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Make sibling modules importable regardless of the working directory.
sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd

import transforms as T
from arcgis_client import ArcGISClient
from derq_client import DerqClient, build_date_chunks
from smart_config import (
    LOG_DIR,
    RAW_DIR,
    STATE_DIR,
    ConfigError,
    ensure_working_dirs,
    load_settings,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Logging and notification
# ---------------------------------------------------------------------------


def setup_logging(verbose: bool = False) -> io.StringIO:
    """
    Log to stdout, a rotating monthly file, and an in-memory buffer that is
    emailed at the end of the run.
    """
    buffer = io.StringIO()
    formatter = logging.Formatter(
        fmt="%(asctime)s  %(levelname)-8s  %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    root = logging.getLogger()
    root.setLevel(logging.DEBUG if verbose else logging.INFO)
    root.handlers.clear()

    for handler in (logging.StreamHandler(sys.stdout), logging.StreamHandler(buffer)):
        handler.setFormatter(formatter)
        root.addHandler(handler)

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    file_handler = RotatingFileHandler(
        LOG_DIR / f"smart_etl_{datetime.now():%Y-%m}.log",
        maxBytes=5_000_000,
        backupCount=6,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    return buffer


def send_email(settings, subject: str, body: str) -> None:
    """Send the run log via the smtp2go relay. Never raises."""
    if not settings.email.get("enabled", False):
        logger.info("Email disabled in config; skipping summary.")
        return
    if not all((settings.email_from, settings.email_to, settings.smtp_host)):
        logger.warning("Email settings incomplete in .env; skipping summary.")
        return

    message = MIMEMultipart()
    message["From"] = settings.email_from
    message["To"] = settings.email_to
    message["Subject"] = subject
    message.attach(
        MIMEText(
            f"<pre style='font-family:monospace;font-size:13px;'>{body}</pre>", "html"
        )
    )

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as server:
            server.ehlo()
            server.starttls()
            server.sendmail(
                settings.email_from, [settings.email_to], message.as_string()
            )
        logger.info("Summary emailed to %s", settings.email_to)
    except Exception as exc:  # noqa: BLE001 - a failed email must not fail the run
        logger.error("Could not send summary email: %s", exc)


# ---------------------------------------------------------------------------
# Preflight
# ---------------------------------------------------------------------------


def preflight(settings, client: ArcGISClient) -> list[str]:
    """
    Validate every configured field map against the live layer schema.

    This is the check the previous ETL lacked. It pushed DERQ's `count` and
    `date` at a layer whose fields are `counts` and `Date`, so every value
    would have written null. Nothing is written unless this returns clean.
    """
    logger.info("Preflight: validating field maps against live layer schemas")
    problems: list[str] = []

    for name, cfg in settings.datasets.items():
        layer_id = cfg["layer_id"]
        try:
            fields = client.get_layer_fields(layer_id)
        except Exception as exc:  # noqa: BLE001
            problems.append(f"{name}: could not read layer {layer_id} schema: {exc}")
            continue

        if cfg.get("derived_from"):
            targets = list(cfg["group_by"]) + [cfg["sum_field"]]
            missing = [t for t in targets if t not in fields]
            problems += [
                f"{name}: '{t}' does not exist on layer {layer_id}" for t in missing
            ]
            status = "OK" if not missing else "FAIL"
            logger.info(
                "  %-16s layer %-2s derived  %-52s %s",
                name, layer_id, ", ".join(targets), status,
            )
            continue

        found = T.validate_field_map(name, cfg, fields)
        problems += found
        logger.info(
            "  %-16s layer %-2s %-8s %-52s %s",
            name, layer_id, cfg["load_mode"],
            ", ".join(T.target_fields(cfg)),
            "OK" if not found else "FAIL",
        )
        dropped = cfg.get("drop_fields") or []
        if dropped:
            logger.info("  %-16s   dropping (no target field): %s", "", ", ".join(dropped))

    for problem in problems:
        logger.error("  ! %s", problem)
    return problems


# ---------------------------------------------------------------------------
# Window resolution
# ---------------------------------------------------------------------------


def resolve_window(settings, client, name, cfg, args):
    """
    Decide the [start, end] date window for one dataset.

    Explicit --start/--end wins. Otherwise work back `lookback_days` from the
    layer's own max date, so a partial final day is re-fetched and replaced.
    An empty layer bootstraps from run.backfill_start.
    """
    yesterday = datetime.now(tz=timezone.utc).date() - timedelta(days=1)

    if args.start:
        start = T.parse_day(args.start)
        end = T.parse_day(args.end) if args.end else yesterday
        return start, min(end, yesterday)

    lookback = args.lookback_days
    if lookback is None:
        lookback = settings.run.get("lookback_days", 3)

    max_date = client.get_max_date(cfg["layer_id"], cfg["date_field"])
    if max_date is None:
        start = T.parse_day(settings.run["backfill_start"])
        logger.info("%s: layer is empty; bootstrapping from %s", name, start)
    else:
        start = max_date.date() - timedelta(days=lookback)
        logger.info(
            "%s: layer max %s, lookback %s day(s) -> from %s",
            name, max_date.date(), lookback, start,
        )
    return start, yesterday


# ---------------------------------------------------------------------------
# Load strategies
# ---------------------------------------------------------------------------


def load_day_replace(client, cfg, mapped: pd.DataFrame, name: str, dry_run: bool):
    """
    Replace each calendar day present in `mapped`.

    Days with no fetched records are left alone: an empty API response is
    indistinguishable from an outage, and deleting on that basis would destroy
    good data. The delete is also scoped to the locations that returned data,
    for the same reason.
    """
    date_field = cfg["date_field"]
    if mapped.empty:
        logger.info("%s: no records to load.", name)
        return {"days": 0, "deleted": 0, "added": 0}

    scope_field = "LocationId" if "LocationId" in mapped.columns else "LocationName"
    working = mapped.copy()
    working["_day"] = pd.to_datetime(working[date_field], errors="coerce").dt.date

    undated = int(working["_day"].isna().sum())
    if undated:
        logger.warning(
            "%s: %s record(s) have an unparseable %s and will be skipped.",
            name, undated, date_field,
        )
        working = working[working["_day"].notna()]

    totals = {"days": 0, "deleted": 0, "added": 0}
    for day, chunk in working.groupby("_day", sort=True):
        payload = chunk.drop(columns="_day")
        features = T.to_arcgis_features(payload, cfg.get("target_date_fields", []))
        totals["days"] += 1

        if dry_run:
            logger.info("  [DRY RUN] %s %s: %s row(s)", name, day, len(features))
            continue

        deleted, added = client.replace_day(
            cfg["layer_id"],
            date_field,
            day,
            features,
            f"{name} {day}",
            scope_field,
            payload[scope_field].dropna().tolist(),
        )
        totals["deleted"] += deleted
        totals["added"] += added

    if dry_run:
        logger.info(
            "  [DRY RUN] %s: %s day(s), %s row(s) total -- nothing written.",
            name, totals["days"], len(working),
        )
    return totals


def load_full_replace(client, cfg, mapped: pd.DataFrame, name: str, dry_run: bool):
    """
    Truncate and reload a whole layer. Used for Speed, which has no date field
    and holds a single whole-of-record distribution rather than a time series.
    """
    if mapped.empty:
        logger.warning("%s: fetched 0 rows; refusing to truncate the layer.", name)
        return {"days": 0, "deleted": 0, "added": 0}

    features = T.to_arcgis_features(mapped, cfg.get("target_date_fields", []))

    if dry_run:
        logger.info(
            "  [DRY RUN] %s: would truncate layer %s and load %s row(s).",
            name, cfg["layer_id"], len(features),
        )
        return {"days": 0, "deleted": 0, "added": 0}

    deleted = client.truncate(cfg["layer_id"])
    added = client.add_features(cfg["layer_id"], features)
    logger.info("  %s: -%s +%s", name, deleted, added)
    return {"days": 0, "deleted": deleted, "added": added}


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def run(settings, args) -> dict:
    client = ArcGISClient(settings)

    problems = preflight(settings, client)
    if problems:
        raise ConfigError(
            f"Preflight failed with {len(problems)} problem(s). Nothing was written. "
            "Fix config.yaml (or the layer schema) and re-run."
        )
    if args.preflight:
        logger.info("Preflight only -- exiting without fetching or writing.")
        return {}

    dry_run = settings.dry_run
    logger.info("Mode: %s", "DRY RUN (nothing written)" if dry_run else "LIVE")

    selected = (
        [d.strip() for d in args.datasets.split(",")]
        if args.datasets
        else list(settings.datasets)
    )
    unknown = [d for d in selected if d not in settings.datasets]
    if unknown:
        raise ConfigError(f"Unknown dataset(s): {unknown}")
    disabled = [
        d for d in selected
        if not settings.datasets[d].get("enabled", True)
    ]
    for name in disabled:
        logger.warning(
            "%s is disabled in config.yaml (enabled: false) and will be skipped.",
            name,
        )

    locations = client.get_locations()
    logger.info("Locations in scope: %s", len(locations))

    derq = DerqClient(settings, cache_dir=RAW_DIR if args.resume else None)
    if args.resume:
        logger.info("Resume mode: caching raw responses under %s", RAW_DIR)

    summary: dict[str, dict] = {}
    vehicle_mapped = pd.DataFrame()

    # --- datasets fetched from DERQ -------------------------------------
    for name in settings.fetched_datasets:
        if name not in selected:
            continue
        cfg = settings.dataset(name)
        logger.info("-" * 60)
        logger.info("Dataset: %s (layer %s, %s)", name, cfg["layer_id"], cfg["load_mode"])

        if cfg["load_mode"] == "full_replace":
            # Speed is a whole-of-record aggregate: always rebuild from the
            # complete history, never just the recent window. That is the
            # single biggest consumer of the Derq daily quota (1,000
            # requests/day, all endpoints), so historical chunks are cached
            # permanently -- a fully-past 30-day window never changes, and its
            # cache key never changes either. Only the final chunk (whose end
            # date moves with 'yesterday') is refetched each run.
            start = T.parse_day(settings.run["backfill_start"])
            if args.start:
                start = T.parse_day(args.start)
            end = datetime.now(tz=timezone.utc).date() - timedelta(days=1)
            chunks = build_date_chunks(
                start, end, settings.derq["max_days_per_request"]
            )
            derq.cache_dir = RAW_DIR
            try:
                frames = [
                    derq.fetch_window(name, cfg, locations, chunk_start, chunk_end)
                    for chunk_start, chunk_end in chunks
                ]
            finally:
                derq.cache_dir = RAW_DIR if args.resume else None
            mapped_frames = [
                T.map_to_layer_schema(f, name, cfg, locations)
                for f in frames
                if not f.empty
            ]
            mapped = T.aggregate_speed(mapped_frames, cfg)
            logger.info("%s: aggregated to %s row(s)", name, len(mapped))
            summary[name] = load_full_replace(client, cfg, mapped, name, dry_run)
            continue

        start, end = resolve_window(settings, client, name, cfg, args)
        if start > end:
            logger.info("%s: already up to date.", name)
            summary[name] = {"days": 0, "deleted": 0, "added": 0}
            continue

        raw = derq.fetch_window(name, cfg, locations, start.isoformat(), end.isoformat())
        mapped = T.map_to_layer_schema(raw, name, cfg, locations)
        if name == "vehicle_counts":
            vehicle_mapped = mapped
        summary[name] = load_day_replace(client, cfg, mapped, name, dry_run)

    # --- derived datasets ------------------------------------------------
    for name, cfg in settings.datasets.items():
        source = cfg.get("derived_from")
        if not source or name not in selected:
            continue
        logger.info("-" * 60)
        logger.info("Dataset: %s (layer %s, derived from %s)", name, cfg["layer_id"], source)

        if source != "vehicle_counts":
            raise ConfigError(f"{name}: unsupported derived_from '{source}'")
        if source not in selected:
            logger.warning(
                "%s: source '%s' was not run, so there is nothing to derive.",
                name, source,
            )
            summary[name] = {"days": 0, "deleted": 0, "added": 0}
            continue

        daily = T.compute_daily_counts(vehicle_mapped, cfg)
        logger.info("%s: %s daily row(s) from %s source row(s)",
                    name, len(daily), len(vehicle_mapped))
        summary[name] = load_day_replace(client, cfg, daily, name, dry_run)

    logger.info("-" * 60)
    logger.info("DERQ requests: %s (cache hits: %s)", derq.request_count, derq.cache_hits)
    if derq.failed_chunks:
        # Day-replace never deletes days with no fetched data, so a failed
        # chunk means missing-but-recoverable days, not corruption. Flag the
        # run so the email/exit code prompts a re-run.
        logger.error(
            "%s DERQ chunk(s) failed after retries; affected days were not "
            "loaded and will be caught up on a re-run:",
            len(derq.failed_chunks),
        )
        for dataset, location, cs, ce in derq.failed_chunks:
            logger.error("    %s / %s / %s..%s", dataset, location, cs, ce)
        raise RuntimeError(f"{len(derq.failed_chunks)} DERQ chunk(s) failed")
    return summary


def write_state(summary: dict, args, dry_run: bool, ok: bool) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    state = {
        "run_utc": datetime.now(tz=timezone.utc).isoformat(),
        "dry_run": dry_run,
        "ok": ok,
        "start": args.start,
        "end": args.end,
        "datasets": summary,
    }
    (STATE_DIR / "last_run.json").write_text(
        json.dumps(state, indent=2, default=str), encoding="utf-8"
    )


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Fetch DERQ camera data and publish it to the "
                    "Transportation_SMART feature service.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--start", help="First day to load, YYYY-MM-DD (backfill).")
    parser.add_argument("--end", help="Last day to load, YYYY-MM-DD. Defaults to yesterday.")
    parser.add_argument("--datasets", help="Comma-separated subset. Default: all.")
    parser.add_argument("--lookback-days", type=int,
                        help="Override run.lookback_days from config.yaml.")
    parser.add_argument("--preflight", action="store_true",
                        help="Validate config against live schemas, then exit.")
    parser.add_argument("--resume", action="store_true",
                        help="Cache raw DERQ responses so an interrupted backfill resumes.")
    parser.add_argument("--verbose", action="store_true", help="Debug-level logging.")

    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", dest="dry_run", action="store_true", default=None,
                      help="Simulate; write nothing. Overrides DRY_RUN in .env.")
    mode.add_argument("--live", dest="dry_run", action="store_false",
                      help="Write to the feature service. Overrides DRY_RUN in .env.")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    buffer = setup_logging(args.verbose)
    ensure_working_dirs()

    summary: dict = {}
    settings = None
    ok = True
    dry_run = True

    try:
        settings = load_settings()
        if args.dry_run is not None:
            settings.dry_run = args.dry_run
        dry_run = settings.dry_run

        logger.info("=" * 60)
        logger.info("SMART Phase 1 ETL -- DERQ to ArcGIS")
        logger.info("=" * 60)

        summary = run(settings, args)

        if summary:
            logger.info("=" * 60)
            logger.info("Summary")
            logger.info("=" * 60)
            for name, counts in summary.items():
                logger.info(
                    "  %-16s %3s day(s)  -%-7s +%s",
                    name, counts["days"], counts["deleted"], counts["added"],
                )
    except ConfigError as exc:
        logger.error("Configuration error: %s", exc)
        ok = False
    except Exception as exc:  # noqa: BLE001
        logger.error("Unhandled exception: %s", exc, exc_info=True)
        ok = False

    try:
        write_state(summary, args, dry_run, ok)
    except Exception as exc:  # noqa: BLE001
        logger.error("Could not write state file: %s", exc)

    # A clean --preflight is a config check, not a run worth emailing about.
    # A failed one is, since that is how a scheduled run reports broken config.
    if settings is not None and not (args.preflight and ok):
        tag = " [DRY RUN]" if dry_run else ""
        status = " OK" if ok else " ERRORS"
        prefix = settings.email.get("subject_prefix", "DERQ ETL")
        send_email(
            settings,
            f"{prefix}{tag}{status} - {datetime.now():%Y-%m-%d %H:%M}",
            buffer.getvalue(),
        )

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
