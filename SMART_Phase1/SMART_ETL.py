"""
DERQ Data ETL Script
TRPA - Transportation SMART Phase 1

Incrementally fetches new data from the DERQ API and pushes it to ArcGIS Feature Services.
API is limited to 30 days per request, so date ranges are chunked automatically.

Layers:
    Safety Insights : FeatureServer/1  (date field: TimeAtSite)
    Vehicle Counts  : FeatureServer/3  (date field: Date)  -- 15-min intervals, source for daily counts
    VRU Counts      : FeatureServer/4  (date field: Date)
    Daily Counts    : FeatureServer/5  (date field: Date)  -- derived from Vehicle Counts layer
"""

import importlib
import subprocess
import sys

# ---------------------------------------------------------------------------
# Dependency check — runs before anything else
# ---------------------------------------------------------------------------

# Third-party packages required by this script.
# Format: (import_name, install_name)
_REQUIRED_PACKAGES = [
    ("requests",  "requests"),
    ("pandas",    "pandas"),
    ("dotenv",    "python-dotenv"),
]

def _ensure_dependencies():
    """Check for required packages and attempt to pip-install any that are missing."""
    missing = []
    for import_name, install_name in _REQUIRED_PACKAGES:
        if importlib.util.find_spec(import_name) is None:
            missing.append(install_name)

    if not missing:
        return  # all good

    print(f"Installing missing packages: {missing}")
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--quiet"] + missing
        )
        print("Packages installed successfully.")
    except subprocess.CalledProcessError as e:
        print(
            f"ERROR: Could not auto-install {missing}.\n"
            f"Please install manually:\n"
            f"  pip install {chr(32).join(missing)}\n"
            f"  or: conda install -c conda-forge {chr(32).join(missing)}"
        )
        sys.exit(1)

_ensure_dependencies()

# ---------------------------------------------------------------------------
# Standard imports (after dependency check)
# ---------------------------------------------------------------------------

import io
import json
import logging
import os
import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import requests
import pandas as pd
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

# Load credentials from .env file (must be in same directory as this script)
load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DERQ_API_URL = "https://api-external.cloud.derq.com"
DERQ_HEADERS = {"x-api-key": os.getenv("derq-api-key")}

ARCGIS_BASE_URL   = "https://maps.trpa.org/server/rest/services/Transportation_SMART/FeatureServer"
ARCGIS_PORTAL_URL = os.getenv("ARCGIS_PORTAL_URL", "https://maps.trpa.org/portal")
ARCGIS_USERNAME   = os.getenv("ARCGIS_USERNAME")
ARCGIS_PASSWORD   = os.getenv("ARCGIS_PASSWORD")

# Max features per addFeatures call (ArcGIS Enterprise default limit is 2000)
ARCGIS_BATCH_SIZE = 2000

# Set to True to simulate a full run without writing anything to ArcGIS.
# Flip to False (or set env var DRY_RUN=false) when ready to push real data.
DRY_RUN = os.getenv("DRY_RUN", "true").lower() != "false"

# ---------------------------------------------------------------------------
# Email / logging config
# ---------------------------------------------------------------------------

EMAIL_FROM   = os.getenv("EMAIL_FROM",   "info@trpa.gov")
EMAIL_TO     = os.getenv("EMAIL_TO",     "gis@trpa.gov")
SMTP_HOST    = os.getenv("SMTP_HOST",    "localhost")
SMTP_PORT    = int(os.getenv("SMTP_PORT", "25"))


# Each dataset: layer number and the field that holds the date/timestamp
LAYER_CONFIG = {
    "safety_insights": {
        "layer_id": 1,
        "date_field": "TimeAtSite",
    },
    "vehicle_counts": {
        "layer_id": 3,
        "date_field": "Date",
        "count_field": "counts",       # 15-min interval count field, used to derive daily counts
    },
    "vru_counts": {
        "layer_id": 4,
        "date_field": "Date",
    },
    "daily_counts": {
        "layer_id": 5,
        "date_field": "Date",
        "source": "vehicle_counts",    # derived by summing vehicle_counts per day per location
    },
}

DEFAULT_SPEED_BUCKETS = "5,10,15,20,25"
ALL_EVENT_TYPES = "IC, WWD, STPV, TV, LCV, RLV, NM-VV, NM-VRU, CRSH"
API_MAX_DAYS = 30  # DERQ API hard limit per request




# ---------------------------------------------------------------------------
# Logging setup — captures all print/log output to send in the email
# ---------------------------------------------------------------------------

def setup_logging() -> io.StringIO:
    """
    Configure the root logger to write to both stdout and an in-memory buffer.
    Returns the StringIO buffer so it can be read at the end of the run.
    """
    log_buffer = io.StringIO()

    # Format: timestamp + level + message
    formatter = logging.Formatter(
        fmt="%(asctime)s  %(levelname)-8s  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Stream to stdout (visible when running interactively)
    stdout_handler = logging.StreamHandler()
    stdout_handler.setFormatter(formatter)

    # Stream to in-memory buffer (captured for email)
    buffer_handler = logging.StreamHandler(log_buffer)
    buffer_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(stdout_handler)
    root.addHandler(buffer_handler)

    return log_buffer


def send_email(subject: str, body: str) -> None:
    """
    Send a plain-text email via the configured SMTP relay (no auth).

    Parameters:
        subject : email subject line
        body    : plain-text email body (the run log)
    """
    msg = MIMEMultipart()
    msg["From"]    = EMAIL_FROM
    msg["To"]      = EMAIL_TO
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
            server.sendmail(EMAIL_FROM, [EMAIL_TO], msg.as_string())
        logging.info(f"Email sent to {EMAIL_TO} — subject: {subject}")
    except Exception as e:
        # Log but never let email failure crash the script
        logging.error(f"Failed to send email: {e}")


# ---------------------------------------------------------------------------
# ArcGIS token + write helpers
# ---------------------------------------------------------------------------

def get_arcgis_token() -> str:
    """
    Generate a short-lived ArcGIS Enterprise token using username/password
    credentials stored in environment variables.

    The token is valid for 60 minutes — sufficient for a single ETL run.
    Credentials are never written to disk or logged.

    Returns:
        Token string to include in addFeatures requests.

    Raises:
        EnvironmentError : if ARCGIS_USERNAME or ARCGIS_PASSWORD are not set
        ValueError       : if the portal returns an error
        requests.HTTPError : on a non-2xx HTTP response
    """
    if not ARCGIS_USERNAME or not ARCGIS_PASSWORD:
        raise EnvironmentError(
            "ARCGIS_USERNAME and ARCGIS_PASSWORD must be set in your .env file."
        )

    url = f"{ARCGIS_PORTAL_URL}/sharing/rest/generateToken"
    payload = {
        "username"  : ARCGIS_USERNAME,
        "password"  : ARCGIS_PASSWORD,
        "client"    : "referer",
        "referer"   : ARCGIS_PORTAL_URL,
        "expiration": 60,          # minutes
        "f"         : "json",
    }

    response = requests.post(url, data=payload, timeout=30)
    response.raise_for_status()
    data = response.json()

    if "error" in data:
        raise ValueError(
            f"ArcGIS token error: {data['error'].get('message', data['error'])}"
        )
    if "token" not in data:
        raise ValueError(f"Unexpected token response: {data}")

    return data["token"]


def df_to_arcgis_features(df: pd.DataFrame, date_fields: list) -> list:
    """
    Convert a pandas DataFrame to a list of ArcGIS feature dicts suitable
    for the addFeatures REST endpoint.

    Date fields are converted to epoch milliseconds (UTC) as required by
    ArcGIS. All other fields are passed through as-is.

    Parameters:
        df          : DataFrame of records to convert
        date_fields : list of column names that contain date/datetime values

    Returns:
        List of {"attributes": {...}} dicts.
    """
    features = []
    for _, row in df.iterrows():
        attributes = {}
        for col, val in row.items():
            if col in date_fields:
                # Convert to epoch milliseconds; handle NaT gracefully
                try:
                    dt = pd.to_datetime(val, utc=True)
                    attributes[col] = int(dt.timestamp() * 1000)
                except Exception:
                    attributes[col] = None
            elif pd.isna(val):
                attributes[col] = None
            else:
                attributes[col] = val
        features.append({"attributes": attributes})
    return features


def push_to_arcgis(
    df: pd.DataFrame,
    layer_id: int,
    date_fields: list,
    token: str,
    dataset_name: str,
) -> int:
    """
    Push a DataFrame of new records to an ArcGIS Feature Service layer using
    the addFeatures REST endpoint, in batches to respect server limits.

    Parameters:
        df           : DataFrame of records to add
        layer_id     : ArcGIS FeatureServer layer number
        date_fields  : list of column names containing date/datetime values
        token        : valid ArcGIS token from get_arcgis_token()
        dataset_name : human-readable label for progress messages

    Returns:
        Total number of features successfully added.

    Raises:
        requests.HTTPError : on a non-2xx HTTP response
    """
    if df.empty:
        logging.info(f"{dataset_name}: no new records to push.")
        return 0

    features = df_to_arcgis_features(df, date_fields)
    total_batches = (len(features) + ARCGIS_BATCH_SIZE - 1) // ARCGIS_BATCH_SIZE

    # --- DRY RUN: print what would be pushed, skip the actual POST ---
    if DRY_RUN:
        logging.info(f"[DRY RUN] {dataset_name}: would push {len(features)} record(s) to layer {layer_id} in {total_batches} batch(es). No data written.")
        return 0

    url = f"{ARCGIS_BASE_URL}/{layer_id}/addFeatures"
    total_added = 0

    for batch_num, i in enumerate(range(0, len(features), ARCGIS_BATCH_SIZE), start=1):
        batch = features[i : i + ARCGIS_BATCH_SIZE]
        logging.info(f"{dataset_name}: pushing batch {batch_num}/{total_batches} ({len(batch)} records)...")

        payload = {
            "features" : json.dumps(batch),
            "rollbackOnFailure": "true",
            "f"        : "json",
            "token"    : token,
        }

        response = requests.post(url, data=payload, timeout=120)
        response.raise_for_status()
        result = response.json()

        if "error" in result:
            raise ValueError(
                f"addFeatures error on layer {layer_id}: "
                f"{result['error'].get('message', result['error'])}"
            )

        # Count successes; each item in addResults has a 'success' boolean
        add_results = result.get("addResults", [])
        succeeded = sum(1 for r in add_results if r.get("success"))
        failed    = len(add_results) - succeeded

        if failed:
            logging.warning(f"{failed} record(s) failed to add for {dataset_name} batch {batch_num}.")
        else:
            logging.info(f"  batch {batch_num} OK")

        total_added += succeeded

    logging.info(f"{dataset_name}: {total_added}/{len(features)} records added successfully.")
    return total_added


# ---------------------------------------------------------------------------
# ArcGIS helpers
# ---------------------------------------------------------------------------

def get_latest_date(layer_id: int, date_field: str) -> datetime:
    """
    Query a Feature Service layer and return the most recent date as a
    timezone-aware UTC datetime.

    Uses a statistics query so only one record is returned regardless of
    layer size.

    Parameters:
        layer_id   : ArcGIS FeatureServer layer number
        date_field : Name of the date/timestamp field to inspect

    Returns:
        datetime (UTC, timezone-aware)

    Raises:
        ValueError  : if the layer returns no data or the field is missing
        requests.HTTPError : on a non-2xx response
    """
    url = f"{ARCGIS_BASE_URL}/{layer_id}/query"
    params = {
        "f": "json",
        "where": "1=1",
        "outStatistics": (
            f'[{{"statisticType":"max","onStatisticField":"{date_field}",'
            f'"outStatisticFieldName":"latest_date"}}]'
        ),
    }

    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()

    # ArcGIS returns errors inside the JSON body too
    if "error" in data:
        raise ValueError(
            f"ArcGIS error on layer {layer_id}: {data['error'].get('message', data['error'])}"
        )

    features = data.get("features", [])
    if not features:
        raise ValueError(f"No features returned from layer {layer_id}.")

    raw_value = features[0].get("attributes", {}).get("latest_date")
    if raw_value is None:
        raise ValueError(
            f"Field '{date_field}' not found or has no data in layer {layer_id}."
        )

    # ArcGIS returns epoch milliseconds for date fields
    latest_dt = datetime.fromtimestamp(raw_value / 1000, tz=timezone.utc)
    return latest_dt


def get_all_latest_dates() -> dict:
    """
    Retrieve the latest date from every configured layer.

    Returns:
        dict mapping dataset name -> datetime (UTC)
        e.g. {"safety_insights": datetime(...), "vehicle_counts": datetime(...), ...}
    """
    latest_dates = {}
    for name, config in LAYER_CONFIG.items():
        logging.info(f"Checking latest date for '{name}' (layer {config['layer_id']})")
        try:
            latest_dt = get_latest_date(config["layer_id"], config["date_field"])
            latest_dates[name] = latest_dt
            logging.info(f"  -> Latest: {latest_dt.strftime('%Y-%m-%d')}")
        except Exception as e:
            logging.error(f"  -> ERROR: {e}")
            latest_dates[name] = None
    return latest_dates



# ---------------------------------------------------------------------------
# Date chunking helpers
# ---------------------------------------------------------------------------

def build_date_chunks(latest_dt: datetime, max_days: int = API_MAX_DAYS) -> list:
    """
    Build a list of (start_date, end_date) string tuples covering the gap
    between the latest stored date and yesterday, split into chunks no
    larger than max_days to respect the DERQ API limit.

    Dates are formatted as 'YYYY-MM-DD' strings as required by the DERQ API.

    Parameters:
        latest_dt : most recent datetime already stored in ArcGIS (UTC)
        max_days  : maximum days per chunk (default: API_MAX_DAYS = 30)

    Returns:
        List of (start_date, end_date) tuples as 'YYYY-MM-DD' strings.
        Returns an empty list if the data is already up to date.

    Example:
        latest_dt = 2025-08-08, today = 2026-03-03
        chunks = [
            ("2025-08-09", "2025-09-07"),
            ("2025-09-08", "2025-10-07"),
            ...
            ("2026-02-02", "2026-03-02"),
        ]
    """
    today = datetime.now(tz=timezone.utc).date()
    yesterday = today - timedelta(days=1)

    # ArcGIS timestamps are UTC midnight, so latest_dt.date() can equal today
    # if the timezone offset lands on midnight. Cap at yesterday to avoid
    # fetching a partial current day.
    latest_date = min(latest_dt.date(), yesterday)
    start = latest_date + timedelta(days=1)  # day after latest stored record

    if start > yesterday:
        return []  # already up to date

    chunks = []
    chunk_start = start
    while chunk_start <= yesterday:
        chunk_end = min(chunk_start + timedelta(days=max_days - 1), yesterday)
        chunks.append((chunk_start.isoformat(), chunk_end.isoformat()))
        chunk_start = chunk_end + timedelta(days=1)

    return chunks


def get_chunks_for_all_layers(latest_dates: dict) -> dict:
    """
    Build date chunks for every layer that has a valid latest date.
    Skips derived layers (daily_counts) since those are computed from
    vehicle_counts, not fetched from the DERQ API.

    Parameters:
        latest_dates : dict of dataset name -> datetime (from get_all_latest_dates)

    Returns:
        dict of dataset name -> list of (start, end) chunk tuples
    """
    DERIVED_LAYERS = {"daily_counts"}  # not fetched from DERQ directly

    chunks_map = {}
    for name, latest_dt in latest_dates.items():
        if name in DERIVED_LAYERS:
            continue
        if latest_dt is None:
            logging.warning(f"Skipping '{name}' — could not determine latest date.")
            continue
        chunks = build_date_chunks(latest_dt)
        chunks_map[name] = chunks
        if chunks:
            logging.info(f"  {name:<20} {len(chunks)} chunk(s)  {chunks[0][0]} -> {chunks[-1][1]}")
        else:
            logging.info(f"  {name:<20} already up to date, no fetch needed.")

    return chunks_map

# ---------------------------------------------------------------------------
# DERQ API helpers
# ---------------------------------------------------------------------------

def get_derq_locations() -> pd.DataFrame:
    """
    Fetch all DERQ sensor locations for the Tahoe deployment.

    Returns:
        DataFrame with at least LocationId and LocationName columns.

    Raises:
        requests.HTTPError : on a non-2xx response
        ValueError         : if the response body is empty or malformed
    """
    url = f"{DERQ_API_URL}/locations"
    response = requests.get(url, headers=DERQ_HEADERS, timeout=30)
    response.raise_for_status()
    data = response.json()
    locations = data.get("body", [])
    if not locations:
        raise ValueError("No locations returned from DERQ API.")
    return pd.DataFrame(locations)


# Retryable HTTP status codes from the DERQ API
_RETRY_STATUS_CODES = {429, 500, 502, 503, 504}
_MAX_RETRIES        = 4      # attempts total (1 original + 3 retries)
_RETRY_BACKOFF_BASE = 10     # seconds; doubles each retry (10, 20, 40)


def _fetch_derq_endpoint(url: str, dataset_name: str) -> pd.DataFrame:
    """
    Internal helper: GET a DERQ endpoint and return the response body as a
    DataFrame. Retries up to _MAX_RETRIES times with exponential backoff on
    rate-limit (429) and server errors (5xx) before giving up.

    Parameters:
        url          : fully-formed DERQ API URL
        dataset_name : human-readable label used in warning messages

    Returns:
        DataFrame of records, or empty DataFrame if all retries fail.
    """
    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            response = requests.get(url, headers=DERQ_HEADERS, timeout=60)

            # Handle retryable HTTP errors before raise_for_status
            if response.status_code in _RETRY_STATUS_CODES:
                if attempt < _MAX_RETRIES:
                    wait = _RETRY_BACKOFF_BASE * (2 ** (attempt - 1))
                    logging.warning(f"HTTP {response.status_code} for {dataset_name} (attempt {attempt}/{_MAX_RETRIES}). Retrying in {wait}s...")
                    time.sleep(wait)
                    continue
                else:
                    logging.error(f"HTTP {response.status_code} for {dataset_name} after {_MAX_RETRIES} attempts. Skipping chunk.")
                    return pd.DataFrame()

            response.raise_for_status()
            data = response.json()

            if str(data.get("statusCode")) != "200":
                logging.warning(f"API returned statusCode={data.get('statusCode')} for {dataset_name}. Skipping chunk.")
                return pd.DataFrame()

            records = data.get("body", [])
            return pd.DataFrame(records) if records else pd.DataFrame()

        except requests.HTTPError as e:
            logging.error(f"HTTP ERROR for {dataset_name}: {e}. Skipping chunk.")
            return pd.DataFrame()
        except requests.Timeout:
            if attempt < _MAX_RETRIES:
                wait = _RETRY_BACKOFF_BASE * (2 ** (attempt - 1))
                logging.warning(f"TIMEOUT for {dataset_name} (attempt {attempt}/{_MAX_RETRIES}). Retrying in {wait}s...")
                time.sleep(wait)
            else:
                logging.error(f"TIMEOUT for {dataset_name} after {_MAX_RETRIES} attempts. Skipping chunk.")
                return pd.DataFrame()
        except Exception as e:
            logging.error(f"UNEXPECTED ERROR for {dataset_name}: {e}. Skipping chunk.")
            return pd.DataFrame()

    return pd.DataFrame()


def fetch_dataset_for_location(
    dataset_name: str,
    location_id: str,
    location_name: str,
    start_date: str,
    end_date: str,
) -> pd.DataFrame:
    """
    Fetch one dataset type for one location over a single date chunk.

    Parameters:
        dataset_name  : one of 'safety_insights', 'vehicle_counts', 'vru_counts'
        location_id   : DERQ location ID string
        location_name : human-readable location name (added to returned DataFrame)
        start_date    : 'YYYY-MM-DD'
        end_date      : 'YYYY-MM-DD'

    Returns:
        DataFrame with records plus LocationId and LocationName columns appended.
        Empty DataFrame if no data or an error occurs.
    """
    base = DERQ_API_URL
    if dataset_name == "safety_insights":
        url = (f"{base}/safety-insights?locationId={location_id}"
               f"&startDate={start_date}&endDate={end_date}"
               f"&eventTypes={ALL_EVENT_TYPES}")
    elif dataset_name == "vehicle_counts":
        url = (f"{base}/counts/vehicle?locationId={location_id}"
               f"&startDate={start_date}&endDate={end_date}")
    elif dataset_name == "vru_counts":
        url = (f"{base}/counts/vru?locationId={location_id}"
               f"&startDate={start_date}&endDate={end_date}")
    else:
        raise ValueError(f"Unknown dataset_name: '{dataset_name}'")

    df = _fetch_derq_endpoint(url, f"{dataset_name}/{location_name}")
    if not df.empty:
        df["LocationId"] = location_id
        df["LocationName"] = location_name
    return df


def fetch_all_new_data(chunks_map: dict, df_locations: pd.DataFrame) -> dict:
    """
    Iterate over all datasets and date chunks, fetching new records from the
    DERQ API for every location.

    Parameters:
        chunks_map   : output of get_chunks_for_all_layers()
        df_locations : DataFrame of DERQ locations (LocationId, LocationName)

    Returns:
        dict mapping dataset name -> combined DataFrame of all new records.
        Datasets with no new data are mapped to an empty DataFrame.
    """
    results = {}

    for dataset_name, chunks in chunks_map.items():
        if not chunks:
            logging.info(f"{dataset_name}: already up to date, skipping.")
            results[dataset_name] = pd.DataFrame()
            continue

        logging.info(f"Fetching '{dataset_name}' — {len(chunks)} chunk(s) x {len(df_locations)} location(s) = {len(chunks) * len(df_locations)} API calls")

        all_records = []
        for chunk_start, chunk_end in chunks:
            logging.info(f"  Chunk {chunk_start} -> {chunk_end}")
            for _, loc_row in df_locations.iterrows():
                location_id   = loc_row["LocationId"]
                location_name = loc_row["LocationName"]
                df_chunk = fetch_dataset_for_location(
                    dataset_name, location_id, location_name,
                    chunk_start, chunk_end
                )
                if not df_chunk.empty:
                    all_records.append(df_chunk)

        if all_records:
            combined = pd.concat(all_records, ignore_index=True)
            logging.info(f"  -> {len(combined)} total new records for '{dataset_name}'")
        else:
            combined = pd.DataFrame()
            logging.info(f"  -> No new records found for '{dataset_name}'")

        results[dataset_name] = combined

    return results



def compute_daily_counts(df_vehicle: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate 15-minute interval vehicle counts into daily totals per location.

    Expects df_vehicle to have columns: Date, LocationId, LocationName, counts.
    Groups by date (day only) and location, summing the counts field.

    Parameters:
        df_vehicle : DataFrame of 15-min vehicle count records

    Returns:
        DataFrame with columns: Date, LocationId, LocationName, counts
        One row per day per location.
    """
    if df_vehicle.empty:
        return pd.DataFrame(columns=["Date", "LocationId", "LocationName", "counts"])

    df = df_vehicle.copy()

    # Normalize Date to date-only (strip time component) for daily grouping
    df["Date"] = pd.to_datetime(df["Date"]).dt.normalize()

    daily = (
        df.groupby(["Date", "LocationId", "LocationName"], as_index=False)["counts"]
        .sum()
    )

    return daily


# ---------------------------------------------------------------------------
# Sanity check — run this first to confirm layers are readable
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Set up logging to stdout + in-memory buffer (buffer is emailed at end of run)
    log_buffer = setup_logging()
    has_errors = False

    try:
        logging.info("=" * 60)
        logging.info("DERQ ETL - Step 1: Checking latest dates in ArcGIS layers")
        logging.info("=" * 60)

        results = get_all_latest_dates()

        logging.info("Latest date summary:")
        for name, dt in results.items():
            config = LAYER_CONFIG[name]
            source = "  [derived from vehicle_counts]" if config.get("source") else ""
            if dt:
                days_behind = (datetime.now(tz=timezone.utc) - dt).days
                logging.info(f"  {name:<20} latest={dt.strftime('%Y-%m-%d')}  ({days_behind} days behind today){source}")
            else:
                logging.warning(f"  {name:<20} could not determine latest date{source}")
                has_errors = True

        # Warn if daily_counts is out of sync with vehicle_counts
        vc = results.get("vehicle_counts")
        dc = results.get("daily_counts")
        if vc and dc and dc > vc:
            logging.warning("daily_counts is ahead of vehicle_counts — something may be wrong.")
            has_errors = True
        elif vc and dc and dc < vc:
            days_diff = (vc - dc).days
            logging.info(f"daily_counts is {days_diff} day(s) behind vehicle_counts — will be caught up on next run.")

        logging.info("-" * 60)
        logging.info("Step 2: Building date chunks for DERQ API calls")
        logging.info("-" * 60)
        chunks_map = get_chunks_for_all_layers(results)
        total_chunks = sum(len(c) for c in chunks_map.values())
        logging.info(f"Total API calls queued: {total_chunks} chunk(s) across {len(chunks_map)} dataset(s).")

        logging.info("-" * 60)
        logging.info("Step 3: Fetching new data from DERQ API")
        logging.info("-" * 60)
        logging.info("Fetching DERQ locations...")
        try:
            df_locations = get_derq_locations()
            logging.info(f"Found {len(df_locations)} location(s): {list(df_locations['LocationName'])}")
        except Exception as e:
            logging.error(f"ERROR fetching locations: {e}")
            has_errors = True
            raise SystemExit(1)

        new_data = fetch_all_new_data(chunks_map, df_locations)

        logging.info("Fetch complete. Summary of new records:")
        for name, df in new_data.items():
            logging.info(f"  {name:<20} {len(df)} new record(s)")

        logging.info("-" * 60)
        dry_label = " [DRY RUN — no data will be written]" if DRY_RUN else " [LIVE — writing to ArcGIS]"
        logging.info(f"Step 4: Pushing new data to ArcGIS Feature Services{dry_label}")
        logging.info("-" * 60)

        if DRY_RUN:
            logging.info("Skipping token generation (DRY RUN).")
            token = None
        else:
            logging.info("Generating ArcGIS token...")
            try:
                token = get_arcgis_token()
                logging.info("Token obtained successfully.")
            except EnvironmentError as e:
                logging.error(f"CREDENTIALS ERROR: {e}")
                has_errors = True
                raise SystemExit(1)
            except Exception as e:
                logging.error(f"ERROR generating token: {e}")
                has_errors = True
                raise SystemExit(1)

        DATE_FIELDS = {
            "safety_insights": ["TimeAtSite"],
            "vehicle_counts" : ["Date"],
            "vru_counts"     : ["Date"],
            "daily_counts"   : ["Date"],
        }

        push_summary = {}
        for name, df in new_data.items():
            if df.empty:
                push_summary[name] = 0
                continue
            layer_id    = LAYER_CONFIG[name]["layer_id"]
            date_fields = DATE_FIELDS.get(name, [])
            added = push_to_arcgis(df, layer_id, date_fields, token, name)
            push_summary[name] = added

        new_vehicle_df = new_data.get("vehicle_counts", pd.DataFrame())
        if not new_vehicle_df.empty:
            logging.info("Computing daily counts from new vehicle count records...")
            df_daily_new = compute_daily_counts(new_vehicle_df)
            logging.info(f"{len(df_daily_new)} new daily count record(s) to push.")
            added = push_to_arcgis(df_daily_new, LAYER_CONFIG["daily_counts"]["layer_id"],
                                   DATE_FIELDS["daily_counts"], token, "daily_counts")
            push_summary["daily_counts"] = added
        else:
            logging.info("No new vehicle counts — skipping daily counts update.")
            push_summary["daily_counts"] = 0

        logging.info("=" * 60)
        logging.info("ETL Complete. Final summary:")
        logging.info("=" * 60)
        for name, count in push_summary.items():
            logging.info(f"  {name:<20} {count} record(s) added to ArcGIS")

    except SystemExit:
        has_errors = True
        raise
    except Exception as e:
        logging.error(f"Unhandled exception: {e}", exc_info=True)
        has_errors = True
    finally:
        # Always send the email, subject flags errors if any occurred
        run_date  = datetime.now().strftime("%Y-%m-%d %H:%M")
        dry_tag   = " [DRY RUN]" if DRY_RUN else ""
        err_tag   = " ⚠ ERRORS" if has_errors else " ✓ OK"
        subject   = f"DERQ ETL{dry_tag}{err_tag} — {run_date}"
        log_body  = log_buffer.getvalue()
        send_email(subject, log_body)