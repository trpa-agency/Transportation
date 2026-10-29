# Origin-destination analysis on the Tahoe street network

A self-contained tool for routing people from origins (where they live) to destinations (hospitals,
exits, schools, anything with a point location) over the street network. It answers two questions:

* **Access:** how long does each origin take to reach its destination, and which one does it use?
* **Reliance:** which streets carry those trips, and how many people depend on each one?

Everything needed is in this folder: the code, the Tahoe street network, population origins, and six
destination sets. No ArcGIS license, network dataset, or RA2CE install is required.

```text
ODAnalysis/
|- README.md               this file
|- odtool.py               the library: build network, snap, route, summarize
|- run_od.py               command-line runner
|- tahoe_analyses.yaml     config that runs all six Tahoe analyses
|- example.ipynb           worked example with maps (start here)
|- prepare_data.py         how data/ was built (reference; not needed to run)
|- environment.yml         conda environment
|- requirements.txt        pip equivalent
|- data/
|  |- tahoe_streets.gpkg       97,814 drivable street segments (Overture, 2026-05-20 release)
|  |- tahoe_origins.gpkg       2,201 hex-grid origins with population and equity weight
|  |- tahoe_destinations.gpkg  six layers: evacuation_exits, law_enforcement, medical_facilities,
|                              emergency_shelters, schools, fresh_food
|- output/                 results (created on first run; not committed)
```

## Quick start

1. **Set up Python** (once). Any environment with geopandas 1.0+, shapely 2.0+, scipy and pyogrio works,
   including a clone of the ArcGIS Pro environment that has geopandas added. For a clean one:

   ```powershell
   conda env create -f environment.yml
   conda activate od-analysis
   ```

2. **Open the example.** `jupyter lab example.ipynb`, then Run All (about two minutes). It runs an
   evacuation analysis, a medical-facility analysis, a deterministic-versus-stochastic comparison, and
   an analysis with destinations you type in.

3. **Or run from the command line.** From this folder:

   ```powershell
   # one analysis
   python run_od.py --destinations data/tahoe_destinations.gpkg --dest-layer medical_facilities --mode gravity

   # all six Tahoe analyses (about 13 minutes)
   python run_od.py --config tahoe_analyses.yaml
   ```

   Run `python run_od.py --help` for every option. Results land in `output/`.

## Using it from Python

```python
import geopandas as gpd
import odtool

streets = gpd.read_file("data/tahoe_streets.gpkg")
origins = gpd.read_file("data/tahoe_origins.gpkg")
hospitals = gpd.read_file("data/tahoe_destinations.gpkg", layer="medical_facilities")

net = odtool.build_network(streets, class_col="class")       # build once, reuse for every analysis
res = odtool.run_od(net, origins, hospitals, mode="gravity",
                    population="population", weight="equity_wt", origin_id="origin_id")

res.summary                       # person-km, person-hours, mean trip time, reachable population
res.segments                      # streets with traffic columns (GeoDataFrame)
res.origins                       # each origin's travel time and distance
res.matrix                        # every origin-to-destination time, distance (and gravity share)
res.save("output", "medical")     # writes the five output files
```

### Using your own data

* **Destinations:** any point layer in any CRS: a shapefile, a GeoPackage layer, or a feature class
  exported to GeoPackage. A `name` column is carried into the outputs if present (`dest_name=` to use
  another).
* **Origins:** any point layer. Pass the population column with `population=` (or `None` to count each
  origin once) and an equity weight with `weight=` (or `None`). Polygons (parcels, block groups) should
  be converted to centroids first.
* **Streets:** any line layer. Set `class_col=` to its road-class column and pass `speeds={class: mph}`,
  or set `speed_col=` to a field holding a speed in mph. Lines must meet at their end points to be
  connected (Overture segments do). `crs=` sets the metric CRS lengths are measured in; the default,
  EPSG:3310 (California Albers), covers the Tahoe region.

## Method

1. **Graph.** Each street line is an edge between its two end points; lines sharing an end point are
   connected. Where two lines join the same pair of points (a loop road beside a street), both are kept
   and the faster one carries the trips in each routing pass. The graph is undirected: one-way
   restrictions and turn penalties are not modeled.
2. **Travel time.** Each edge's time is its length at a free-flow speed set by road class:

   | class | mph | | class | mph |
   |---|---|---|---|---|
   | motorway | 55 | | residential, unclassified | 25 |
   | trunk | 45 | | living_street, service | 10 |
   | primary | 35 | | unknown | 15 |
   | secondary, tertiary | 30 | | anything else | 25 |

   These are starting assumptions, not calibrated speeds. `cost="distance"` routes on shortest distance
   instead.
3. **Snapping.** Each origin and destination is moved to the nearest point on the nearest street in the
   largest connected part of the network, and the street is split there. The distance moved is reported
   as `snap_m`; check large values.
4. **Destination choice.**
   * `nearest`: all of an origin's trips go to the destination it reaches fastest. Use it where people
     go to the closest option (evacuation exits, police response areas).
   * `gravity`: trips split across all destinations in proportion to `time ** -beta` (beta = 2 by
     default), so a destination twice as far draws a quarter as many trips. Use it where people have a
     real choice (hospitals, grocery stores, schools).
5. **Stochastic assignment.** Routing is repeated `n_draws` times (default 100). In each draw every
   street's travel time is multiplied by a random factor with mean 1 and about 25 percent spread
   (`sigma=0.25`, lognormal), and destination choice is redone on the perturbed times. Results are the
   average over draws. In a street grid many routes are nearly tied; a single shortest-path run picks one
   and loads every upstream trip on it, so one block looks critical and its neighbors look empty.
   Averaging spreads trips over the near-ties while a clearly faster road still wins nearly every draw.
   `n_draws=1, sigma=0` gives a single deterministic run.
6. **Routing engine.** Dijkstra (scipy) runs once from each destination, giving a shortest-path tree that
   covers every origin at once; trips are accumulated down the tree. This is why it is fast: a
   seven-destination run of 100 draws takes about 25 seconds, against hours for routing each OD pair.
   Runtime grows with the number of destinations under `gravity` (33 grocery stores take about five
   minutes).

## Outputs

`res.save(folder, name)` and `run_od.py` write:

| file | contents |
|---|---|
| `<name>_segments.gpkg` | every input street with the traffic fields below |
| `<name>_origins.gpkg` | every origin with its access fields below |
| `<name>_destinations.csv` | trips arriving at each destination, snap distance |
| `<name>_od_matrix.csv` | one row per origin x destination: `time_min`, `dist_km` (and `share` for gravity) |
| `<name>_summary.json` | run settings and totals |

**Street fields** (averages over the draws):

| field | meaning |
|---|---|
| `traffic` | people whose trip crosses the street (population routed) |
| `traffic_egalitarian` | number of origins whose trip crosses it, ignoring population |
| `traffic_prioritarian` | population x equity weight: trips from higher-poverty areas count more |
| `traffic_sd` | draw-to-draw standard deviation of `traffic`; high relative to `traffic` means the street shares its load with a near-tied alternative |
| `routed` | 1 if any trip crossed the street in any draw |
| `mph` | speed used |

A street split by a snapped point takes the larger value of its two pieces.

**Origin fields:** `time_min` and `dist_km` (free-flow, along the chosen route; under `gravity`, the
share-weighted average over destinations), `dest_id` and `dest_name` (`nearest` only), `reachable`,
`snap_m`.

**Summary:** `person_km` and `person_hours` (total travel), `mean_trip_min` (population-weighted),
`population_reachable`, `origins_unreachable`, and `trip_check_max_gap`: in every draw, the trips sent to
each destination are compared with the trips that arrive at it after routing; the largest gap must be 0.

**Reading traffic totals.** Summed street `traffic` is not a trip count. A trip adds its population to
every street it crosses, and with stochastic assignment it is spread over parallel streets. Compare runs
on `person_km` or on individual streets, not on summed traffic.

## The Tahoe data

| file | source | notes |
|---|---|---|
| `tahoe_streets.gpkg` | Overture Maps transportation segments, 2026-05-20 release, drivable classes | 2,529 segments that shared both end points with another were split at their midpoint, so every link is distinct. `segment_id` is the Overture ID (repeated on the two halves of a split segment); `street_id` is unique. `in_basin` = 1 inside the Tahoe Basin. |
| `tahoe_origins.gpkg` | TRPA Demographics hex grid (2024 sample year) | `population` per hex. `equity_wt` = 1 + the block group's normalized poverty rate (1.0 outside the block groups); `blockgroup` names it. |
| `tahoe_destinations.gpkg` | TRPA and HIFLD facility layers | evacuation_exits (7 highway exits from the basin), law_enforcement (7), medical_facilities (5), emergency_shelters (9), schools (21), fresh_food (33). `dest_id` is the row order. |

These are the inputs to the TRPA PROTECT criticality analysis (FHWA PROTECT grant). `prepare_data.py`
records how they were cut from that project's files.

## Validation

The method reproduces the PROTECT analysis built on RA2CE (Deltares):

| destination set | mode | person-km, distance cost: this tool vs. RA2CE | street traffic correlation with the PROTECT stochastic run |
|---|---|---|---|
| evacuation exits | nearest | +0.08 percent | 0.994 |
| law enforcement | nearest | +0.36 percent | 0.996 |
| medical facilities | gravity | +0.10 percent | 0.999 |
| emergency shelters | gravity | -0.07 percent | 0.998 |
| schools | gravity | no RA2CE run | 0.994 |
| fresh food | gravity | no RA2CE run | 0.994 |

The small differences come from snapping: RA2CE snaps to any street, this tool to the main connected
network, and it builds the graph from the street lines directly rather than through RA2CE's simplified
graph. Every street matched between the two.

## Limits

* Free-flow speeds by class; no congestion, signals, turn penalties, or one-way streets.
* Speeds are assumptions. Calibrate them (or pass observed speeds with `speed_col=`) before quoting
  travel times as observed.
* Population sits at hex-grid points; trips start at the nearest street to each point.
* Streets not connected to the main network (private roads, gaps in Overture) receive no trips, and
  points are never snapped to them.
