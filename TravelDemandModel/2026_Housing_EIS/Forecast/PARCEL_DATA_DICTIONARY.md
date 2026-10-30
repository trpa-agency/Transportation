# Scenario Parcel Layer — Data Dictionary

**Layer:** `data/processed_data/run_<timestamp>/parcels.gdb/<scenario_name>_parcels`
**Produced by:** `scripts/run_scenarios.py` (`export_scenario_feature_classes`)
**Geometry:** `data/processed_data/base_data/parcel_geometry.gdb/parcel_geometry`, joined by `APN`
**Coordinate system:** NAD 1983 UTM Zone 10N (EPSG 26910)

Each scenario run writes one polygon feature class per scenario, with one record per parcel (61,276 records). The same attributes are in `all_scenarios_parcels.parquet` in the run folder, where every scenario is stacked and identified by `SCENARIO`.

Counts and examples below come from `run_2026-10-16_140239` (Alternatives 1–3, configs dated 04/28/2026).

---

## Contents

1. [How the layer is built](#how-the-layer-is-built)
2. [Field reference](#field-reference)
   - [Parcel identity and location](#parcel-identity-and-location)
   - [Existing development (base year)](#existing-development-base-year)
   - [Development capacity](#development-capacity)
   - [Forecast results](#forecast-results)
3. [FORECAST_REASON — allocation conditions](#forecast_reason--allocation-conditions)
4. [Occupancy and income by reason](#occupancy-and-income-by-reason)
5. [Data notes and known issues](#data-notes-and-known-issues)

---

## How the layer is built

| Step | Script | What it does |
|---|---|---|
| 1 | `scripts/parcel_attributing.ipynb` | Starts from the base-year parcels (`Base/data/processed_data/parcel_spatial_joins.parquet`). Adds zoning, IPES, retirement, development-capacity fields and known projects (`Assigned`). Shuffles the parcels into a fixed random order and writes `base_parcel_data.parquet`. |
| 2 | `scripts/run_scenarios.py` | For each scenario config, allocates each unit pool's `Future_Units` to eligible parcels (see [FORECAST_REASON](#forecast_reason--allocation-conditions)). Then assigns development year, occupancy rate and income shares. |
| 3 | `scripts/run_scenarios.py` | Joins the parcel records to the static geometry snapshot by APN and writes the feature classes. |

**Allocation order.** The parcels are in a fixed random order; the order used is recorded in `scripts/Parcel_Sort_Order_20260410160756.csv`. Each pool walks that list and takes every eligible parcel until its target is met. The last parcel can receive a partial amount. Once a parcel has a `FORECAST_REASON`, later pools can't use it. Pools run in this sequence:

1. **Known projects** (`Assigned`), set in step 1.
2. **Jurisdiction Bonus Unit pools**: CSLT, DG, PL, WA.
3. **Jurisdiction General pools**: CSLT, EL, PL, DG, WA.
4. **TRPA pools**: Bonus, General, ADU, then the Alternative 2 pools (Affordable, Moderate, Achievable, Affordable by Design, JADU).
5. **Remainders.** If an MF or SF pool can't place all its units, some pools send the shortfall to their Infill condition. The pools covered are listed under [Remainder pass](#remainder-pass).
6. **ADU top-up.** Any units still unplaced are assigned as `TRPA ADU Units`. The target is the sum of all pool `Future_Units` plus 874 known-project units.

**Unit-type split.** Each pool's `Future_Units` is split into MF, SF and Infill shares using the config's `zone_proportions`. The default is MF 35%, SF 50%, Infill 15%, and rounding error goes to SF.

---

## Field reference

Types are the ArcGIS field types in the feature class. **Nulls** is the number of null records out of 61,276 in each scenario.

### Parcel identity and location

| Field | Type | Description | Values / notes |
|---|---|---|---|
| `APN` | Text | Assessor's Parcel Number. This is the join key to parcel geometry. | Seven APNs appear more than once, 44 extra records in total. See [Data notes](#data-notes-and-known-issues). |
| `APO_ADDRESS` | Text | Parcel situs address. | From `sde.Parcel_History_Attributed` (YEAR = 2022). |
| `YEAR` | Long | Year of the parcel-history record the descriptive attributes came from. | Always 2022. |
| `JURISDICTION` | Text | Local jurisdiction. | `CSLT` City of South Lake Tahoe, `EL` El Dorado Co., `PL` Placer Co., `WA` Washoe Co., `DG` Douglas Co., `CC` Carson City |
| `COUNTY` | Text | County. | Same codes as `JURISDICTION`; CSLT parcels are `EL`. |
| `OWNERSHIP_TYPE` | Text | Owner category. | `Private`, `State`, `Federal`, `Local`, blank. Only `Private` parcels can receive pool allocations. |
| `COUNTY_LANDUSE_DESCRIPTION` | Text | Assessor land use description. | |
| `EXISTING_LANDUSE` | Text | TRPA existing land use category. | e.g. `Single Family Residential`, `Vacant`, `Condominium`, `Condominium Common Area`, `Multi-Family Residential`, `Commercial`, `Open Space` |
| `REGIONAL_LANDUSE` | Text | Regional land use. | **Not populated** — blank in every record. |
| `YEAR_BUILT` | Text | Year the primary structure was built. | `0` = none or unknown. |
| `PLAN_ID` | Text | Area plan or plan area code. | e.g. `WCTAP` |
| `PLAN_NAME` | Text | Area plan or plan area name. | e.g. `WASHOE COUNTY TAHOE AREA PLAN` |
| `ZONING_ID` | Text | Zoning district ID. | Joins to `sde.PermissibleUses`. |
| `ZONING_DESCRIPTION` | Text | Zoning district name. | |
| `TOWN_CENTER` | Text | Town center the parcel is in. | Blank if the parcel is outside a town center. |
| `LOCATION_TO_TOWNCENTER` | Text | Proximity to a town center. | `Within Town Center`, `Within Quarter Mile of Town Center`, `Further than Quarter Mile from Town Center`, blank |
| `TAZ` | Text | Traffic analysis zone. Forecast units roll up to the model by this field. | 127 nulls |
| `PARCEL_ACRES` | Double | Parcel area in acres. | 1,621 nulls. Parcels with a null are never eligible for pool allocation (see [notes](#data-notes-and-known-issues)). |
| `PARCEL_SQFT` | Double | Parcel area in square feet. | 1,621 nulls |
| `WITHIN_BONUSUNIT_BNDY` | Text | Whether the parcel is inside the Residential Bonus Unit boundary. | `Yes` / `No` |
| `WITHIN_TRPA_BNDY` | Long | Whether the parcel is inside the TRPA boundary. | `1` / `0`. All pool allocations require `1`. |
| `VHR` | Text | Whether the parcel has an existing vacation home rental. | `Yes` / `No` |

### Existing development (base year)

| Field | Type | Description | Values / notes |
|---|---|---|---|
| `Residential_Units` | Long | Existing residential units. | Total 49,462 across all records |
| `TouristAccommodation_Units` | Long | Existing tourist accommodation units (TAUs). | Total 11,243 |
| `CommercialFloorArea_SqFt` | Double | Existing commercial floor area, in square feet. | Total 6,474,964 |

### Development capacity

These fields are set in `parcel_attributing.ipynb`. Pool eligibility is decided by these fields.

| Field | Type | Description | Values / notes |
|---|---|---|---|
| `IPES_SCORE` | Double | Individual Parcel Evaluation System score, from LT Info. | 50,202 nulls (no score in LT Info). The vacant-buildable test requires a score above 0, or above 726 in Placer. |
| `IPES_SCORE_TYPE` | Text | IPES score status. | `Official`, `Information Only`, `Draft`, `Inactive`, `Transferred`, null |
| `RETIRED` | Text | Whether the parcel is retired from development (LT Info `RetiredFromDevelopment`). | `Yes` / `No`. Only `No` counts as vacant buildable. |
| `HOUSING_ZONING` | Text | Residential uses allowed by the parcel's zoning, from `PermissibleUses`. | `SF/MF` (both), `SF_only`, `MF_only`, `NA` (neither) |
| `COMMERCIAL_ALLOWED` | Text | Whether commercial use is allowed in the zone. | `Yes` / `No` (informational) |
| `TOURIST_ALLOWED` | Text | Whether tourist accommodation is allowed in the zone. | `Yes` / `No` (informational) |
| `ADU_ALLOWED` | Text | Whether an accessory dwelling unit is allowed. | `Yes` if `HOUSING_ZONING` is `SF/MF` or `SF_only`, **and either** the county is EL, PL or WA, **or** the county is DG or CC and `PARCEL_ACRES` ≥ 1 |
| `DENSITY` | Double | Maximum multi-family density allowed by zoning, in units per acre. | Null where multi-family use isn't allowed |
| `MAX_RESIDENTIAL_UNITS` | Double | Theoretical maximum units: `PARCEL_ACRES × DENSITY`. | Null where `DENSITY` is null |
| `MAX_UNITS` | Long | Realistic maximum units: `MAX_RESIDENTIAL_UNITS × 0.6`, truncated to a whole number. Null becomes 0. **`SF_only` parcels are set to 1.** | Units placed on a parcel by MF, SF and ADU pools. |
| `POTENTIAL_UNITS` | Long | Unused capacity: `MAX_UNITS − Residential_Units`, floored at 0. | Units placed on a parcel by Infill pools. |
| `TOP_TEN_POTENTIAL_UNITS` | Text | `Yes` if `POTENTIAL_UNITS` is at or above the 90th percentile. | The threshold is 1, so 27% of parcels are `Yes`. **No active allocation condition uses this field.** |

### Forecast results

| Field | Type | Description | Values / notes |
|---|---|---|---|
| `SCENARIO` | Text | Scenario name from the config (`scenario_name`). | e.g. `Alternative_2_04282026` |
| `FORECAST_REASON` | Text | The pool and unit type that placed new units on the parcel. | See [FORECAST_REASON](#forecast_reason--allocation-conditions). Null = no new residential units. |
| `FORECASTED_RESIDENTIAL_UNITS` | Double | New residential units placed on the parcel. | Treat null as 0. Some parcels that were considered but got nothing hold 0. |
| `Development_Year` | Double | Model year by which the units are built. | `2035` or `2050`; null if no units. All `Assigned` units are 2035. 2035 is capped at 33% of the config's total pool `Future_Units`, and `Assigned` units count toward that cap. The rest of the 2035 cap is filled by parcels in allocation order; everything else is 2050. |
| `FORECASTED_RES_OCCUPANCY_RATE` | Double | Share of new units that are occupied full-time; the rest are second homes or vacation units. | Set by `FORECAST_REASON`; see [Occupancy and income](#occupancy-and-income-by-reason) |
| `FORECASTED_OCCUPIED_UNITS` | Double | `FORECASTED_RESIDENTIAL_UNITS × FORECASTED_RES_OCCUPANCY_RATE` | Feeds TAZ occupied units and population. |
| `FORECASTED_RES_INCOME_LOW` | Double | Share of occupied units in low-income households. | 0–1; the three shares sum to 1 on parcels with units. |
| `FORECASTED_RES_INCOME_MEDIUM` | Double | Share of occupied units in medium-income households. | 0–1 |
| `FORECASTED_RES_INCOME_HIGH` | Double | Share of occupied units in high-income households. | 0–1 |
| `FORECASTED_RES_INCOME_LOW_UNITS` | Double | `FORECASTED_RES_INCOME_LOW × FORECASTED_OCCUPIED_UNITS` | |
| `FORECASTED_RES_INCOME_MEDIUM_UNITS` | Double | `FORECASTED_RES_INCOME_MEDIUM × FORECASTED_OCCUPIED_UNITS` | |
| `FORECASTED_RES_INCOME_HIGH_UNITS` | Double | `FORECASTED_RES_INCOME_HIGH × FORECASTED_OCCUPIED_UNITS` | |
| `FORECAST_RES_INCOME_CATEGORY` | Text | Household income category for a known project, from `data/inputs/res_assigned_lookup.csv`. | `Low` (lookup value `Affordable`), `Medium` (`Achievable`), `High`; null elsewhere. |
| `FORECASTED_COMMERCIAL_SQFT` | Long | New commercial floor area. | **Always 0.** Placeholder; commercial growth isn't allocated to parcels in this pipeline. |
| `FORECASTED_TOURIST_UNITS` | Long | Net change in TAUs. | **Always 0.** Placeholder; forecast-year TAUs come in at the TAZ level from the 2025 RTP inputs. |


Feature-class system fields: `OBJECTID`, `Shape`, `Shape_Length`, `Shape_Area`.

---

## FORECAST_REASON — allocation conditions

### Shared criteria

Every reason except `Assigned` combines the base requirement below with some of the other criteria.

| Code | Criterion | Field test |
|---|---|---|
| **BASE** | Inside TRPA, private and not yet allocated | `WITHIN_TRPA_BNDY = 1` AND `OWNERSHIP_TYPE = 'Private'` AND `FORECAST_REASON` is null |
| **SIZE** | At least 0.15 acre and not a condo | `PARCEL_ACRES >= 0.15` AND `EXISTING_LANDUSE` is not `Condominium` or `Condominium Common Area` (common areas excluded starting 10/30/2026; see [note 3](#data-notes-and-known-issues)) |
| **VAC** | Vacant buildable | `EXISTING_LANDUSE = 'Vacant'` AND `RETIRED = 'No'` AND `IPES_SCORE > 0` |
| **VAC‑PL** | Vacant buildable, Placer | Same as VAC but `IPES_SCORE > 726` |
| **MFZ** | Multi-family zoning | `HOUSING_ZONING` in (`SF/MF`, `MF_only`) |
| **SFZ** | Single-family-only zoning | `HOUSING_ZONING = 'SF_only'` |
| **BU** | Bonus Unit boundary | `WITHIN_BONUSUNIT_BNDY = 'Yes'` |
| **TC** | Inside a town center | `TOWN_CENTER` is not blank (the quarter-mile buffer doesn't count) |
| **ADU** | Existing home that allows an ADU | `ADU_ALLOWED = 'Yes'` AND `Residential_Units > 0` |

### Units placed per parcel

| Unit type (reason suffix) | Units given to each parcel | Vacant required? |
|---|---|---|
| `MF`, `SF`, `ADU Units`, `JADU Units` | `MAX_UNITS` (always 1 on `SF_only` parcels) | MF / SF: yes. ADU / JADU: no, it needs an existing home. |
| `Infill` | `POTENTIAL_UNITS`, the unused capacity on parcels that are already built or vacant | No |

The last parcel in each pool gets only what is left of the target.

### Known projects

| FORECAST_REASON | Condition | Units |
|---|---|---|
| `Assigned` | The APN is in `scripts/Lookup_Lists/known_projects.csv`, which lists permitted projects, allocations, bonus unit reservations and pending ADUs. CFA and TAU rights are excluded. Set before any pool runs; no other criteria apply. | Sum of `Quantity` for the APN; 874 units on 229 parcels. Identical in every scenario. |

### Jurisdiction pools

Labels follow the pattern `<JUR> <Bonus|General> Units <MF|SF|Infill>`. Every one also requires `JURISDICTION = <JUR>`, BASE and SIZE.

| FORECAST_REASON | Vacant | Zoning | Other | Notes |
|---|---|---|---|---|
| `<JUR> General Units MF` | VAC (Placer: VAC‑PL) | MFZ | — | CSLT, DG, EL, PL, WA |
| `<JUR> General Units SF` | VAC (Placer: VAC‑PL) | SFZ | — | |
| `<JUR> General Units Infill` | — | MFZ | — | |
| `CSLT Bonus Units MF` / `SF` | VAC | **MFZ for both** | BU | The SF condition uses multi-family zoning, so MF and SF test the same parcels. |
| `CSLT Bonus Units Infill` | — | MFZ | BU | |
| `DG Bonus Units MF` / `SF` | VAC | **MFZ for both** | BU | Same as CSLT. |
| `DG Bonus Units Infill` | — | MFZ | BU | |
| `PL Bonus Units MF` | VAC‑PL | **SFZ** | BU |  |
| `PL Bonus Units SF` | VAC‑PL | **MFZ** | BU | |
| `PL Bonus Units Infill` | — | MFZ | BU | |
| `WA Bonus Units MF` / `SF` | VAC | **SFZ for both** | BU | |
| `WA Bonus Units Infill` | — | MFZ | BU | |

### TRPA pools

TRPA pools have no jurisdiction filter and draw from the whole region. All of them require BASE and SIZE. The pools below the ADU rows exist only in Alternative 2; they are 0 in the other configs, so they don't run.

| FORECAST_REASON prefix | Config `Unit_Pool` | MF | SF | Infill | Other |
|---|---|---|---|---|---|
| `TRPA Bonus Units` | Bonus Unit | VAC + MFZ | VAC + SFZ | MFZ | BU |
| `TRPA General Units` | General | VAC + MFZ | VAC + SFZ | MFZ | — |
| `TRPA ADU Units` | ADU (+ top-up) | — | — | — | ADU. Placed as `MAX_UNITS` (1 on `SF_only`; up to 2 observed on `SF/MF`). Also gets the [ADU top-up](#how-the-layer-is-built). |
| `TRPA JADU Units` | JADU | — | — | — | ADU (same condition as `TRPA ADU Units`) |
| `TRPA Affordable Units` | Affordable | VAC + MFZ | VAC + SFZ | MFZ | TC |
| `TRPA Moderate Units` | Moderate | VAC + MFZ | VAC + SFZ | MFZ | BU |
| `TRPA Achievable Bonus Units` | Achievable Bonus | VAC + MFZ | VAC + SFZ | MFZ | BU |
| `TRPA Achievable General Units` | Achievable General | VAC + MFZ | VAC + SFZ | MFZ | — |
| `TRPA Achievable TC Units` | Achievable TC | VAC + MFZ | VAC + SFZ | MFZ | TC |
| `TRPA Affordable BD Units` | Affordable by Design | VAC + MFZ | VAC + SFZ | MFZ | — ("BD" = By Design) |
| `TRPA Affordable by Design TC Units` | Affordable by Design TC | VAC + MFZ | VAC + SFZ | MFZ | TC |

### Remainder pass

After all pools run, the MF and SF pools in this list send any units they couldn't place to the Infill condition shown. The reason label written to the parcel is the Infill label.

| Shortfall from | Re-allocated as |
|---|---|
| WA Bonus SF | `WA Bonus Units Infill` |
| EL / PL / WA / DG General MF; WA General SF | `<JUR> General Units Infill` (the DG remainder places `MAX_UNITS`, not `POTENTIAL_UNITS`) |
| TRPA General MF | `TRPA General Units Infill` |
| TRPA Affordable, Moderate, Achievable Bonus, Achievable General, Affordable BD, Affordable by Design TC, Achievable TC — MF and SF | the matching TRPA `… Infill` reason |

Shortfalls from pools not in this list, such as CSLT or DG Bonus, end up in the ADU top-up.

For example, the MF and SF passes for Alternative 2's 456 Affordable units placed nothing on vacant town-center parcels. All of them end up on 33 town-center infill parcels as `TRPA Affordable Units Infill`.

---

## Occupancy and income by reason

`FORECASTED_RES_OCCUPANCY_RATE` and the income shares come from the scenario config's `occupancy_rates` and `income_proportions`.

