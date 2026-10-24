# Tahoe Effective Population Model — Methodology

**Model:** Tahoe Effective Population Model (TEPM)
**Implementation:** `EffectivePopulationModel/scripts/`
**Ported from:** [trpa-reid/tahoe_effective_population_model](https://github.com/trpa-reid/tahoe_effective_population_model) (`app.R` / `script.R`)

This document records the equations the model evaluates, where each default comes from, and the places where the original R implementation does something surprising that the port preserves on purpose. It is the reference for anyone who needs to defend a TEPM number or change an assumption.

---

## 1. What the model estimates

**Effective population** is the number of people physically present in the Lake Tahoe region on an *annual average day*. It is not a residential population, not a peak-day count, and not an annual visitation total. It answers: on a typical day, how many people are in the basin using its roads, water, parking and services?

The estimate is built from five sub-populations:

```
effective population = full-time residents
                     + non-resident commuters
                     + day visitors
                     + overnight visitors (hotel/motel/resort/casino, STR, campground)
                     + second home occupants
```

Residents and commuters are read directly from data. The three visitor groups are modeled, and the modeling hinges on one structural idea: **the entry-station traffic volume is a budget**. Every vehicle entering the region on an average day belongs to some known group. Day visitors are what is left after every other group is accounted for.

---

## 2. Overnight segments

Four segments share one structure: hotel/motel/resort/casino, short-term rentals (STRs/VHRs), campgrounds and second homes. Each contributes two groups of people — those already in the region, and those arriving that day.

### 2.1 Occupied units on an average day

For the three commercial segments, occupancy comes from annual unit-nights rented:

```
occupied units = annual unit-nights rented ÷ days per year
```

Second homes are a housing *stock*, not a rental flow, so occupancy is a share:

```
occupied units = second homes × second home occupancy
```

### 2.2 Vehicles

```
vehicles present  = occupied units × vehicles per unit
arriving vehicles = vehicles present ÷ length of stay
```

Dividing by length of stay converts a stock of vehicles into a daily arrival rate. If the average party stays 3.44 nights, roughly 1 in 3.44 of the vehicles present arrived today.

### 2.3 Population

```
stay population    = vehicles present  × vehicle occupancy
arrival population = arriving vehicles × vehicle occupancy
segment population = stay population + arrival population
```

Arrivals are counted on top of the staying population because people arriving that day are in the region that day as well, in addition to those already there.

### 2.4 Worked example — hotels at the default assumptions

| Step | Calculation | Result |
| --- | --- | ---: |
| Occupied rooms | 1,754,130 ÷ 365 | 4,805.8 |
| Vehicles present | 4,805.8 × 1.08 | 5,190.3 |
| Arriving vehicles | 5,190.3 ÷ 3.44 | 1,508.8 |
| Stay population | 5,190.3 × 3.26 | 16,920.4 |
| Arrival population | 1,508.8 × 3.26 | 4,918.7 |
| **Hotel population** | | **21,839.1** |

Applying the same steps to STRs (13,244.8) and campgrounds (1,333.8) gives an **overnight visitor population of 36,418**.

---

## 3. Day visitors

Day visitors are the residual of the entry-volume budget:

```
day visitor vehicles = entry volume
                     − freight trips
                     − discretionary trips
                     − non-resident commuter trips
                     − resident commuter trips
                     − arriving vehicles of every overnight segment

day visitor population = day visitor vehicles × day visitor vehicle occupancy
```

At the defaults:

| Component | Vehicles/day |
| --- | ---: |
| Total entry volume | 25,281.0 |
| less Freight trips | 758.0 |
| less Discretionary trips | 8,299.0 |
| less Non-resident commuter trips | 4,949.0 |
| less Resident commuter trips | 1,800.0 |
| less Hotel arriving vehicles | 1,508.8 |
| less STR arriving vehicles | 639.9 |
| less Campground arriving vehicles | 88.2 |
| less Second home arriving vehicles | 1,160.3 |
| **= Day visitor vehicles** | **6,077.8** |

6,077.8 × 2.62 = **15,924 day visitors**.

Because day visitors are a residual, **every other assumption in the model pushes on them**. Raising hotel occupancy does not only add overnight visitors, it also removes day-visitor vehicles from the budget. This partial offset is the single most important thing to understand before changing an assumption, and it is why `entry_volume_accounting.csv` is written on every run.

The residual can in principle go negative, which means the stated non-day-visitor trips exceed the entry volume. The model warns rather than returning the negative number silently.

Commuter and freight trips enter the budget as **vehicles**, i.e. one person per vehicle. Commuters are then added to effective population as persons directly, not through vehicle occupancy.

---

## 4. Second homes

```
occupied homes     = second homes × second home occupancy
stay population    = occupied homes × second home vehicle occupancy
arriving vehicles  = (occupied homes × vehicles per second home) ÷ length of stay
arrival population = arriving vehicles × second home vehicle occupancy
```

At the defaults: 20,580 × 0.19 = 3,910.2 occupied homes → 7,703.1 staying + 2,285.7 arriving = **9,989 second home occupants**.

Second homes are reported as their own sub-population, separate from overnight visitors, matching the dashboard's value boxes.

---

## 5. Effective population

```
effective population = resident population
                     + non-resident commuters
                     + round(day visitors + overnight visitors + second home occupants)
```

The rounding is applied **once, to the summed visitor populations**, not to each component. At the defaults: 51,577 + 4,949 + round(15,923.9 + 36,417.8 + 9,988.8) = 56,526 + round(62,330.4989) = **118,856**.

This is not a pedantic detail at the default assumptions. The visitor sum lands at 62,330.4989, a hair under the halfway point. Rounding the three components separately first would give 15,924 + 36,418 + 9,989 = 62,331 and an effective population of 118,857. The model rounds once, so the answer is 118,856.

Python's `round` and R's `round` both use round-half-to-even, so the Python port matches the R output to the unit.

**Peaking ratio** (a reporting metric added in this port) is effective population ÷ full-time residents: **2.30** at the defaults. On an average day the basin holds about 2.3 people for every full-time resident.

---

## 6. Derived inputs

Two inputs had no literal default in the Shiny app — it computed them on the fly in `renderUI` blocks. Leaving them `null` in a config reproduces that behavior:

| Input | Rule | Value at defaults |
| --- | --- | ---: |
| `freight_trips` | `round(entry volume × 0.03)` | 758 |
| `discretionary_trips` | `round(round(overnight population) × 0.07) + 5,750` | 8,299 |

The coefficients are themselves configurable, under `derived_input_rules`.

Discretionary trips are residents and overnight visitors leaving the basin and returning — a Costco run, a ski day at Kirkwood. They occupy entry-station capacity without adding a new person to the region, so they are removed from the day-visitor budget. The rule has two parts: a component that scales with overnight visitation (7%) and a fixed resident component (5,750).

Note that `discretionary_trips` depends on the overnight population, so it moves when lodging assumptions move. There is no circularity — the overnight population does not depend on the entry-volume budget.

---

## 7. Provenance of the defaults

| Input | Default | Source |
| --- | ---: | --- |
| `entry_volume` | 25,281 | StreetLight InSight 2018 OD study 150448, external-origin/internal-destination trips, all days, all day |
| `resident_population` | 51,577 | 2018 ACS 5-year `B01003_001E`, basin tracts |
| `nonresident_commuters` | 4,949 | 2018 LEHD/CTPP |
| `resident_commuters` | 1,800 | 2018 LEHD/CTPP |
| `second_homes` | 20,580 | 2018 ACS 5-year `B25004_006E` (26,585) less 6,005 STR units |
| `str_units_rented_annual` | 482,940 | Transient occupancy tax reporting |
| `hotel_units_rented_annual` | 1,754,130 | Transient occupancy tax reporting |
| `campsites_rented_annual` | 99,284 | Campground reservation data |
| Vehicle occupancies, vehicles per unit, lengths of stay | various | Visitor intercept surveys and lodging operator reporting |

### 7.1 Entry volume

The StreetLight export classifies each OD pair by whether its origin and destination zones are pass-through. External origin with internal destination (EI) is an inbound trip. Summing EI volume over the all-days, all-day slice gives 25,281 average daily inbound vehicles. IE (25,757) is the outbound mirror and is not used — the model counts entries, not exits.

### 7.2 Census variables

The R app queried the Census Bureau API for `B25004_006` across four counties (El Dorado, Placer, Douglas, Washoe) and then clipped the result to a basin tract shapefile.

This port reads the same ACS tables from TRPA's Demographics census service instead:

<https://maps.trpa.org/server/rest/services/Demographics/MapServer/28>

The service is already basin-scoped, so no clipping step is needed, and it requires no API key. The two sources reconcile exactly — for 2018 both give 26,585 seasonal units and 51,577 residents.

The table is in long format (one row per geography, variable and vintage), which creates two ways to get a silently wrong answer. The handler guards both: `sample_level` is pinned so the same variable is not summed at tract *and* block group level, and a duplicated geography in the result fails the run rather than doubling the total.

ACS 5-year vintages 2011–2024 are available. Tract counts change after 2020 as boundaries were redrawn (26 basin tracts in 2018, 31 from 2022 on).

**6,005 STR units** are subtracted from the seasonal unit count. The ACS "seasonal, recreational, or occasional use" category includes units that are rented as STRs, which the model already counts in the STR segment. Without the subtraction those units would contribute twice.

---

## 8. Known quirks preserved from the R model

These are places where the original implementation is internally inconsistent. The port reproduces them so its numbers match, and documents them so they can be changed deliberately rather than by accident. Both are covered by tests in `scripts/test_model.py`.

### 8.1 Second-home stay population omits vehicles per home

Hotels, STRs and campgrounds compute stay population as `vehicles present × vehicle occupancy`. Second homes compute it as `occupied homes × vehicle occupancy` — the 1.27 vehicles-per-home factor is **not** applied.

The second-home *arrival* population does apply it.

One reading is that 1.97 is being used as persons-per-occupied-home in the stay term and persons-per-vehicle in the arrival term. Either way the two terms are not on the same basis. Applying the factor to both would raise the second-home stay population from 7,703 to 9,783 and effective population from 118,856 to about 120,936 — roughly 1.8%.

In the code this is `OvernightSegment.count_vehicles_in_stay_population`, set `False` for second homes only.

### 8.2 Second-home arrivals use the STR length of stay

Second-home arriving vehicles are divided by `str_length_of_stay` (4.28 nights), not by a second-home-specific value. A second home stay is generally longer than an STR stay, so this likely overstates second-home arrivals and, through the entry-volume budget, understates day visitors.

`second_home_length_of_stay` is exposed in the config. It defaults to `null`, which reproduces the R behavior. Setting it to a number uses that value instead — no code change needed.

---

## 9. Limitations

- **Annual average day.** The model has no seasonality. A July Saturday and a November Tuesday are both "an average day". Peak-day planning needs a different tool or a scenario with peak-period assumptions substituted throughout.
- **Day visitors are a residual.** They absorb all error in the entry volume and in every subtracted group. An entry volume that is 5% low pushes the entire error into day visitors.
- **One person per commuter and freight vehicle.** Carpooling among commuters is not modeled.
- **Mixed data vintages.** The defaults combine 2018 ACS, 2018 StreetLight, 2018 LEHD/CTPP and TOT reporting from adjacent years. They are internally consistent enough for the base year but should be re-based together, not one at a time.
- **No pass-through traffic.** EE trips (2,216/day in the 2018 StreetLight data) cross the region without stopping and are excluded from the entry-volume budget. They still use the road network, so a VMT or congestion question needs them added back.
- **Static second-home occupancy.** A single 19% rate covers all second homes year-round.

---

## 10. Changing an assumption

1. Copy `configs/default_config.json` and rename it. Set `scenario_name` and `description`.
2. Edit the inputs you are changing. Leave the rest alone — the file is the complete assumption set, and a scenario is only meaningful against the full baseline.
3. Put the scenario config in a folder with the baseline config and run the folder. The run writes `all_scenarios_summary.csv` with the change from the first scenario.
4. Read `entry_volume_accounting.csv` before believing the answer. If the change moved overnight arrivals, some of the population it added came back out of day visitors.
5. If you are not sure an assumption matters, enable `sensitivity` and read `sensitivity_tornado.csv` instead of guessing.

At the defaults and ±10%, the model is most sensitive to entry volume (±12,852 effective population) and resident population (±10,315), then hotel vehicle occupancy (±3,567) and day visitor vehicle occupancy (±3,185).
