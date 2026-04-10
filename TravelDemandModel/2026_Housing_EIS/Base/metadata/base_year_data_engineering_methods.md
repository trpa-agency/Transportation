# Base Year Data Engineering — Methods and Results

**Script:** `scripts/base_year_data_engineering.ipynb`  
**Project:** 2026 Housing EIS Travel Demand Model — Base Year  
**Author:** TRPA Data Team  
**Last Updated:** April 2026

---

## Overview

This notebook implements a parcel-level data engineering pipeline that builds TAZ (Traffic Analysis Zone) input files for the regional travel demand model. It integrates property inventory, occupancy rates, census demographics, employment, campground, and school enrollment data from TRPA web services and local lookup tables, and aggregates all attributes to the TAZ level for model input.

Parquet checkpoints are saved after each major stage so the pipeline can be resumed at any point without re-fetching source data.

---

## Configuration

| Parameter | Value |
|---|---|
| Parcel Year | 2022 |
| School Year | 2021–2022 |
| Census Year | 2022 |
| Occupancy Timeframes | June 1, August 1, September 1, 2022 |
| Default TAU Occupancy Rate | 59.23% |
| Default VHR Occupancy Rate | 42.23% |
| Household Size Adjustment Factor | 1.021 |

The adjustment factor corrects modeled household size to match the ACS-derived basin total (53,953 persons / 52,788.25 model-calculated).

---

## Input Data Sources

All spatial and tabular data are fetched from TRPA REST services at `https://maps.trpa.org/server/rest/services`.

| Dataset | Service Layer | Query Filter | Notes |
|---|---|---|---|
| Parcels | `Existing_Development/MapServer/2` | `Year = 2022` | APN, units, commercial floor area |
| VHR Registry | `VHR/MapServer/0` | — | APNs registered as vacation home rentals |
| TAZ Boundaries | `Transportation_Planning/MapServer/6` | — | Polygon layer |
| Block Groups | `Demographics/MapServer/27` | — | Filtered to 2020 vintage, block-group level |
| Census Demographics | `Demographics/MapServer/28` | `year_sample = 2022` | Occupancy, household size, income (ACS 5-year) |
| Occupancy Zones | `Transportation_Planning/MapServer/15` | — | Zone polygons for rate averaging |
| Occupancy Rates | `data/raw_data/occupancy_rates.csv` | — | Pre-aggregated summer rates by zone and room type. **Not fetched from the web service** — the service schema changed and returns incomplete zone coverage (see Gotcha #9). Update this CSV when changing base year. |
| Campgrounds | `Recreation/MapServer/1` | `RECREATION_TYPE = 'Campground'` | Location and site counts — type filter required; layer contains all recreation sites |
| Campground Visits | `Transportation_Planning/MapServer/14` | `Year = 2022` | Occupancy rates by campground — year filter required; layer contains multiple years |
| Schools (spatial) | `Transportation_Planning/MapServer/16` | — | Location and enrollment by name |
| Schools (table) | `Transportation_Planning/MapServer/17` | `Year = '2021-2022'` | Enrollment by school year |

**Local Lookup Files** (in `scripts/Lookup_Lists/`):

| File | Purpose |
|---|---|
| `development_2022_2025.csv` | Unit count changes for specific APNs |
| `closed_tourist_parcels.csv` | TAU parcels to zero out (closed facilities) |
| `lookup_tau_type.csv` | TAU type overrides (HotelMotel / Casino / Resort) |
| `income_census_codes.csv` | Maps ACS variable codes to income categories |

---

## Processing Stages

### Stage 1 — Data Acquisition

Fetches all source datasets from TRPA web services into memory. Service URL and field availability are verified before downstream processing.

---

### Stage 2 — Parcel Classification and Spatial Joins

#### 2a. Unit Adjustments
Known development project changes (2022–2025) are applied to parcel unit counts, creating `Residential_Units_Adjusted`.

#### 2b. VHR Flag
Parcels present in the VHR registry receive a `VHR = "Yes"` flag.

#### 2c. TAU Type Classification
Default logic: parcels with no TAU units = `"N/A"`; parcels with TAU units = `"HotelMotel"`. The `lookup_tau_type.csv` overrides specific APNs with `"Casino"` or `"Resort"`.

#### 2d. Closed Facility Zeroing
`TouristAccommodation_Units` is set to zero for APNs listed in `closed_tourist_parcels.csv`.

#### 2e. Spatial Joins (ArcPy)
Parcel centroids are spatially joined to:
- TAZ boundaries (match option: HAVE_THEIR_CENTER_IN)
- 2020 Census block groups
- Occupancy zones

CSLT VHR parcels receive an override: their occupancy zone is set to `"CSLT_ALL"` to aggregate occupancy rates for that jurisdiction.

**Checkpoint:** `parcel_spatial_joins_{RUN_DATE}.parquet`

---

### Stage 3 — Occupancy Rate Application

Monthly occupancy rates for June, August, and September 2022 are averaged by zone and property type. Rates are then mapped to parcels based on their assigned occupancy zone:

- **TAU rate** applied to parcels classified as HotelMotel, Casino, or Resort
- **VHR rate** applied to parcels flagged as VHR

Zero rates are applied where no relevant unit type exists.

**Checkpoints:** `occupancy_rates_table_{RUN_DATE}.parquet`, `parcel_occupancy_rates_{RUN_DATE}.parquet`

---

### Stage 4 — IDW Interpolation for Missing Rates

TAU or VHR parcels with missing occupancy rates are filled using Inverse Distance Weighting (IDW):

- Parcel polygons converted to centroids
- IDW raster generated (power = 2, cell size = 100 m) from known-rate parcel centroids
- IDW values extracted back to target parcel points
- Basin-wide defaults (59.23% TAU, 42.23% VHR) applied as final fallback

**Checkpoint:** `parcel_occupancy_interpolated_{RUN_DATE}.parquet`

---

### Stage 5 — Census / Socioeconomic Attribution

#### 5a. Residential Occupancy Rates
From ACS variables by block group:
- `B25002_002E` — occupied units
- `B25002_003E` — vacant units
- `B25004_006E` — vacant for seasonal use

Derived rates:
- `PrimaryResidence_Rate` = occupied / total units
- `SecondaryResidence_Rate` = seasonal vacant / vacant units

#### 5b. Household Size
From ACS variable `B25010_001E` (average household size of occupied units), multiplied by the adjustment factor (1.021) to create `PersonsPerUnit`.

#### 5c. Income Distribution
ACS income bracket variables (mapped via `income_census_codes.csv`) are grouped into High, Medium, and Low categories by block group. Proportions are calculated as shares of total income-reported households:
- `HighIncome_Rate`, `MediumIncome_Rate`, `LowIncome_Rate`

#### 5d. Unit Derivation
Block-group attributes are joined to parcels, then the following unit counts are derived:

| Field | Calculation |
|---|---|
| `OccupiedUnits` | Residential_Units × PrimaryResidence_Rate |
| `UnoccupiedUnits` | Residential_Units − OccupiedUnits |
| `SeasonalUnits` | UnoccupiedUnits × SecondaryResidence_Rate |
| `HighUnits` | OccupiedUnits × HighIncome_Rate |
| `MediumUnits` | OccupiedUnits × MediumIncome_Rate |
| `LowUnits` | OccupiedUnits × LowIncome_Rate |
| `People` | OccupiedUnits × PersonsPerUnit |

VHR units are subtracted from seasonal estimates to prevent double-counting. Block group `3200500170022020` has seasonal units manually zeroed due to a Beach Club data lag.

**Checkpoint:** `parcel_socioeconomic_{RUN_DATE}.parquet`

---

### Stage 6 — Campground Processing

Campground locations (filtered to `RECREATION_TYPE = 'Campground'`) are spatially joined to TAZs using ArcPy. Campground visit records (filtered to `Year = 2022`) are merged onto campground records by name. Bayview Campground is excluded. The `campground` column in the output represents **total site capacity** (`Total_Sites`), consistent with the 2022 RTP base year:

`campground = Total_Sites` (aggregated to TAZ)

`SitesSold = Total_Sites × Occupancy_Rate` is also computed and retained internally but is used only for the occupancy rate output, not the overnight visitor capacity table.

**Checkpoint:** `campground_taz_{RUN_DATE}.parquet`

---

### Stage 7 — School Enrollment Processing

School locations are spatially joined to TAZs. School type (Elementary, Middle, High, College) is inferred from school name. Enrollment is summed by type and TAZ and pivoted to one row per TAZ.

**Output:** `SchoolEnrollment_{RUN_DATE}.csv`  
**Checkpoint:** `school_enrollment_{RUN_DATE}.parquet`

---

### Stage 8 — TAZ Aggregation and CSV Export

All parcel-level checkpoints are loaded and aggregated to TAZ level. Five model input files are produced:

| File | Contents |
|---|---|
| `OvernightVisitorZonalData_Summer_{RUN_DATE}.csv` | TAU rooms by type (HotelMotel, Casino, Resort), campground sites (Total_Sites), seasonal percentage, rec attractiveness |
| `VisitorOccupancyRates_Summer_{RUN_DATE}.csv` | Weighted TAU occupancy rate and mean VHR occupancy rate per TAZ |
| `SocioEcon_Summer_{RUN_DATE}.csv` | Residential units, occupied units, occupancy rate, seasonal rate, household size, income distribution proportions, persons |
| `Employment_{RUN_DATE}.csv` | Employment by sector and TAZ |
| `inputs_summarized_{RUN_DATE}.csv` | All five tables merged on TAZ (wide format) |

---

### Stage 9 — QA and Basin Summary

A basin-wide QA table is produced for comparison against prior base years. Checks include:

- TAZ assignment completeness
- Null rate distributions
- Output file existence and file sizes
- TAZ-level rounding with income tie-break (ensures non-zero occupied TAZs have at least 1 income-class unit)
- Population zeroing where `OccupiedUnits = 0` at TAZ level
- Optional comparison to prior-year summary if `inputs_summarized copy.csv` exists

**Output:** `taz_summarized_{RUN_DATE}.csv`

See `scripts/QA_2022_vs_2026.ipynb` for a full side-by-side comparison of all four output CSVs against the 2022 base year.

---

## Output Files

### Intermediate Checkpoints (`data/processed_data/`)

| File | Stage |
|---|---|
| `parcel_spatial_joins_{RUN_DATE}.parquet` | 2e |
| `occupancy_rates_table_{RUN_DATE}.parquet` | 3 |
| `parcel_occupancy_rates_{RUN_DATE}.parquet` | 3 |
| `parcel_occupancy_interpolated_{RUN_DATE}.parquet` | 4 |
| `parcel_socioeconomic_{RUN_DATE}.parquet` | 5 |
| `campground_taz_{RUN_DATE}.parquet` | 6 |
| `school_enrollment_{RUN_DATE}.parquet` | 7 |

### Final Model Inputs (`data/processed_data/`)

| File | Description |
|---|---|
| `OvernightVisitorZonalData_Summer_{RUN_DATE}.csv` | Lodging and campground units by TAZ |
| `VisitorOccupancyRates_Summer_{RUN_DATE}.csv` | TAU and VHR occupancy rates by TAZ |
| `SocioEcon_Summer_{RUN_DATE}.csv` | Residential demographics and income by TAZ |
| `Employment_{RUN_DATE}.csv` | Employment by sector and TAZ |
| `SchoolEnrollment_{RUN_DATE}.csv` | Enrollment by school type and TAZ |
| `inputs_summarized_{RUN_DATE}.csv` | Merged wide-format summary of all inputs |
| `taz_summarized_{RUN_DATE}.csv` | TAZ-level aggregation with rounded integers |

---

## Basin-Wide Summary Metrics

Comparison of key outputs between the 2022 RTP base year run and the 2026 Housing EIS base year run. All fixes have been applied and the notebook has been fully re-run. Values are final.

### OvernightVisitorZonalData_Summer.csv

| Metric | 2022 RTP | 2026 Housing EIS | Change | Notes |
|---|---|---|---|---|
| TAU rooms — HotelMotel | 5,187 | 4,906 | −281 | Closed facilities zeroed out |
| TAU rooms — Resort | 3,634 | 3,634 | 0 | No change |
| TAU rooms — Casino | 2,984 | 2,703 | −281 | TAZ 395/397 closed; TAZ 396 new |
| Campground sites | 1,964 | 1,964 | 0 | ✓ Matches after campground fixes |
| percentHouseSeasonal (sum) | 195.2 | 178.2 | −17.0 | Updated ACS seasonal vacancy rates |
| TAZ count | 282 | 282 | 0 | TAZ 355 added to `REQUIRED_OVERNIGHT_TAZS` (all-zero row, no parcel data) |

### SocioEcon_Summer.csv

| Metric | 2022 RTP | 2026 Housing EIS | Change | Notes |
|---|---|---|---|---|
| Residential units (total) | 49,390 | 49,950 | +560 | New development in parcel layer (`development_2022_2025.csv`) |
| Occupied units (total) | 23,296 | 23,655 | +359 | Driven by +560 units; census rates frozen to 2022 (Gotcha #11) |
| Total persons | 53,842 | 55,031 | +1,189 | +2.2%; development units + frozen 2022 household size |
| emp_retail | 0 | 3,711 | — | Now populated (was placeholder) |
| emp_srvc | 0 | 7,503 | — | Now populated (was placeholder) |
| emp_rec | 0 | 2,248 | — | Now populated (was placeholder) |
| emp_game | 0 | 2,564 | — | Now populated (was placeholder) |
| emp_other | 0 | 10,711 | — | Now populated (was placeholder) |
| **Employment total** | **0** | **26,737** | — | Now populated from 2022 source |

### SchoolEnrollment.csv

| Metric | 2022 RTP | 2026 Housing EIS | Change | Notes |
|---|---|---|---|---|
| Elementary enrollment | 2,879 | 2,879 | 0 | Unchanged — same school year |
| Middle enrollment | 1,240 | 1,240 | 0 | Unchanged |
| High school enrollment | 2,172 | 2,172 | 0 | Unchanged |
| College enrollment | 2,798 | 3,018 | +220 | TAZ 1 (+171) and TAZ 2 (+49) hardcoded — see Gotcha #12 |
| TAZ count | 282 | 296 | +14 | Phantom TAZs added (TAZs 1, 2 have college enrollment) |

### VisitorOccupancyRates_Summer.csv

Rates are per-TAZ fractions (0–1); the meaningful comparisons are TAZ count and average rate among active TAZs, not the sum.

| Metric | 2022 RTP | 2026 Housing EIS | Change | Notes |
|---|---|---|---|---|
| HotelMotel — TAZs with rate | 49 | 46 | −3 | Fewer TAZs with open HotelMotel units |
| HotelMotel — avg rate | 0.500 | 0.486 | −0.013 | Minor zone rate shift |
| Resort — TAZs with rate | 16 | 16 | 0 | Unchanged |
| Resort — avg rate | 0.523 | 0.508 | −0.015 | Minor zone rate shift |
| Casino — TAZs with rate | 6 | 5 | −1 | TAZ 395/397 closed |
| Casino — avg rate | 0.514 | 0.541 | +0.027 | Remaining casino zone rate slightly higher |
| Campground — TAZs with rate | 16 | 16 | 0 | ✓ Unchanged (copied from 2022) |
| House/Seasonal — TAZs with rate | 169 | 182 | +13 | See note below |
| House/Seasonal — avg rate | 0.464 | 0.464 | 0 | Patched to match 2022 — see Gotcha #10 |
| Unique hotelmotel rate values | 18 | 16 | — | ✓ Zone lookup working (was 3 before fix) |

**House/seasonal rate note:** The corrected zone lookup (CSLT_ALL override) produces a higher average rate (~0.487) than the 2022 run because 31 CSLT TAZs that incorrectly received the basin-wide default (0.4223) in 2022 now get the correct CSLT-wide VHR rate (0.5258). However, because these inputs are a 2025 forecast run on a model calibrated to the 2022 values, the house/seasonal rates are patched back to the 2022 per-TAZ values in Stage 8 (see Gotcha #10). The average shown above reflects the patched output. The +13 TAZ count change is real and retained: 14 TAZs newly have registered VHR parcels that did not appear in the 2022 run.

---

## Key Design Decisions

- **Parquet checkpoints** avoid pickle version lock-in and enable stage-level resumption.
- **Spatial reference** for all ArcPy operations: NAD 1983 UTM Zone 10N.
- **Block group filtering** to 2020 vintage and 16-character TRPAID ensures correct census joins.
- **VHR double-counting prevention:** VHR units are subtracted from seasonal estimates before the seasonal rate is applied.
- **CSLT VHR override:** All CSLT VHR parcels use the combined `CSLT_ALL` occupancy zone for averaging. `CSLT_Zone1–5` have HotelMotel entries only — there is no per-zone VHR measurement for CSLT. The combined zone produces the correct rate (0.5258); however, this rate is patched back to 2022 values in Stage 8 for calibration compatibility (see Gotcha #10).
- **ArcPy schema lock avoidance:** A custom `arcpy_spatial_join_attr()` function writes unique-UUID feature classes to scratchGDB to prevent file lock conflicts.
- **Bayview Campground exclusion:** Explicitly dropped from campground occupancy rate calculations (same as 2022).
- **Campground metric — Total_Sites (capacity):** The `campground` column in `OvernightVisitorZonalData` uses `Total_Sites` (total available sites), consistent with the 2022 run. `SitesSold` (occupied = Total_Sites × Occupancy_Rate) is computed internally but is not used for the capacity output.
- **Income tie-break:** If TAZ rounding produces zero units across all income classes for a TAZ with occupied units, one unit is assigned to the highest income class.
- **Phantom TAZs:** TAZs 1, 2, 3, 4, 5, 6, 7, 10, 20, 30, 40, 50, 60, 70 are added as all-zero rows to `SchoolEnrollment.csv` and other output files for model completeness. These zones have no development.

---

## Changes from 2022 RTP Base Year — Gotchas and Fixes

The following issues were identified and corrected during the 2026 Housing EIS base year run. This section documents the root causes and resolutions so future runs can avoid the same problems.

### 1. Campground fetch — missing `RECREATION_TYPE` filter

**Problem:** The 2026 script originally fetched campgrounds using `get_fs_data_spatial(CAMPGROUND_URL)` with no attribute filter. The `Recreation/MapServer/1` layer contains all recreation site types (trailheads, boat launches, day-use areas, etc.), not just campgrounds. This inflated `Total_Sites` in the campground layer.

**Fix:** Changed to `get_fs_data_spatial_query(CAMPGROUND_URL, query_params="RECREATION_TYPE='Campground'")`, matching the 2022 query.

### 2. Campground visits fetch — missing year filter

**Problem:** The campground visits table (`Transportation_Planning/MapServer/14`) contains records for multiple years. Fetching without a year filter (`get_fs_data(CAMPVISITS_URL)`) caused the left merge on `RECREATION_NAME` to produce duplicate rows (one per year per campground), multiplying `Total_Sites` sums by the number of years present in the table. This was the primary source of the apparent ~2,000 extra campground sites.

**Fix:** Changed to `get_fs_data_query(CAMPVISITS_URL, query_params=f"Year = {PARCEL_YEAR}")`, consistent with the 2022 query which used `"Year = 2022"`.

### 3. Campground metric — `SitesSold` vs `Total_Sites`

**Problem:** The original 2026 script aggregated `campground = SitesSold` (= Total_Sites × Occupancy_Rate) into `campground_taz.parquet` and passed it through to `OvernightVisitorZonalData_Summer.csv`. The 2022 run used `Total_Sites` (capacity) for the same column. Comparing the two outputs produced a misleading +598 difference that was actually an apples-to-oranges comparison of capacity vs occupied sites.

**Fix:** Changed the aggregation in Stage 6 to `campground = Total_Sites`, matching 2022 logic. `SitesSold` is still computed for informational purposes.

**Note:** After applying fixes 1 and 2, the campground total should be close to the 2022 value of 1,964. Any remaining difference reflects actual changes in the campground GIS layer. Investigate if the post-fix total diverges by more than a few sites.

### 4. Employment — placeholder zeros in 2022

**Context (not a bug):** The 2022 RTP run left all employment columns in `SocioEcon_Summer.csv` as zero (placeholder). The 2026 run populates employment from actual 2022 source data. This is intentional, not a regression.

| Sector | 2022 (placeholder) | 2026 |
|---|---|---|
| emp_retail | 0 | 3,711 |
| emp_srvc | 0 | 7,503 |
| emp_rec | 0 | 2,248 |
| emp_game | 0 | 2,564 |
| emp_other | 0 | 10,711 |
| **Total** | **0** | **26,737** |

### 5. New column — `rec_attractiveness` in OvernightVisitorZonalData

**Context:** `OvernightVisitorZonalData_Summer.csv` in 2026 includes a new `rec_attractiveness` column (basin total: 247,506) copied from the example input file. This column did not exist in the 2022 output. It is carried forward unchanged from the prior model run and is not recomputed.

### 6. TAU unit changes — HotelMotel and Casino

Differences in lodging unit counts between 2022 and 2026 reflect closed or reclassified facilities applied via `closed_tourist_parcels.csv` and `lookup_tau_type.csv`:

| TAZ | Type | 2022 | 2026 | Diff | Likely Cause |
|---|---|---|---|---|---|
| 141 | HotelMotel | 78 | 14 | −64 | Partial closure applied |
| 257 | HotelMotel | 86 | 110 | +24 | New units / reclassification |
| 259 | HotelMotel | 24 | 0 | −24 | Full closure applied |
| 292 | HotelMotel | 93 | 0 | −93 | Full closure applied |
| 306 | HotelMotel | 124 | 0 | −124 | Full closure applied |
| 395 | Casino | 105 | 0 | −105 | Reclassified or closed |
| 396 | Casino | 0 | 10 | +10 | New casino TAU |
| 397 | Casino | 186 | 0 | −186 | Reclassified or closed |

### 7. Phantom TAZs — SchoolEnrollment row count increase

TAZs 1, 2, 3, 4, 5, 6, 7, 10, 20, 30, 40, 50, 60, 70 were added to `SchoolEnrollment.csv` (and other output files) as all-zero rows via the "add phantom TAZs" step (commit `f8a5ad7`). These are low-use or undeveloped zones required by the model network. Their addition does not change any basin totals.

### 8. `percentHouseSeasonal` methodology

The 2022 run derived `percentHouseSeasonal` from `SecondaryResidence_Rate` at the TAZ level (mean of parcel-level rates). The 2026 run uses the same methodology. The basin sum decreased from 195.2 to 178.2 across the 282 shared TAZs, reflecting updated ACS vacancy data used to compute `SecondaryResidence_Rate`.

### 9. Occupancy rate zone lookup — web service schema mismatch ✓ Fixed

**Problem:** Stage 3 (Cell 29) originally fetched occupancy rates from the live service (`Transportation_Planning/MapServer/13`) and filtered by `MonthNum` / `Year` to reconstruct the summer average. The service has changed its schema since 2022 — it now uses fields `MonthNum`, `Year`, `Type`, `ZoneID`, `OccupancyRate` instead of the 2022 schema (`Zone_ID`, `RoomType`, `TRPA_OccRate`). Critically, the `MonthNum.notna()` filter only matched rows for a small subset of zones (~5 out of 19), so most parcels failed to find a zone rate and fell through to IDW. When IDW also found too few source points, parcels fell to the basin-wide defaults (`DEFAULT_TAU_OCCUPANCY = 0.5923`, `DEFAULT_VHR_OCCUPANCY = 0.4223`).

**Symptoms:** After re-run, `VisitorOccupancyRates_Summer.csv` showed:
- HotelMotel rate sums ~27.5 vs 24.5 expected (2022) — inflated by default fallback
- House/seasonal rate sums ~82.8 vs 78.4 expected — inflated by default fallback
- Only 3 unique non-zero hotelmotel rate values vs 18 in 2022
- Nearly all TAU parcels assigned `0.5923` exactly (= DEFAULT_TAU_OCCUPANCY)

**Root cause:** The `occupancy_rates.csv` in `data/raw_data/` already contains the correct pre-aggregated zone rates (19 zones, `Zone_ID` / `RoomType` / `TRPA_OccRate`), identical to the source used in the 2022 run. The 2026 script was ignoring this file and attempting to reconstruct the rates from the live service, which is now structured differently.

**Fix (Cell 29):** Changed Stage 3 to read `occupancy_rates.csv` directly from `DATA_DIR` using the 2022-compatible field names:
```python
df_occ_src = pd.read_csv(DATA_DIR / "occupancy_rates.csv")
df_tau = df_occ_src[df_occ_src["RoomType"].isin(TAU_TYPES)] \
    .groupby("Zone_ID")["TRPA_OccRate"].mean() ...
df_vhr = df_occ_src[df_occ_src["RoomType"] == "VHR"] \
    .groupby("Zone_ID")["TRPA_OccRate"].mean() ...
```
The `OCC_RATES_URL` service fetch in Cell 10 was also removed as it is no longer used.

**Resolved:** Re-ran Stages 3–8 from the `parcel_spatial_joins.parquet` checkpoint. Unique hotelmotel rate values increased from 3 back to 16, confirming zone lookup is working correctly. All output CSVs regenerated.

### 10. house/seasonal rates — CSLT VHR zone lookup bug (2022) and calibration patch

**Root cause (2022 bug):** In `occupancy_rates.csv`, `CSLT_Zone1–5` have HotelMotel entries only — there is no per-zone VHR row for any CSLT sub-zone. In the 2022 run, CSLT VHR parcels were spatially assigned to one of those five zones, failed the VHR rate lookup, fell through IDW (too few known-rate neighbors), and landed on the basin-wide default (`DEFAULT_VHR_OCCUPANCY = 0.4223`). As a result, 31 CSLT TAZs with VHR parcels showed `house = seasonal = 0.4223` in `VisitorOccupancyRates_Summer.csv` — not a measured rate, just the fallback.

**Confirmed by comparison:** Direct TAZ-by-TAZ diff of the two `VisitorOccupancyRates_Summer.csv` files shows exactly 31 CSLT TAZs with `house22 = 0.4223` → `house26 = 0.5258`, plus 14 additional CSLT TAZs that went from `0.0` (no VHR in 2022 registry) to `0.5258` (newly registered VHRs).

**Correct rate:** The `CSLT_ALL` zone in `occupancy_rates.csv` holds the combined VHR measurement across the entire CSLT jurisdiction (0.5258). The Stage 2e override assigns all CSLT VHR parcels to `CSLT_ALL` before the rate lookup, so the zone lookup always finds a match. This is the technically correct rate.

**Why the output is patched to 2022 values:** These 2026 Housing EIS inputs are a 2025 forecast run on top of a model calibrated to the 2022 base year. The calibration process links observed trip counts to the 2022 socioeconomic inputs — including the (incorrect) `house`/`seasonal` rates those CSLT TAZs received. Substituting the corrected rates without re-calibration would alter implied seasonal visitor demand in a way the model coefficients cannot absorb.

**Patch (Stage 8, cells 8c–8c-patch):** The corrected VHR rate computation is retained in the notebook but commented out. A patch cell immediately following loads `house` and `seasonal` from the 2022 `VisitorOccupancyRates_Summer.csv` and uses those values in the merge that produces the output CSV. Running the notebook end-to-end produces `VisitorOccupancyRates_Summer.csv` with 2022-matched house/seasonal rates.

**To revert:** Delete the patch markdown and code cells in section 8c-patch and uncomment the corrected VHR lookup in the cell above them. Do this after re-calibration against the corrected rates.

### 11. Census block-group rates — ACS service schema change and calibration patch

**Root cause:** The `Demographics/MapServer/28` ACS census service changed its schema from **wide format** (one row per block group, one column per ACS variable, e.g. `B25002_002E`, `B25002_003E`) to **long format** (one row per variable per block group, with `variable_code` and `value` columns). Simultaneously, the `year_sample` field used for year filtering was removed from the service.

The 2026 notebook's Stage 5 code issued a server-side filter `year_sample = 2022` — which the service silently ignored because the field no longer exists — and then used `pivot_table(aggfunc="first")` to reconstruct the wide format. Because the year filter was ignored, the pivot picked up records from multiple ACS survey vintages, producing rates that differ from the 2022 base year run.

**Affected variables:**
- `PrimaryResidence_Rate` (B25002_002E occupied / total units)
- `SecondaryResidence_Rate` (B25004_006E seasonal-vacant / B25002_003E total-vacant)
- `PersonsPerUnit` (B25010_001E household size × `HOUSEHOLD_SIZE_ADJUSTMENT`)
- `HighIncome_Rate`, `MediumIncome_Rate`, `LowIncome_Rate` (income band fractions from income census codes lookup)

**Why it matters for calibration:** The same reasoning as Gotcha #10 applies. These rates feed directly into `OccupiedUnits`, `SeasonalUnits`, `People`, and income-band counts in `SocioEcon_Summer.csv`. Changing them without re-calibrating the model alters implied population and demand in ways the 2022 coefficients cannot absorb.

**Fix — frozen CSV:** Block-group rates were extracted from `parcel_pickle4.pkl` — the 2022 run's final post-VHR-adjustment parcel file (61,259 parcels). This pickle contains the per-parcel rates after Stage 5 of the 2022 run, including the VHR unit subtraction applied to `SecondaryResidence_Rate`. The block-group-level rates were collapsed by `BLOCK_GROUP` (`pivot_table(aggfunc="first")` on already-unique per-parcel constant values) and saved to:

```
data/raw_data/census_block_group_rates_2022.csv
```

78 block groups, columns: `BLOCK_GROUP` (16-char TRPAID), `SecondaryResidence_Rate`, `PrimaryResidence_Rate`, `PersonsPerUnit`, `HighIncome_Rate`, `MediumIncome_Rate`, `LowIncome_Rate`. One null row and 2 rows with `SecondaryResidence_Rate = 0` (Beach Club block group manually zeroed in the 2022 run) are present and handled correctly.

**Patch — notebook changes (all cells support Run All):**

| Cell | ID | Change |
|---|---|---|
| 10 (Stage 1 fetch) | `b44fe2e7` | `df_census` live fetch commented out. The service returns mixed-year long-format data; Stage 5 no longer needs it. Original fetch lines preserved in comments. |
| 11 (diagnostic) | `bg-census-diag` | Entire cell commented out. It was used to diagnose the schema change (Gotchas #9 and #11); leaving it active adds two duplicate service fetches per Run All and prints misleading output. |
| 39 (Stage 5 header) | `15f7fabb` | Inputs line updated: `df_census` → `census_block_group_rates_2022.csv` |
| 41 (Stage 5a header) | `76c930ef` | Patch markdown cell (`stage5-patch-md`) inserted immediately after, explaining root cause and calibration rationale. |
| — (new) | `stage5-patch-code` | Patch code cell inserted after the markdown. Reads frozen CSV, constructs `df_occ_bg`, `df_hh`, `df_inc_pivot`. |
| 42 (5a code) | `99038599` | Commented out. Built `df_occ_bg` from live ACS service; replaced by patch cell above. |
| 44 (5b code) | `6f8d9017` | Commented out. Built `df_hh` from live ACS service; replaced by patch cell above. |
| 46 (5c code) | `7129634d` | Commented out. Built `df_inc_pivot` from live ACS service; replaced by patch cell above. |
| 48 (5d combine) | `418db59a` | VHR adjustment block commented out (`PATCH 5d` note). `SecondaryResidence_Rate` from frozen CSV is already VHR-adjusted; re-running would double-subtract. Parcel merge and unit count derivation unchanged. |

**Run result (confirmed good):** After applying all patches and running both notebooks:
- Stage 5 patch cell: 77 of 78 block groups matched (1 null row in CSV, expected)
- 172 parcel rate nulls (125 parcels with no BLOCK_GROUP + ~47 unmatched BGs — same as 2022 behavior)
- SocioEcon differences vs 2022 are small and entirely attributable to the +560 new residential units from `development_2022_2025.csv`, not census rate changes
- All Stage 9 seasonal QA checks passed: `percentHouseSeasonal` mean = 0.665 (ref 0.73, pass), seasonal occ rate mean = 0.464 (ref 0.46, pass)

**To revert (after re-calibration):**
1. In Cell 10, uncomment the `df_census` fetch lines and remove the `PATCHED OUT` comment block.
2. In Cell 11, uncomment all lines and remove the `PATCHED OUT` header comment.
3. Delete the `stage5-patch-md` and `stage5-patch-code` cells inserted after Cell 41.
4. In Cells 42, 44, 46, remove the `PATCHED OUT` header comments and uncomment the original code.
5. In Cell 48, remove the `PATCH 5d: VHR ADJUSTMENT SKIPPED` comment block and uncomment the VHR adjustment block.
6. Update Cell 39 Inputs line back to `df_census`.

### 12. Phantom TAZ college enrollment hardcode

**Problem:** TAZs 1 and 2 are phantom zones (no parcel polygons; added to satisfy model network requirements). The spatial school-to-TAZ join assigns zero enrollment to all phantom TAZs because no school point geometries land inside their boundaries. However, TAZ 1 and TAZ 2 have real college enrollment load that must be assigned for the model to correctly account for student-generated trips in those zones.

**Fix (Cell 59, id `0385a172`):** After the phantom TAZ row concat block, a hardcode patch overrides `college_enrollment` for these two TAZs:

| TAZ | college_enrollment |
|---|---|
| 1 | 171 |
| 2 | 49 |
| All other phantom TAZs | 0 (unchanged) |

All other enrollment types (elementary, middle, high school) for these TAZs remain zero. The values were sourced from reference enrollment data and confirmed against the 2022 run.

**Run result:** College enrollment basin total increased from 2,798 → 3,018 (+220). Total school enrollment basin total: 9,309 (was 9,089 before patch). Shared-TAZ enrollment for all other types remains identical to 2022.

**To revert:** Remove the `_college_overrides` loop block from Cell 59 (marked `PATCH: Phantom TAZ college enrollment hardcodes`).

---

## Dependencies

| Dependency | Required For |
|---|---|
| ArcGIS Pro + arcpy | Stages 2e, 4, 6, 7 (spatial joins, IDW) |
| ArcGIS Spatial Analyst Extension | Stage 4 (IDW interpolation) |
| arcgis Python API | Web service data fetching |
| pandas, numpy | All tabular processing |
| matplotlib | QA notebook visualizations |
| TRPA network access | All web service calls |
| Local lookup CSV files | Stages 2a–2d, 5c |

---

## Updating for a New Base Year

To apply this pipeline to a future base year, update the following configuration variables at the top of the notebook:

- `PARCEL_YEAR`
- `SCHOOL_YEAR`
- `CENSUS_YEAR`
- `OCCUPANCY_TIMEFRAMES` (list of date strings)
- Household size adjustment factor (recalculate from new ACS data)
- Default occupancy rates (recalculate from new zone data)
- Lookup files in `Lookup_Lists/` (update development changes, closed parcels as needed)

**Checklist for campground data integrity (lessons from 2026 run):**
1. Confirm `RECREATION_TYPE = 'Campground'` filter is applied to the campground spatial fetch.
2. Confirm campground visits are filtered to the correct year (`Year = {PARCEL_YEAR}`).
3. After running Stage 6, verify `Total_Sites` basin sum is consistent with the prior run. Any difference > ~50 sites warrants investigation in the GIS layer before proceeding.

**Checklist for occupancy rate data integrity (lessons from 2026 run):**
1. Stage 3 reads rates from `data/raw_data/occupancy_rates.csv`. For a new base year, update this CSV with the new season's averaged rates before running. Do not rely on the live `OCC_RATES_URL` service — its schema has changed and it returns incomplete zone coverage.
2. After running Stage 3 (`parcel_occupancy_rates.parquet`), check that the number of unique hotelmotel rate values is > 10. If most TAZs show exactly `0.5923`, the zone lookup has failed and fallen back to defaults — stop and investigate before proceeding. (2026 baseline: 16 unique values.)
3. After Stage 8, compare `VisitorOccupancyRates_Summer.csv` hotelmotel sum against the prior run. A sum > 26 indicates the fallback is still active. (2026 confirmed value: 22.4.)
