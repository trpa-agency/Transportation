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

| Dataset | Service Layer | Notes |
|---|---|---|
| Parcels | `Existing_Development/MapServer/2` | Queried for 2022; APN, units, commercial floor area |
| VHR Registry | `VHR/MapServer/0` | APNs registered as vacation home rentals |
| TAZ Boundaries | `Transportation_Planning/MapServer/6` | Polygon layer |
| Block Groups | `Demographics/MapServer/27` | Filtered to 2020 vintage, block-group level |
| Census Demographics | `Demographics/MapServer/28` | Occupancy, household size, income (ACS 5-year) |
| Occupancy Zones | `Transportation_Planning/MapServer/15` | Zone polygons for rate averaging |
| Occupancy Rates | `Transportation_Planning/MapServer/13` | Monthly rates by zone and property type |
| Campgrounds | `Recreation/MapServer/1` | Location and site counts |
| Campground Visits | `Transportation_Planning/MapServer/14` | Occupancy rates by campground |
| Schools (spatial) | `Transportation_Planning/MapServer/16` | Location and enrollment by name |
| Schools (table) | `Transportation_Planning/MapServer/17` | Enrollment by school year |

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

Campground locations are spatially joined to TAZs (ArcPy). Occupancy rates are merged onto campground records (Bayview Campground excluded). Occupied site counts are computed as:

`SitesSold = Total_Sites × Occupancy_Rate`

Results are aggregated to TAZ level.

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
| `OvernightVisitorZonalData_Summer_{RUN_DATE}.csv` | TAU rooms by type (HotelMotel, Casino, Resort), campground sites, seasonal percentage |
| `VisitorOccupancyRates_Summer_{RUN_DATE}.csv` | Weighted TAU occupancy rate and mean VHR occupancy rate per TAZ |
| `SocioEcon_Summer_{RUN_DATE}.csv` | Residential units, occupied units, occupancy rate, seasonal rate, household size, income distribution proportions, persons |
| `Employment_{RUN_DATE}.csv` | Employment by sector, carried forward from prior 2022 base year run |
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

## Basin-Wide Summary Metrics (Base Year 2022)

| Metric | Value |
|---|---|
| Default TAU occupancy rate | 59.23% |
| Default VHR occupancy rate | 42.23% |
| Seasonal rate (fixed) | 39.00% |
| Household size adjustment factor | 1.021 |
| ACS total persons (basin) | 53,953 |
| Model-calculated persons (pre-adjustment) | 52,788.25 |
| Placeholder employment total | 26,777 |

---

## Key Design Decisions

- **Parquet checkpoints** avoid pickle version lock-in and enable stage-level resumption.
- **Spatial reference** for all ArcPy operations: NAD 1983 UTM Zone 10N.
- **Block group filtering** to 2020 vintage and 16-character TRPAID ensures correct census joins.
- **VHR double-counting prevention:** VHR units are subtracted from seasonal estimates before the seasonal rate is applied.
- **CSLT VHR override:** All CSLT VHR parcels use the combined `CSLT_ALL` occupancy zone for averaging.
- **ArcPy schema lock avoidance:** A custom `arcpy_spatial_join_attr()` function writes unique-UUID feature classes to scratchGDB to prevent file lock conflicts.
- **Bayview Campground exclusion:** Explicitly dropped from campground occupancy rate calculations.
- **Income tie-break:** If TAZ rounding produces zero units across all income classes for a TAZ with occupied units, one unit is assigned to the highest income class.

---

## Dependencies

| Dependency | Required For |
|---|---|
| ArcGIS Pro + arcpy | Stages 2e, 4, 6, 7 (spatial joins, IDW) |
| ArcGIS Spatial Analyst Extension | Stage 4 (IDW interpolation) |
| arcgis Python API | Web service data fetching |
| pandas, numpy | All tabular processing |
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
