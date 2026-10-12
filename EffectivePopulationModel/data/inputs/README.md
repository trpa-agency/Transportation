# Model input data

Nothing in this folder is needed for a normal run. The model's defaults are literal values in the scenario config, so `python run_model.py` works on a fresh clone with no files here and no network access.

This folder exists for the optional `data_sources` blocks, which recompute an input from its original source instead of trusting a literal.

## StreetLight origin-destination export

To enable `data_sources.entry_volume`, drop the OD export here:

```
150448_2018_od_grid_trav_od_traveler_all.csv
```

Relative paths in `od_csv` resolve against this folder; absolute paths are used as given.

The 2018 export is about 16 MB of vendor data and is **not committed to this repo**. Get it from the StreetLight InSight project (study 150448), or point `od_csv` at wherever it already lives on disk.

The handler needs these columns, which are the vendor's own names:

- `Average Daily O-D Traffic (StL Volume)`
- `Origin Zone Is Pass-Through`
- `Destination Zone Is Pass-Through`
- `Day Type`
- `Day Part`

## Census / ACS

Nothing to place here. `second_homes` and `resident_population` read from TRPA's Demographics census service over the network:

<https://maps.trpa.org/server/rest/services/Demographics/MapServer/28>

No API key and no tract shapefile are needed — the service is already limited to basin geographies. See the README's "rebuilding inputs from source data" section.
