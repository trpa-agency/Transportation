# Tahoe Effective Population Model (TEPM)

**Purpose:** Estimate the number of people physically present in the Lake Tahoe region on an annual average day — residents, commuters, day visitors, overnight visitors and second home occupants combined.

This is a Python port of the TEPM R-Shiny dashboard ([trpa-reid/tahoe_effective_population_model](https://github.com/trpa-reid/tahoe_effective_population_model)). The arithmetic is unchanged; what changed is how you drive it. Instead of typing numbers into a web form and reading value boxes, you write a JSON scenario config and run a script, the same way the 2026 Housing EIS forecast works. Runs are reproducible, diffable, and leave a full record of which assumptions produced which answer.

---

## Quick start

```bash
cd EffectivePopulationModel/scripts

# Run every config in ../configs/ (just the default scenario, as shipped)
python run_model.py

# Verify the port reproduces the R model's arithmetic
python test_model.py
```

The default config reproduces the dashboard's landing-page result:

| Sub-population | Persons | Share |
| --- | ---: | ---: |
| Full-time residents | 51,577 | 43.4% |
| Commuters | 4,949 | 4.2% |
| Day visitors | 15,924 | 13.4% |
| Overnight visitors | 36,418 | 30.6% |
| Second home owners | 9,989 | 8.4% |
| **Effective population** | **118,856** | |

Peaking ratio (effective population ÷ full-time residents): **2.30**

The rounded sub-populations above add to 118,857, one more than the total. That is correct, not a typo: the model rounds the summed visitor populations once rather than rounding each component first, exactly as the R model did, and at these assumptions the sum falls just under the halfway point. See [methodology §5](metadata/model_methodology.md).

---

## Folder layout

```
EffectivePopulationModel/
├── README.md
├── configs/
│   └── default_config.json              example config holding every default
├── data/
│   ├── inputs/
│   │   └── README.md                    what to drop here for the data sources
│   └── processed_data/                  timestamped run folders
├── metadata/
│   └── model_methodology.md             equations, provenance, known quirks
├── scripts/
│   ├── model.py                         the math — no file or network I/O
│   ├── config.py                        config loading, validation, resolution
│   ├── data_sources.py                  optional StreetLight / TRPA ACS derivations
│   ├── sensitivity.py                   one-at-a-time parameter sweep
│   ├── run_model.py                     CLI entry point
│   └── test_model.py                    verification against the R expressions
└── Engineering/                          input data engineering notebooks
```

---

## How a scenario works

A scenario is one JSON file. Copy `configs/default_config.json`, rename it, edit the numbers:

```jsonc
{
  "scenario_name": "High_Visitation_2035",
  "description": "Tests a 15% increase in overnight capacity.",
  "inputs": {
    "entry_volume": 29000,
    "hotel_units_rented_annual": 2017250,
    ...
  }
}
```

Keys beginning with an underscore (`_comment`, `_entry_volume`, …) are documentation and are ignored by the loader, so a config can carry its own explanation inline.

Every config in `configs/` runs in a batch, and the run writes a comparison table across all of them with the first scenario as the baseline. That is how you compare alternatives — put one config per alternative in a folder and run the folder.

### Command line

```bash
# A specific config, or a folder of them
python run_model.py ../configs/default_config.json
python run_model.py /path/to/alternatives/

# Ignore data_sources blocks and use each config's literal values
python run_model.py --no-data-sources

# Write outputs somewhere else
python run_model.py --out-dir /path/to/output
```

The script exits non-zero if any scenario fails, so it works in a pipeline. A failing scenario does not stop the others — the batch finishes and reports which ones failed.

---

## What a run produces

```
data/processed_data/run_YYYY-MM-DD_HHMMSS/
├── <scenario_name>/
│   ├── effective_population_summary.csv   the five sub-populations and the total
│   ├── entry_volume_accounting.csv        how entry volume splits across trip groups
│   ├── overnight_segments.csv             per-segment vehicles present, arriving, population
│   ├── model_inputs.csv                   every input with its value, unit and provenance
│   ├── sensitivity_tornado.csv            only when sensitivity is enabled
│   ├── results.json                       machine-readable full result
│   └── <config file name>                 copy of the config that produced it
├── configs/                               copy of every config in the batch
├── all_scenarios_summary.csv              one row per scenario, with change from baseline
└── run_log.txt                            the console output of the run
```

`model_inputs.csv` is the audit trail the dashboard never had. Each input is labeled:

- `config` — a literal value in the config file
- `data_source` — computed from StreetLight or the TRPA census service during this run
- `derived` — left null in the config and filled by `derived_input_rules`

`entry_volume_accounting.csv` shows the structure the model actually turns on: day visitors are what is left of the entry volume after freight, discretionary trips, commuters and overnight arrivals are removed. If an assumption pushes that residual negative, the run warns and says so rather than quietly returning a smaller number.

---

## Inputs

| Input | Unit | Default | Source of the default |
| --- | --- | ---: | --- |
| `entry_volume` | vehicles/day | 25,281 | StreetLight InSight 2018 OD study 150448, EI trips |
| `resident_population` | persons | 51,577 | 2018 ACS 5-year |
| `nonresident_commuters` | persons/day | 4,949 | 2018 LEHD/CTPP |
| `resident_commuters` | persons/day | 1,800 | 2018 LEHD/CTPP |
| `freight_trips` | vehicles/day | *derived* → 758 | 3% of entry volume |
| `discretionary_trips` | vehicles/day | *derived* → 8,299 | 7% of overnight population + 5,750 |
| `day_visitor_vehicle_occupancy` | persons/veh | 2.62 | Visitor survey |
| `second_homes` | units | 20,580 | 2018 ACS B25004_006E (26,585) less 6,005 STR units |
| `second_home_occupancy` | share | 0.19 | |
| `vehicles_per_second_home` | vehicles/unit | 1.27 | |
| `second_home_vehicle_occupancy` | persons/veh | 1.97 | |
| `second_home_length_of_stay` | nights | *null* → 4.28 | Falls back to the STR length of stay |
| `str_units_rented_annual` | unit-nights | 482,940 | Transient occupancy tax reporting |
| `vehicles_per_str_unit` | vehicles/unit | 2.07 | |
| `str_length_of_stay` | nights | 4.28 | |
| `str_vehicle_occupancy` | persons/veh | 3.92 | |
| `hotel_units_rented_annual` | room-nights | 1,754,130 | Transient occupancy tax reporting |
| `vehicles_per_hotel_room` | vehicles/room | 1.08 | |
| `hotel_length_of_stay` | nights | 3.44 | |
| `hotel_vehicle_occupancy` | persons/veh | 3.26 | |
| `campsites_rented_annual` | site-nights | 99,284 | |
| `vehicles_per_campsite` | vehicles/site | 1.18 | |
| `campsite_length_of_stay` | nights | 3.64 | |
| `campsite_vehicle_occupancy` | persons/veh | 3.26 | |
| `days_per_year` | days | 365 | |

Three inputs may be `null`. `freight_trips` and `discretionary_trips` are then computed from `derived_input_rules`, reproducing the values the Shiny app rendered on the fly. `second_home_length_of_stay` falls back to the STR length of stay, which is what the R model did.

Everything else is required. The loader reports every problem in a config at once — unknown keys, missing keys, non-numeric values, nulls where a number is required, and values outside their valid range — rather than one per run.

---

## Optional: rebuilding inputs from source data

Some defaults were computed at startup by the R app rather than typed in. The `data_sources` block reproduces them, so a scenario can be re-based on a new data vintage instead of a stale literal. **All are disabled by default**, so the model runs with no network access and no large vendor files on disk.

### `entry_volume` from StreetLight

Sums `Average Daily O-D Traffic (StL Volume)` over OD pairs whose pass-through flags classify them as the requested trip types. `EI` (external origin, internal destination) is the inbound-to-basin volume.

```jsonc
"entry_volume": {
  "enabled": true,
  "od_csv": "150448_2018_od_grid_trav_od_traveler_all.csv",
  "day_type": "0: All Days (M-Su)",
  "day_part": "0: All Day (12am-12am)",
  "trip_types": ["EI"]
}
```

Relative paths resolve against `data/inputs/`. The export is ~16 MB and is vendor data, so it is not committed — see `data/inputs/README.md`.

### ACS variables from the TRPA Demographics service

`second_homes` and `resident_population` come from TRPA's own census table:

<https://maps.trpa.org/server/rest/services/Demographics/MapServer/28>

The R app queried the Census Bureau API directly and then clipped the result to a basin tract shapefile. TRPA's service is already basin-scoped, needs no API key, and is the agency's copy of the same ACS tables, so it replaces both steps. The two reconcile exactly: for 2018 the service returns **26,585** seasonal units and **51,577** residents — the same values the Census API returns for the basin tracts, and the same numbers the R app used.

```jsonc
"second_homes": {
  "enabled": true,
  "service_url": "https://maps.trpa.org/server/rest/services/Demographics/MapServer/28",
  "variable_code": "B25004_006E",
  "dataset": "acs/acs5",
  "sample_level": "tract",
  "year_sample": 2018,
  "subtract_units": 6005
},
"resident_population": {
  "enabled": true,
  "variable_code": "B01003_001E",
  "dataset": "acs/acs5",
  "sample_level": "tract",
  "year_sample": 2018
}
```

The handler is generic over `variable_code` / `dataset` / `sample_level` / `year_sample`, so any variable the table carries can drive either input. ACS variable codes in this table carry the `E` estimate suffix (`B25004_006E`, not `B25004_006`).

Three things the handler enforces, because the table is in long format and the failure mode is a silently wrong sum:

- **`sample_level` must be pinned.** The same variable exists at tract and block group level; summing both double counts. It defaults to `tract`.
- **No geography may appear twice** in the result. If one does, the run fails and names the duplicates rather than returning a doubled total.
- **Soft-deleted rows are excluded** (`delete_flag`), and a non-numeric value in any geography fails the run.

The ACS 5-year table carries vintages **2011–2024**. Tract counts change after 2020 as boundaries were redrawn (26 basin tracts in 2018, 31 from 2022 on); the service handles that itself, so re-basing to a newer year is just a change to `year_sample`. Re-basing the default scenario to 2024 gives an effective population of 120,542 against 118,856 for 2018.

`subtract_units` nets short-term rentals out of the seasonal unit count so they are not also counted in the STR segment.

---

## Optional: sensitivity analysis

The dashboard's value was letting someone nudge an assumption and watch the answer move. The batch equivalent is a tornado table. Enable it in a config:

```jsonc
"sensitivity": {
  "enabled": true,
  "variation": 0.10,
  "parameters": null
}
```

Each parameter runs low and high while everything else holds at its scenario value, and `sensitivity_tornado.csv` reports the swing in effective population, sorted largest first. `null` sweeps every behavioral and volumetric input; otherwise give a list whose entries are either an input name or an object:

```jsonc
"parameters": [
  "entry_volume",
  {"input": "day_visitor_vehicle_occupancy", "low": 2.1, "high": 3.0},
  {"input": "str_length_of_stay", "variation": 0.25}
]
```

Inputs left null in the config re-derive inside every sweep run, so varying `entry_volume` correctly carries through to the freight trips that depend on it.

At the default assumptions and ±10%, the model is most sensitive to entry volume and resident population, then to hotel vehicle occupancy and day visitor vehicle occupancy.

---

## Model structure

```
effective population = full-time residents
                     + non-resident commuters
                     + day visitors
                     + overnight visitors (hotel/motel/resort/casino, STR, campground)
                     + second home occupants
```

Each overnight segment contributes two groups: people *staying* in the region on an average day, and people *arriving* that day. Day visitors are the residual of the entry-station volume:

```
day visitor vehicles = entry volume
                     − freight trips
                     − discretionary trips
                     − non-resident commuter trips
                     − resident commuter trips
                     − arriving vehicles of every overnight segment

day visitor population = day visitor vehicles × day visitor vehicle occupancy
```

Full equations, per-segment derivations and the provenance of each default are in [metadata/model_methodology.md](metadata/model_methodology.md).

---

## Verifying the port

`scripts/test_model.py` checks the Python against a line-by-line transcription of the R value-box expressions — not against a snapshot of the Python's own output, so it is a real check on the translation:

```bash
python scripts/test_model.py
```

It covers the defaults and a perturbed set of assumptions, the entry-volume accounting identity, both second-home quirks the R model contains, config validation, the negative-residual warning, and the sensitivity sweep's re-derivation behavior.

The data-source derivations independently reproduce the literal defaults shipped in the config — 25,281 entry vehicles from the StreetLight export, and 26,585 seasonal units and 51,577 residents from the TRPA census service — which confirms those numbers are right.

---

## Differences from the R app

**Preserved exactly.** All arithmetic. Python's `round` and R's `round` both use round-half-to-even, so results match to the unit. Two quirks in the R model's second-home treatment are preserved deliberately and documented in the methodology: the stay population omits the vehicles-per-home factor that the other segments apply, and arrivals are divided by the STR length of stay. `second_home_length_of_stay` lets you override the second one without touching code.

**Dropped.** The Shiny UI, the leaflet boundary map and the embedded documentation PDF. None of them fed the calculation.

**Added.** Config validation with all errors reported at once. Input provenance tracking. Entry-volume accounting output. A warning when the day-visitor residual goes negative. Batch scenario comparison. The sensitivity sweep. Verification tests.

**One thing to fix on the R side:** `app.R` hard-codes a Census API key in plain text at line 19. If that app has ever been published or shared, treat the key as exposed and rotate it. This port needs no key at all — it reads the same ACS tables from TRPA's Demographics service.
