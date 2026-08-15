# SMART Phase 1 -- Tahoe Basin Traffic Camera Data

ETL and data-package tooling for the USDOT SMART grant *Intelligent Sensor
Integration on Rural Multi-Modal System with an Urban Recreation Travel Demand*
(grant `SMARTFY22N1P1G41`), a Tahoe Transportation District project with TRPA as
the data and open-data partner.

Pulls vehicle counts, vulnerable road user counts, safety events and speed
distributions from the DERQ INSIGHT API for AI-enabled cameras around the Lake
Tahoe Basin, and publishes them to the `Transportation_SMART` feature service on
`maps.trpa.org`.

Downstream consumers:

- [ArcGIS dashboard](https://trpa.maps.arcgis.com/apps/dashboards/4528512a81d8475e90fc0ad713cb2489)
- [Tahoe Open Data -- Transportation Patterns](https://www.tahoeopendata.org/pages/transportation-patterns)
- The DOI-archived data package, <https://doi.org/10.21949/1530332>

## Setup

```bash
conda create --name smart-etl --clone arcgispro-py3
conda activate smart-etl
pip install -r requirements.txt
```

Do not `pip install` into the ArcGIS Pro base environment. The ETL itself needs
only `requests`, `pandas`, `python-dotenv` and `PyYAML` -- it talks to the
feature service over plain REST and never imports `arcpy`, so any Python 3.9+
environment works.

Then copy `.env.template` to `.env` and fill in the DERQ API key and an ArcGIS
account with edit rights on the service. `.env` is gitignored.

## Running

```bash
python scripts/run_etl.py --preflight
```

Validates every field map in `config.yaml` against the live layer schemas and
exits. Writes nothing. Run this after any schema change.

```bash
python scripts/run_etl.py --dry-run
```

Full simulation: fetches from DERQ, maps the fields, reports exactly what would
be written. Touches nothing on the service.

```bash
python scripts/run_etl.py --live
```

The scheduled run. Works back `run.lookback_days` from each layer's own max date
and replaces every day in that window.

Backfill an explicit window, caching raw responses so an interruption resumes:

```bash
python scripts/run_etl.py --start 2025-09-07 --end 2025-09-30 --live --resume
```

## How loading works

Each calendar day is **deleted and re-added** rather than appended. Re-running
the same window is a no-op instead of a source of duplicates, and a partial
final day -- normal, since the API returns whatever has landed so far -- heals
itself on the next run. The delete is scoped to the locations that actually
returned data, so a camera that had an API outage on a given day keeps its
existing rows instead of losing them.

The Speed layer has no date field. It holds one whole-of-record distribution per
location, interval and approach, so it is rebuilt by truncate-and-replace from
the full history on every run.

`daily_counts` (layer 5) is derived by summing the fifteen-minute vehicle counts,
grouped by date and location **name** -- that layer has no `LocationId` field.

### The DERQ request quota

Confirmed by Derq (Aug 2026): **1,000 requests per day per API key across all
endpoints**, max 5 requests/second. `derq.max_requests_per_run` in config.yaml
(default 850) hard-stops a run below the cap -- remaining chunks are recorded
as failures and a `--resume` re-run finishes them after the quota resets. Three
consecutive rate-limited chunks trigger the same fast-fail, since grinding
retries into an exhausted quota wastes hours.

A scheduled incremental run costs roughly 90-120 requests (the Speed rebuild
reuses permanently cached historical chunks and refetches only the final,
still-moving window), so the quota comfortably supports a weekly or monthly
cadence. A from-scratch backfill (~1,100 requests) needs two days or a
temporary limit increase from Derq.

### The DERQ date-boundary quirk

The API filters `startDate`/`endDate` at **UTC midnight**, but the data is
stamped in **local Pacific time**. Verified live: a request for `[D1, D2]`
returns a partial `D1-1` (evening only, 28 of 96 fifteen-minute intervals), a
partial `D2-1` (midnight to ~5 PM, 68 of 96), and only `[D1, D2-2]` complete.
A naive single-day request returns zero records.

`DerqClient.fetch_window` therefore pads every request by two days and trims
each chunk back to its own complete days (per chunk, not at the end -- padded
requests overlap at chunk seams, and a late trim would keep seam days twice).
The `source_date_field` entry in each dataset's config names the raw payload
column used for the trim. Speed has no date field, so it cannot be trimmed and
accepts sub-day fuzz at the edges of its whole-of-record aggregate.

### Field mapping

The DERQ API and the feature service disagree on names: DERQ returns `count` and
`date`, the layers use `counts` and `Date`. Every rename lives in the `datasets`
block of `config.yaml`, and `--preflight` refuses to run if any mapped target
does not exist on the live layer.

The service schema is frozen because it backs a live dashboard and a published
open-data page, so DERQ fields with no target column are dropped: `lane` and
`movement` from vehicle counts, `headingDirection` and `movement` from VRU
counts. Row granularity is preserved -- one row per DERQ record, not aggregated
-- so totals and row counts stay continuous with the DOI-archived dataset.

`Camera_Status` on Safety Insights is not a DERQ field at all -- it is a
denormalized copy of the camera's `Status`, populated on all 24,244 existing
rows. The `enrich_from_locations` block in `config.yaml` joins it from the
locations layer at load time so new rows stay consistent with the published
history.

## Scheduling

`run_monthly.bat` is the Task Scheduler entry point. Set **Start in** to this
directory and point `PYTHON` inside the script at your environment. It exits
non-zero on failure so Task Scheduler reports the result correctly. The host must
reach both `api-external.cloud.derq.com` and `maps.trpa.org`.

A run summary is emailed via the smtp2go relay; set `email.enabled: false` in
`config.yaml` to turn it off.

## Regenerating the deliverables

```bash
python scripts/build_data_dictionary.py    # -> Documentation/Data_Dictionary.csv
python scripts/build_data_package.py       # -> data/exports/<package_name>.zip
```

The data dictionary is generated from the **live** layer schemas joined to
`metadata/field_descriptions.yaml`, and reports any field it cannot describe, so
it cannot drift from what is actually published. Run it before the package
builder, which bundles it.

The package builder exports every layer, renders the USDOT README and the
DCAT-US `MetadataPackage.json` with row and column counts read from the service,
copies the attachments listed in `metadata/data_package.yaml`, and zips the
result. Attachments it cannot find are reported rather than silently skipped --
the wrong-way-driver video clips currently live inside the published Phase 1 zip
and need extracting to the path named in that file.

## Tests

```bash
python -m pytest tests -m "not network"    # offline
python -m pytest tests -m network          # contract tests vs maps.trpa.org
```

The network tests assert that `config.yaml` still matches the live schemas, that
the service still allows Delete, and that the batch size is within
`maxRecordCount`. Run them after anyone edits the feature service.

## Layout

```
config.yaml            service URLs, layer map, field maps, run windows
.env                   credentials (gitignored)
run_monthly.bat        Task Scheduler entry point
scripts/
  smart_config.py      config + .env loading
  derq_client.py       DERQ API: retry, chunking, raw-response cache
  arcgis_client.py     token, query, delete-where, batched add
  transforms.py        field mapping, epoch conversion, aggregations
  run_etl.py           CLI orchestrator
  build_data_dictionary.py
  build_data_package.py
metadata/              field descriptions, data package values
templates/             USDOT README and DCAT-US templates
tests/                 offline + network contract tests
notebooks/             Data_QAQC.ipynb -- post-run checks
data/                  gitignored: raw cache, run state, exports
Data/                  committed Phase 1 record and published DOI package
Documentation/         API PDF, generated data dictionary, Archive/
Parametrix_Samples/    consultant's Microsoft Fabric pipeline, for reference
```

`Documentation/Archive/` holds the superseded Phase 1 scripts with notes on why
each was retired.
