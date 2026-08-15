"""
Client for the DERQ INSIGHT API.

The API caps a single request at 30 days, so every fetch is chunked. A full
catch-up run is on the order of 500 sequential requests, which is why this
module has a politeness delay, retry/backoff, and an optional on-disk cache of
raw responses so an interrupted backfill can resume without re-hitting DERQ.
"""

from __future__ import annotations

import gzip
import json
import logging
import time
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import requests

from transforms import parse_day, trim_to_window

logger = logging.getLogger(__name__)

# HTTP statuses worth retrying: rate limiting and transient server errors.
RETRY_STATUS_CODES = frozenset({429, 500, 502, 503, 504})

# The DERQ API filters startDate/endDate at UTC midnight, but the data is
# stamped in local Pacific time. Verified empirically: a request for [D1, D2]
# returns a partial D1-1 (evening only, 28 of 96 fifteen-minute intervals) and
# a partial D2-1 (midnight to ~5 PM, 68 of 96); only [D1, D2-2] arrive
# complete. So every request is padded by this many days past the wanted
# window, and the response is trimmed back to the days that are complete.
BOUNDARY_PAD_DAYS = 2


def build_date_chunks(
    start: str | date, end: str | date, max_days: int = 30
) -> list[tuple[str, str]]:
    """
    Split an inclusive [start, end] window into (start, end) string pairs no
    longer than max_days, as required by the DERQ API.

    Returns an empty list when start is after end, which is how "already up to
    date" is represented.
    """
    first, last = parse_day(start), parse_day(end)
    if first > last:
        return []

    chunks = []
    cursor = first
    while cursor <= last:
        chunk_end = min(cursor + timedelta(days=max_days - 1), last)
        chunks.append((cursor.isoformat(), chunk_end.isoformat()))
        cursor = chunk_end + timedelta(days=1)
    return chunks


class DerqClient:
    """Thin, retrying wrapper over the DERQ INSIGHT REST endpoints."""

    def __init__(self, settings, cache_dir: Path | None = None):
        self.settings = settings
        self.base_url = settings.derq_url
        self.cfg = settings.derq
        self.cache_dir = cache_dir  # None disables caching
        self.session = requests.Session()
        self.session.headers.update(settings.derq_headers())
        self.request_count = 0
        self.cache_hits = 0
        # (dataset, location_name, start, end) of chunks that exhausted retries.
        self.failed_chunks: list[tuple[str, str, str, str]] = []
        # Hard stop below Derq's daily quota (1,000/day/key, all endpoints).
        # When exhausted, remaining chunks fast-fail into failed_chunks instead
        # of burning retries into 429s; a --resume run finishes them tomorrow.
        self.max_requests = self.cfg.get("max_requests_per_run")
        self.budget_exhausted = False
        # Circuit breaker: N consecutive give-ups of the same kind mean the
        # problem is systemic (exhausted daily quota, or Derq's backend down),
        # so the remaining chunks fast-fail instead of burning requests and
        # retry time one chunk at a time.
        self._consecutive_failures = 0
        self._breaker_threshold = 3

    # -- internals ---------------------------------------------------------

    def _trip_breaker_maybe(self, reason: str) -> None:
        """Count a chunk-level give-up; trip the fast-fail breaker at the threshold."""
        self._consecutive_failures += 1
        if (
            self._consecutive_failures >= self._breaker_threshold
            and not self.budget_exhausted
        ):
            self.budget_exhausted = True
            logger.error(
                "%s consecutive failed chunks (last: %s) -- systemic failure, "
                "fast-failing the remaining chunks. Re-run with --resume once "
                "the cause clears (quota reset / Derq backend recovery).",
                self._consecutive_failures, reason,
            )

    def _cache_path(self, dataset: str, location_id: str, start: str, end: str) -> Path:
        return self.cache_dir / dataset / location_id / f"{start}_{end}.json.gz"

    def _read_cache(self, path: Path):
        try:
            with gzip.open(path, "rt", encoding="utf-8") as handle:
                return json.load(handle)
        except (OSError, ValueError) as exc:
            logger.warning("Ignoring unreadable cache file %s: %s", path, exc)
            return None

    def _write_cache(self, path: Path, records: list) -> None:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with gzip.open(path, "wt", encoding="utf-8") as handle:
                json.dump(records, handle)
        except OSError as exc:
            logger.warning("Could not write cache file %s: %s", path, exc)

    def _get(self, url: str, label: str) -> list | None:
        """
        GET a DERQ endpoint and return its `body` list.

        Retries rate limits, 5xx, and timeouts with exponential backoff.
        Returns None (NOT an empty list) when all retries fail, so one bad
        chunk cannot abort a multi-month backfill but a failure is never
        mistaken for -- or cached as -- a genuinely empty response.
        """
        max_retries = self.cfg.get("max_retries", 4)
        backoff_base = self.cfg.get("retry_backoff_base", 10)
        timeout = self.cfg.get("request_timeout", 60)

        for attempt in range(1, max_retries + 1):
            try:
                self.request_count += 1
                response = self.session.get(url, timeout=timeout)

                if response.status_code in RETRY_STATUS_CODES:
                    if attempt < max_retries:
                        wait = backoff_base * (2 ** (attempt - 1))
                        logger.warning(
                            "HTTP %s for %s (attempt %s/%s). Retrying in %ss...",
                            response.status_code, label, attempt, max_retries, wait,
                        )
                        time.sleep(wait)
                        continue
                    logger.error(
                        "HTTP %s for %s after %s attempts. Skipping chunk.",
                        response.status_code, label, max_retries,
                    )
                    self._trip_breaker_maybe(f"HTTP {response.status_code}")
                    return None

                response.raise_for_status()
                payload = response.json()

                # DERQ reports application-level failures inside a 200 body --
                # including raw backend database errors like "current
                # transaction is aborted" (observed live on /speed-distribution).
                if str(payload.get("statusCode")) != "200":
                    detail = payload.get("errorMessage") or payload.get("statusCode")
                    logger.warning(
                        "API error for %s: %s. Skipping chunk.", label, detail
                    )
                    self._trip_breaker_maybe(f"API error: {str(detail)[:80]}")
                    return None

                self._consecutive_failures = 0
                return payload.get("body", []) or []

            except requests.HTTPError as exc:
                logger.error("HTTP error for %s: %s. Skipping chunk.", label, exc)
                return None
            except requests.Timeout:
                if attempt < max_retries:
                    wait = backoff_base * (2 ** (attempt - 1))
                    logger.warning(
                        "Timeout for %s (attempt %s/%s). Retrying in %ss...",
                        label, attempt, max_retries, wait,
                    )
                    time.sleep(wait)
                    continue
                logger.error("Timeout for %s after %s attempts. Skipping chunk.",
                             label, max_retries)
                return None
            except Exception as exc:  # noqa: BLE001 - never kill a long backfill
                logger.error("Unexpected error for %s: %s. Skipping chunk.", label, exc)
                return None

        return None

    def _build_url(self, dataset: str, endpoint: str, location_id: str,
                   start: str, end: str) -> str:
        url = (
            f"{self.base_url}{endpoint}?locationId={location_id}"
            f"&startDate={start}&endDate={end}"
        )
        if dataset == "safety_insights":
            url += f"&eventTypes={self.cfg['event_types']}"
        elif dataset == "speed":
            url += (
                f"&speedBuckets={self.cfg['speed_buckets']}&speedUnit=mph"
            )
        return url

    # -- public API --------------------------------------------------------

    def get_locations(self) -> pd.DataFrame:
        """
        The camera list as DERQ knows it (GET /locations).

        The pipeline deliberately does NOT fetch from this -- the curated
        ArcGIS layer 0 is authoritative -- but the QA notebook compares the two
        lists, because a camera present in DERQ and absent from layer 0 is
        data that silently never gets fetched.
        """
        records = self._get(f"{self.base_url}/locations", "locations")
        if not records:
            return pd.DataFrame(columns=["LocationId", "LocationName"])
        return pd.DataFrame(records)

    def fetch_chunk(
        self,
        dataset: str,
        endpoint: str,
        location_id: str,
        location_name: str,
        start: str,
        end: str,
    ) -> pd.DataFrame:
        """
        Fetch one dataset, one location, one <=30-day window.

        LocationId and LocationName are stamped onto the frame because the API
        returns neither -- both are real fields on every target layer.
        """
        label = f"{dataset}/{location_name} {start}..{end}"
        records = None

        if self.cache_dir is not None:
            path = self._cache_path(dataset, location_id, start, end)
            if path.exists():
                records = self._read_cache(path)
                if records is not None:
                    self.cache_hits += 1
                    logger.debug("cache hit %s", label)

        if records is None:
            over_budget = (
                self.max_requests and self.request_count >= self.max_requests
            )
            if over_budget and not self.budget_exhausted:
                self.budget_exhausted = True
                logger.error(
                    "Request budget (%s) exhausted -- remaining chunks are "
                    "recorded as failed; re-run with --resume after the "
                    "daily quota resets.",
                    self.max_requests,
                )
            if self.budget_exhausted:
                self.failed_chunks.append((dataset, location_name, start, end))
                return pd.DataFrame()
            url = self._build_url(dataset, endpoint, location_id, start, end)
            records = self._get(url, label)
            if records is None:
                # Exhausted retries. Never cache a failure -- a cached empty
                # would make a --resume re-run trust the hole -- and record it
                # so the caller can report and repair the gap.
                self.failed_chunks.append((dataset, location_name, start, end))
                return pd.DataFrame()
            if self.cache_dir is not None:
                self._write_cache(
                    self._cache_path(dataset, location_id, start, end), records
                )
            delay = self.cfg.get("request_delay_seconds", 0)
            if delay:
                time.sleep(delay)

        if not records:
            return pd.DataFrame()

        df = pd.DataFrame(records)
        df["LocationId"] = location_id
        df["LocationName"] = location_name
        return df

    def fetch_window(
        self,
        dataset: str,
        dataset_cfg: dict,
        locations: pd.DataFrame,
        start: str,
        end: str,
    ) -> pd.DataFrame:
        """
        Fetch one dataset across every location for an arbitrary window,
        chunking to the API's 30-day limit and concatenating the results.

        Datasets with a `source_date_field` get boundary handling: each chunk
        request is padded by BOUNDARY_PAD_DAYS and the response trimmed back to
        the chunk's own complete days. The trim must be per chunk -- adjacent
        padded requests overlap, and trimming only at the end would keep the
        seam days twice (a complete copy from one chunk plus a partial copy
        from the next).

        Datasets without a date field (speed) cannot be trimmed; their request
        is padded so the recent edge is covered, and the sub-day fuzz at the
        boundaries of the aggregate is accepted.
        """
        endpoint = dataset_cfg["endpoint"]
        source_date_field = dataset_cfg.get("source_date_field")
        max_days = self.cfg["max_days_per_request"]

        if source_date_field:
            # Chunks tile the COMPLETE-day windows; each request is then padded,
            # so the stride must leave room for the pad inside the 30-day cap.
            chunks = build_date_chunks(start, end, max_days - BOUNDARY_PAD_DAYS)
        else:
            chunks = build_date_chunks(start, end, max_days)

        if not chunks:
            logger.info("%s: nothing to fetch for %s..%s", dataset, start, end)
            return pd.DataFrame()

        logger.info(
            "%s: %s chunk(s) x %s location(s) = %s request(s)",
            dataset, len(chunks), len(locations), len(chunks) * len(locations),
        )

        frames = []
        for chunk_start, chunk_end in chunks:
            request_end = (
                parse_day(chunk_end) + timedelta(days=BOUNDARY_PAD_DAYS)
            ).isoformat()
            logger.info(
                "  %s -> %s (requesting through %s)",
                chunk_start, chunk_end, request_end,
            )
            for _, row in locations.iterrows():
                frame = self.fetch_chunk(
                    dataset,
                    endpoint,
                    row["LocationId"],
                    row["LocationName"],
                    chunk_start,
                    request_end,
                )
                if frame.empty:
                    # Worth surfacing: a decommissioned camera returns an empty
                    # body rather than an error, and would otherwise vanish.
                    logger.debug("    no records: %s", row["LocationName"])
                    continue
                if source_date_field:
                    frame = trim_to_window(
                        frame, source_date_field, chunk_start, chunk_end
                    )
                if not frame.empty:
                    frames.append(frame)

        if not frames:
            logger.info("  -> 0 records for %s", dataset)
            return pd.DataFrame()

        combined = pd.concat(frames, ignore_index=True)
        logger.info("  -> %s records for %s", len(combined), dataset)
        return combined
