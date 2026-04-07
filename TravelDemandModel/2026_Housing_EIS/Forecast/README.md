# 2026 Housing EIS — Development Forecast

**Project:** 2026 Housing Element Environmental Impact Study (EIS)
**Purpose:** Parcel-level development forecasting for 2035 and 2050 model years to support the Tahoe Regional Transportation Plan (RTP) and Housing EIS alternatives analysis.

---

## Overview

This folder contains the full forecasting workflow for the Lake Tahoe Basin Housing EIS. The workflow is split into two phases: **shared data engineering** (parcel preparation and base unit pool assembly) and **scenario-specific forecasting** (per-alternative unit allocation, TAZ summaries, and travel demand model inputs). Four housing policy alternatives are evaluated, each with its own unit distribution assumptions and known-projects list.

---

## Folder Structure

```
Forecast/
├── README.md                          # This file
├── scripts/                           # Shared Phase 1 scripts (run once, common to all alternatives)
│   ├── parcel_engineering.ipynb       # Phase 1A: spatial joins, parcel classification, unit pool assembly
│   ├── scenario_forecast_template.ipynb  # Phase 1B: reference template for scenario notebooks
│   ├── Base_Forecast.ipynb            # Original combined notebook (source of Phase 1A/1B)
│   ├── utils.py                       # Shared helper functions
│   └── Lookup_Lists/                  # Shared input CSVs (zoned units, assigned units, CTC lands, etc.)
├── data/                              # Shared processed data outputs
│   ├── base_parcel_data.pkl           # Engineered parcel layer (output of Phase 1A)
│   ├── unit_pool_assigned.csv         # Adjusted unit pools after known-project subtraction
│   ├── taz_summary_2035.csv/.pickle   # TAZ-level summary — 2035 model year
│   ├── taz_summary_2050.csv/.pickle   # TAZ-level summary — 2050 model year
│   ├── Parcels_Forecast.csv           # Parcel-level forecast (tabular)
│   └── TAZ_Units.csv                  # Existing and forecasted residential units by TAZ
├── Alternative_1/                     # Housing Alternative 1 scenario
│   ├── Alternative_1_Forecast.ipynb
│   ├── utils.py
│   ├── inputs/                        # Alternative-specific zoned units and scenario distribution CSVs
│   └── Changes from RTP Model Run.md
├── Alternative_2/                     # Housing Alternative 2 scenario
│   ├── Alternative_2_Forecast.ipynb
│   └── inputs/
├── Alternative_3/                     # Housing Alternative 3 scenario
│   ├── Alternative_3_Forecast.ipynb
│   └── inputs/
└── Alternative_4/                     # Housing Alternative 4 scenario
    ├── Alternative_4_Forecast.ipynb
    └── inputs/
```

---

## Process Flow

### Phase 1 — Shared Data Engineering (`scripts/`)

Run once. Outputs are shared across all alternatives.

```mermaid
flowchart TD
    A([Start]) --> B

    subgraph SETUP["1. Setup"]
        B[Import packages\npandas · arcpy · sqlalchemy · numpy]
        B --> C[Configure workspace\nSDE connections · local paths]
    end

    subgraph INGEST["2. Data Ingestion"]
        C --> D[Load base-year parcel data\nparcel_pickle4.pkl]
        C --> E[Load parcel development layer\nSDE.Parcel_History_Attributed]
        C --> F[Load spatial layers\nTAZ · Block Group · Bonus Unit Boundary]
    end

    subgraph SPATIAL["3. Parcel Engineering — parcel_engineering.ipynb"]
        D & E & F --> G[Spatial join: parcels → TAZ]
        G --> H[Spatial join: parcels → Block Group]
        H --> I[Spatial join: parcels → Bonus Unit Boundary]
        I --> J[Assign categorical fields\nzoning · land use · eligibility flags]
        J --> K[Assign Known Projects\nfrom forecast_residential_assigned_units.csv]
        K --> L[Assign CTC Asset Lands\nfull buildout for 17 parcels]
        L --> M[Compute adjusted unit pools\nby jurisdiction × pool type]
        M --> N[Export outputs\nbase_parcel_data.pkl · unit_pool_assigned.csv]
    end

    N --> O([Phase 1 Complete])
```

### Phase 2 — Scenario Forecasting (per Alternative)

Run independently for each alternative using its own `inputs/` folder.

```mermaid
flowchart TD
    O([Phase 1 Outputs]) --> P

    subgraph SCENSETUP["1. Scenario Setup"]
        P[Load base_parcel_data.pkl\nLoad unit_pool_assigned.csv]
        P --> Q[Load alternative-specific inputs\nzoned units · known projects · scenario distribution]
    end

    subgraph POOLSETUP["2. Pool Proportions"]
        Q --> R[Set MF · SF · Infill proportions\nper zone via zone_proportions dict]
    end

    subgraph FCAST["3. Residential Forecasting"]
        R --> S[Define parcel conditions\nget_parcel_conditions from utils]
        S --> T[Forecast Jurisdiction Pools\nCSLT · DG · PL · WA · EL]
        S --> U[Forecast TRPA Pools\nBonus Unit · General · ADU]
        T & U --> V[Assign remainder units\nas infill]
        V --> W[Assign Development Year\n2035 · 2050]
        W --> X[Assign Occupancy Rate\nper unit type]
        X --> Y[Assign HH Income Category\nLow · Medium · High]
    end

    subgraph OTHERFCAST["4. Other Forecasts"]
        Y --> Z[Tourist Accommodation\nfrom forecast_tourist_assigned_units.csv]
        Z --> AA[Commercial Floor Area\nfrom forecast_commercial_assigned_units.csv]
    end

    subgraph SUMMARY["5. TAZ Summary & QA"]
        AA --> AB[Aggregate to TAZ level\noccupied units · income tiers]
        AB --> AC[Calculate forecasted population\nunits × persons per occupied unit]
        AC --> AD[QA checks\nby jurisdiction · reason · zone type · town center]
    end

    subgraph EXPORT["6. Exports"]
        AD --> AE[Parcels_Forecast.csv\nParcel_Forecast GDB Feature Class]
        AD --> AF[taz_summary_2035.csv/pickle\ntaz_summary_2050.csv/pickle]
        AD --> AG[TAZ_Units.csv]
    end
```

---

## Notebooks

| Notebook | Phase | Purpose |
|---|---|---|
| `scripts/parcel_engineering.ipynb` | 1A | Spatial joins, parcel classification, unit pool assembly; exports `base_parcel_data.pkl` and `unit_pool_assigned.csv` |
| `scripts/scenario_forecast_template.ipynb` | 1B | Reference template for building alternative notebooks; loads Phase 1A outputs |
| `scripts/Base_Forecast.ipynb` | — | Original combined notebook (source for the Phase 1A/1B split); kept for reference |
| `Alternative_1/Alternative_1_Forecast.ipynb` | 2 | Scenario forecast for Alternative 1 |
| `Alternative_2/Alternative_2_Forecast.ipynb` | 2 | Scenario forecast for Alternative 2 |
| `Alternative_3/Alternative_3_Forecast.ipynb` | 2 | Scenario forecast for Alternative 3 |
| `Alternative_4/Alternative_4_Forecast.ipynb` | 2 | Scenario forecast for Alternative 4 |

---

## Inputs

### Shared Inputs (`scripts/Lookup_Lists/`)

| Input | Type | Description |
|---|---|---|
| `forecast_residential_assigned_units.csv` | CSV | Known residential allocations 2023–2025 |
| `forecast_residential_zoned_units.csv` | CSV | Jurisdiction-level zoned residential unit pools |
| `forecast_tourist_assigned_units.csv` | CSV | Known tourist accommodation changes |
| `forecast_tourist_zoned_units.csv` | CSV | Jurisdiction-level zoned tourist unit pools |
| `forecast_commercial_assigned_units.csv` | CSV | Known commercial floor area changes |
| `forecast_commercial_zoned_units.csv` | CSV | Jurisdiction-level zoned commercial floor area |
| `CTC_AssetLands_Lookup.csv` | CSV | 17 CTC asset land parcels for full buildout |
| `known_projects.csv` | CSV | Master list of known development projects |
| `SocioEcon_Summer.csv` | CSV | Base-year TAZ socioeconomic data (persons per unit) |

### Alternative-Specific Inputs (`Alternative_N/inputs/`)

| Input | Type | Description |
|---|---|---|
| `forecast_residential_zoned_units.csv` | CSV | Scenario-adjusted zoned unit pool overrides |
| `known_projects.csv` | CSV | Alternative-specific known projects list |
| `scenarioN_instructions.csv` | CSV | Narrative description of scenario assumptions |
| `scenarioN_unit_distribution.csv` | CSV | Per-zone MF / SF / Infill proportion targets |

### Spatial / Database Inputs

| Input | Type | Description |
|---|---|---|
| `parcel_pickle4.pkl` | Pickle | Base-year parcel data from the 2022 Travel Demand Model |
| `SDE.Parcel_History_Attributed` | SDE Feature Class | Parcel development records with attributed history |
| TAZ polygons | SDE Feature Class | Traffic Analysis Zones |
| Block Group polygons | SDE Feature Class | Census block groups |
| Bonus Unit Boundary | SDE Feature Class | TRPA bonus unit eligibility boundary |

---

## Outputs

### Shared (`data/`)

| Output | Type | Description |
|---|---|---|
| `base_parcel_data.pkl` | Pickle | Engineered parcel layer with spatial joins and classification (Phase 1A output) |
| `unit_pool_assigned.csv` | CSV | Unit pools after subtracting known projects and CTC lands |
| `Parcels_Forecast.csv` | CSV | Parcel-level forecast with all assigned attributes |
| `taz_summary_2035.pkl/.csv` | Pickle / CSV | TAZ-level summary for 2035 model year |
| `taz_summary_2050.pkl/.csv` | Pickle / CSV | TAZ-level summary for 2050 model year |
| `TAZ_Units.csv` | CSV | Existing and forecasted residential units by TAZ |

### Per Alternative

| Output | Type | Description |
|---|---|---|
| `Parcel_Forecast` | GDB Feature Class | Spatial parcel forecast for GIS use |
| `taz_summary_2035.csv/.pickle` | CSV / Pickle | Alternative-specific TAZ summary — 2035 |
| `taz_summary_2050.csv/.pickle` | CSV / Pickle | Alternative-specific TAZ summary — 2050 |

---

## Key Logic

### Two-Phase Architecture

The workflow is intentionally split so that the computationally expensive parcel engineering (spatial joins, SDE reads) only runs once. All four alternatives share the same engineered parcel layer and start from the same adjusted unit pools.

| Phase | Script | Runs | Key Output |
|---|---|---|---|
| 1A — Parcel Engineering | `parcel_engineering.ipynb` | Once | `base_parcel_data.pkl`, `unit_pool_assigned.csv` |
| 1B — Scenario Template | `scenario_forecast_template.ipynb` | Reference only | — |
| 2 — Scenario Forecast | `Alternative_N_Forecast.ipynb` | Once per alternative | TAZ summaries, parcel forecast |

### Residential Unit Allocation

Units are allocated in a strict priority order:

1. **Known Projects** — directly mapped by APN from the assigned units lookup
2. **CTC Asset Lands** — full buildout assigned to 17 specific parcels
3. **Jurisdictional Pools** — remaining units distributed by jurisdiction (CSLT, DG, PL, WA, EL) and unit type via the `zone_proportions` dictionary:
   - Multifamily (MF) — default 35% of pool (overridable per zone)
   - Single-family (SF) — default 50% of pool (overridable per zone)
   - Infill — default 15% of pool (overridable per zone)
4. **TRPA Pools** — bonus unit and general allocations administered by TRPA
5. **Remainders** — leftover pool units assigned as infill
6. **ADUs** — Accessory Dwelling Units filled to reach regional total

### Pool Proportion Overrides

Each alternative notebook contains a `zone_proportions` dictionary keyed by `(Jurisdiction, Unit_Pool)`. Any zone not listed falls back to global defaults. This allows fine-grained scenario differentiation without changing core allocation logic.

```python
zone_proportions = {
    ('CSLT', 'Bonus Unit'): {'mf': 0.50, 'sf': 0.35, 'infill': 0.15},
    # ... more overrides ...
    'default': {'mf': 0.35, 'sf': 0.50, 'infill': 0.15},
}
```

### Development Year Assignment

| Year | Share | Method |
|---|---|---|
| 2035 | ~33% of total | All "Assigned" projects + proportional random draw |
| 2050 | Remainder | Remaining parcels |

### Parcel Eligibility Conditions

Parcels are filtered by jurisdiction-specific criteria before unit assignment (defined in `utils.get_parcel_conditions()`):
- **Vacant buildable:** private, not retired, IPES score > 0 (Placer: > 726)
- **Infill:** existing residential with specific zoning
- **Bonus unit boundary:** must be within the TRPA-designated polygon
- **ADU eligible:** existing single residential unit with ADU allowed flag set

### Population Calibration

Forecasted population = occupied units × persons per occupied unit (from base-year socioeconomic data). The persons-per-unit factor is adjusted iteratively until regional population targets are met:
- **2035 target:** 55,592 persons
- **2050 target:** 57,611 persons

---

## Key Changes from RTP Model Run

The following changes are common across all alternatives (documented in each `Changes from RTP Model Run.md`):

1. Known residential unit changes from 2022–2025 are pre-incorporated into the input parcel pickle
2. Adjusted zoned unit pools to account for construction between 2022 and 2025 (per K. Kasman)
3. Updated known projects list
4. ADUs are now allowed in Washoe County
5. 33% of allocations assumed to be multi-family (100% occupied); remaining 66% single-family
6. Population in 2035 and 2050 is allowed to vary based on persons per household and occupancy rate (not fixed to a target)

---

## Dependencies

| Package | Use |
|---|---|
| `pandas` | Data manipulation |
| `arcpy` | Spatial joins, SDE reads, feature class export |
| `numpy` | Numeric operations |
| `sqlalchemy` | SQL Server database connections |
| `pathlib` | File path management |
| `pickle` | Intermediate data serialization |
| `utils.py` | Project-specific helper functions (`get_parcel_conditions`, `forecast_residential_units`, `forecast_residential_units_infill`, `get_target_sum`, `check_parcel_condition`, etc.) |

> **Environment:** Requires an ArcGIS Pro Python environment with access to the TRPA SDE geodatabase and SQL Server instances (`sql12`, `sql14`). Database credentials are read from the `DB_USER` and `DB_PASSWORD` environment variables.