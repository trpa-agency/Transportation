"""
REST client for the Transportation_SMART feature service on maps.trpa.org.

Deliberately uses plain `requests` rather than arcpy or the arcgis package, so
the ETL runs in any Python environment and can be scheduled on a server without
an ArcGIS Pro licence.

Writes go through `replace_day`: delete everything in one calendar day, then
add that day's records. That makes a re-run a no-op instead of a duplicate, and
lets a partial final day heal itself -- neither of which append-only allowed.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import date, datetime, timezone

import pandas as pd
import requests

from transforms import candidate_day_clause, epoch_day_bounds

logger = logging.getLogger(__name__)

# Transient write failures are real: an addFeatures immediately after a large
# delete on the same table can hit lock contention and return a generic
# "Unable to complete operation". Retry writes a few times before failing.
WRITE_RETRIES = 3
WRITE_RETRY_WAIT = 10  # seconds; doubles per attempt


class ArcGISError(RuntimeError):
    """Raised when the feature service returns an error payload."""


def _raise_on_error(payload: dict, context: str) -> dict:
    """ArcGIS returns failures inside a 200 body, so status codes aren't enough."""
    if isinstance(payload, dict) and "error" in payload:
        error = payload["error"]
        message = error.get("message", error) if isinstance(error, dict) else error
        details = error.get("details") if isinstance(error, dict) else None
        raise ArcGISError(f"{context}: {message}" + (f" {details}" if details else ""))
    return payload


class ArcGISClient:
    def __init__(self, settings):
        self.settings = settings
        self.service_url = settings.service_url
        self.timeout = settings.arcgis.get("request_timeout", 120)
        # Deletes on the large editor-tracked tables can take minutes per
        # batch; hanging up early just turns a slow success into a retry storm.
        self.write_timeout = settings.arcgis.get("write_timeout", 600)
        self.batch_size = settings.arcgis.get("batch_size", 2000)
        self.session = requests.Session()
        self._token: str | None = None

    # -- auth --------------------------------------------------------------

    @property
    def token(self) -> str:
        """Lazily generate a 60-minute Enterprise token; cached for the run."""
        if self._token is None:
            self._token = self._generate_token()
        return self._token

    def _generate_token(self) -> str:
        self.settings.require_arcgis_credentials()
        url = f"{self.settings.arcgis_portal_url.rstrip('/')}/sharing/rest/generateToken"
        payload = {
            "username": self.settings.arcgis_username,
            "password": self.settings.arcgis_password,
            "client": "referer",
            "referer": self.settings.arcgis_portal_url,
            "expiration": 60,
            "f": "json",
        }
        response = self.session.post(url, data=payload, timeout=30)
        response.raise_for_status()
        data = _raise_on_error(response.json(), "token request")
        if "token" not in data:
            raise ArcGISError(f"Unexpected token response: {data}")
        logger.info("ArcGIS token obtained.")
        return data["token"]

    # -- reads (anonymous) -------------------------------------------------

    def layer_url(self, layer_id: int) -> str:
        return f"{self.service_url}/{layer_id}"

    def get_layer_fields(self, layer_id: int) -> set[str]:
        """Field names on a layer, used by preflight to validate the field maps."""
        response = self.session.get(
            self.layer_url(layer_id), params={"f": "json"}, timeout=30
        )
        response.raise_for_status()
        data = _raise_on_error(response.json(), f"layer {layer_id} metadata")
        return {f["name"] for f in data.get("fields", [])}

    def count(self, layer_id: int, where: str = "1=1") -> int:
        response = self.session.get(
            f"{self.layer_url(layer_id)}/query",
            params={"f": "json", "where": where, "returnCountOnly": "true"},
            timeout=self.timeout,
        )
        response.raise_for_status()
        data = _raise_on_error(response.json(), f"count on layer {layer_id}")
        return int(data.get("count", 0))

    def get_max_date(self, layer_id: int, date_field: str) -> datetime | None:
        """
        Most recent value of a date field, as a UTC datetime.

        Returns None for an empty layer or an all-null field, which the caller
        treats as "bootstrap from run.backfill_start" rather than an error.
        """
        statistics = [
            {
                "statisticType": "max",
                "onStatisticField": date_field,
                "outStatisticFieldName": "latest",
            }
        ]
        response = self.session.get(
            f"{self.layer_url(layer_id)}/query",
            params={
                "f": "json",
                "where": "1=1",
                "outStatistics": json.dumps(statistics),
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        data = _raise_on_error(response.json(), f"max({date_field}) on layer {layer_id}")

        features = data.get("features") or []
        if not features:
            return None
        raw = features[0].get("attributes", {}).get("latest")
        if raw is None:
            return None
        return datetime.fromtimestamp(raw / 1000, tz=timezone.utc)

    def query_all(
        self, layer_id: int, out_fields: str = "*", where: str = "1=1",
        return_geometry: bool = False, page_size: int = 2000,
    ) -> pd.DataFrame:
        """
        Page through an entire layer with resultOffset. Used by the data
        package and data dictionary generators.
        """
        records, offset = [], 0
        while True:
            response = self.session.get(
                f"{self.layer_url(layer_id)}/query",
                params={
                    "f": "json",
                    "where": where,
                    "outFields": out_fields,
                    "returnGeometry": str(return_geometry).lower(),
                    "resultOffset": offset,
                    "resultRecordCount": page_size,
                    "orderByFields": "OBJECTID",
                    # Harmless on public layers, and lets the delete path use
                    # this for its candidate query on secured ones.
                    **({"token": self.token} if self._token else {}),
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = _raise_on_error(response.json(), f"query on layer {layer_id}")
            features = data.get("features") or []
            if not features:
                break
            records.extend(f["attributes"] for f in features)
            if len(features) < page_size and not data.get("exceededTransferLimit"):
                break
            offset += len(features)
            # Layer 3 is 450k+ rows at 2000 per page; without this the export
            # looks hung for several minutes.
            if offset % (page_size * 25) == 0:
                logger.info("  layer %s: %s rows fetched...", layer_id, offset)
        return pd.DataFrame(records)

    def get_locations(self) -> pd.DataFrame:
        """
        Camera locations from the ArcGIS layer -- the curated list, not the DERQ
        /locations endpoint -- filtered to the statuses named in config.

        Status is returned as well as the identifiers, because Safety Insights
        carries it as Camera_Status (see enrich_from_locations in config.yaml).
        """
        layer_id = self.settings.locations["source_layer"]
        df = self.query_all(layer_id, out_fields="LocationId,LocationName,Status")

        if df.empty:
            raise ArcGISError(f"No locations found in layer {layer_id}.")
        for required in ("LocationId", "LocationName"):
            if required not in df.columns:
                raise ArcGISError(
                    f"Field '{required}' missing from locations layer. "
                    f"Found: {list(df.columns)}"
                )

        statuses = self.settings.locations.get("include_status")
        if statuses and "Status" in df.columns:
            before = len(df)
            df = df[df["Status"].isin(statuses)]
            if len(df) < before:
                logger.info(
                    "Filtered locations by status %s: %s of %s kept.",
                    statuses, len(df), before,
                )

        columns = ["LocationId", "LocationName"]
        if "Status" in df.columns:
            columns.append("Status")
        return df[columns].reset_index(drop=True)

    # -- writes ------------------------------------------------------------

    def _post_write(
        self, url: str, data: dict, context: str, timeout: int | None = None
    ) -> dict:
        """
        POST a write operation, retrying transient failures.

        A failed batch with rollbackOnFailure=true leaves nothing partially
        applied, so retrying the same payload is safe.
        """
        last_error: Exception | None = None
        for attempt in range(1, WRITE_RETRIES + 1):
            try:
                response = self.session.post(
                    url, data=data, timeout=timeout or self.timeout
                )
                response.raise_for_status()
                return _raise_on_error(response.json(), context)
            except (ArcGISError, requests.RequestException) as exc:
                last_error = exc
                if attempt < WRITE_RETRIES:
                    wait = WRITE_RETRY_WAIT * (2 ** (attempt - 1))
                    logger.warning(
                        "%s failed (attempt %s/%s): %s -- retrying in %ss",
                        context, attempt, WRITE_RETRIES, exc, wait,
                    )
                    time.sleep(wait)
        raise ArcGISError(f"{context}: gave up after {WRITE_RETRIES} attempts") from last_error

    def get_object_ids(self, layer_id: int, where: str) -> list[int]:
        """ObjectIDs of every feature matching a WHERE clause."""
        response = self.session.get(
            f"{self.layer_url(layer_id)}/query",
            params={
                "f": "json",
                "where": where,
                "returnIdsOnly": "true",
                "token": self.token,
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        data = _raise_on_error(response.json(), f"id query on layer {layer_id}")
        return data.get("objectIds") or []

    def _delete_ids(self, layer_id: int, object_ids: list[int]) -> int:
        """
        Delete features by ObjectID, batched and retried. Returns rows deleted.

        Always delete by ID, never by WHERE: the delete parser on some layers
        rejects clauses containing '@' (present in location names like
        "US50 @ Cave Rock"), and timestamp literals are interpreted in the
        database's timezone rather than UTC. ID deletes sidestep both.

        A timed-out delete may still complete server-side, so a retry can
        report failures for rows that are simply already gone. A reported
        failure is therefore verified with an existence check before being
        treated as an error -- if the rows no longer exist, the delete
        achieved its goal.
        """
        deleted = 0
        for offset in range(0, len(object_ids), self.batch_size):
            batch = object_ids[offset : offset + self.batch_size]
            data = self._post_write(
                f"{self.layer_url(layer_id)}/deleteFeatures",
                {
                    "objectIds": ",".join(map(str, batch)),
                    "rollbackOnFailure": "true",
                    "f": "json",
                    "token": self.token,
                },
                f"deleteFeatures on layer {layer_id}",
                timeout=self.write_timeout,
            )
            results = data.get("deleteResults", [])
            failed = sum(1 for r in results if not r.get("success"))
            if failed:
                remaining = self.get_object_ids(
                    layer_id,
                    f"OBJECTID IN ({','.join(map(str, batch))})",
                )
                if remaining:
                    raise ArcGISError(
                        f"layer {layer_id}: {len(remaining)} row(s) reported "
                        "failed and still exist after delete"
                    )
                logger.info(
                    "  layer %s: %s delete(s) reported failed but rows are "
                    "gone (earlier timed-out call completed server-side)",
                    layer_id, failed,
                )
            deleted += len(results)
        return deleted

    def delete_where(self, layer_id: int, where: str) -> int:
        """Delete every feature matching a WHERE clause, via ID lookup."""
        return self._delete_ids(layer_id, self.get_object_ids(layer_id, where))

    def add_features(self, layer_id: int, features: list[dict]) -> int:
        """Add features in batches of `batch_size`. Returns rows added."""
        if not features:
            return 0

        total_batches = (len(features) + self.batch_size - 1) // self.batch_size
        added = 0

        for batch_num, offset in enumerate(
            range(0, len(features), self.batch_size), start=1
        ):
            batch = features[offset : offset + self.batch_size]
            data = self._post_write(
                f"{self.layer_url(layer_id)}/addFeatures",
                {
                    "features": json.dumps(batch),
                    "rollbackOnFailure": "true",
                    "f": "json",
                    "token": self.token,
                },
                f"addFeatures on layer {layer_id} (batch {batch_num}/{total_batches})",
                timeout=self.write_timeout,
            )
            results = data.get("addResults", [])
            succeeded = sum(1 for r in results if r.get("success"))
            failed = len(results) - succeeded
            if failed:
                first_error = next(
                    (r.get("error") for r in results if not r.get("success")), None
                )
                logger.warning(
                    "layer %s batch %s/%s: %s of %s failed. First error: %s",
                    layer_id, batch_num, total_batches, failed, len(results),
                    first_error,
                )
            added += succeeded

        return added

    def get_day_object_ids(
        self,
        layer_id: int,
        date_field: str,
        day: str | date,
        scope_field: str | None = None,
        scope_values: list | None = None,
    ) -> list[int]:
        """
        ObjectIDs of every row on one UTC calendar day.

        Two-step because the database compares timestamp literals in its own
        timezone (PST on this server) while storing UTC: over-select with a
        wide literal window, then filter each candidate's raw epoch -- returned
        in UTC ms regardless of database timezone -- to the exact day.
        """
        where = candidate_day_clause(date_field, day, scope_field, scope_values)
        candidates = self.query_all(
            layer_id, out_fields=f"OBJECTID,{date_field}", where=where
        )
        if candidates.empty:
            return []
        start_ms, end_ms = epoch_day_bounds(day)
        in_day = candidates[date_field].between(start_ms, end_ms - 1)
        return candidates.loc[in_day, "OBJECTID"].astype(int).tolist()

    def replace_day(
        self,
        layer_id: int,
        date_field: str,
        day: str | date,
        features: list[dict],
        label: str,
        scope_field: str | None = None,
        scope_values: list | None = None,
    ) -> tuple[int, int]:
        """
        Delete one day's rows (matched by raw epoch, see get_day_object_ids)
        then add its replacements.

        Not atomic -- the layer is briefly missing that day between the two
        calls. Scoping to a single day bounds the exposure, and for a monthly
        job that is an acceptable trade for idempotency.
        """
        object_ids = self.get_day_object_ids(
            layer_id, date_field, day, scope_field, scope_values
        )
        deleted = self._delete_ids(layer_id, object_ids)
        added = self.add_features(layer_id, features)
        logger.info("  %s: -%s +%s", label, deleted, added)
        return deleted, added

    def truncate(self, layer_id: int) -> int:
        """Delete every row. Used for the Speed layer, which has no date field."""
        return self.delete_where(layer_id, "1=1")
