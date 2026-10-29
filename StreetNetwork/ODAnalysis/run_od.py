"""Run an origin-destination analysis from the command line.

One analysis from arguments:

    python run_od.py --destinations data/tahoe_destinations.gpkg --dest-layer medical_facilities \
        --mode gravity --name medical_facilities

Several analyses from a config file (see tahoe_analyses.yaml):

    python run_od.py --config tahoe_analyses.yaml

Outputs go to output/ (or --out): <name>_segments.gpkg, <name>_origins.gpkg,
<name>_destinations.csv, <name>_od_matrix.csv, <name>_summary.json.
"""
import argparse
import json
from pathlib import Path

import geopandas as gpd

import odtool

HERE = Path(__file__).resolve().parent
DEFAULTS = dict(
    streets=str(HERE / "data" / "tahoe_streets.gpkg"), streets_layer=None, class_col="class",
    speed_col=None, speeds=None,
    origins=str(HERE / "data" / "tahoe_origins.gpkg"), origins_layer=None,
    population="population", weight="equity_wt", origin_id="origin_id",
    destinations=None, dest_layer=None, dest_name="name",
    mode="nearest", cost="time", n_draws=100, sigma=0.25, beta=odtool.GRAVITY_BETA, seed=20261008,
    out=str(HERE / "output"),
)


def read(path, layer=None):
    return gpd.read_file(path, layer=layer) if layer else gpd.read_file(path)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", help="YAML file with `defaults:` and a list of `analyses:`")
    ap.add_argument("--name", help="output file prefix (default: the destination layer or file name)")
    for k, v in DEFAULTS.items():
        if k == "speeds":
            continue
        ap.add_argument("--" + k.replace("_", "-"), default=None,
                        type=type(v) if isinstance(v, (int, float)) else str)
    a = ap.parse_args()

    cli = {k: v for k, v in vars(a).items() if k in DEFAULTS and v is not None}
    if a.config:
        import yaml
        cfg = yaml.safe_load(Path(a.config).read_text(encoding="utf-8"))
        base = {**DEFAULTS, **(cfg.get("defaults") or {}), **cli}
        jobs = [{**base, **job} for job in cfg["analyses"]]
        cfg_dir = Path(a.config).resolve().parent
    else:
        if not cli.get("destinations"):
            ap.error("--destinations is required (or use --config)")
        jobs = [{**DEFAULTS, **cli, "name": a.name}]
        cfg_dir = Path.cwd()

    def resolve(p):
        return None if p is None else str((cfg_dir / p).resolve()) if not Path(p).is_absolute() else p

    networks = {}
    for job in jobs:
        for k in ("streets", "origins", "destinations", "out"):
            job[k] = resolve(job[k])
        for k in ("population", "weight", "class_col"):      # "none" on the command line = no column
            if isinstance(job[k], str) and job[k].lower() in ("none", "null", ""):
                job[k] = None
        name = job.get("name") or job["dest_layer"] or Path(job["destinations"]).stem
        print(f"\n=== {name}: {job['mode']} / {job['cost']} / {job['n_draws']} draws")
        nkey = (job["streets"], job["streets_layer"], job["class_col"], job["speed_col"],
                json.dumps(job["speeds"], sort_keys=True))
        if nkey not in networks:
            networks[nkey] = odtool.build_network(read(job["streets"], job["streets_layer"]),
                                                  class_col=job["class_col"], speed_col=job["speed_col"],
                                                  speeds=job["speeds"])
        res = odtool.run_od(
            networks[nkey], read(job["origins"], job["origins_layer"]),
            read(job["destinations"], job["dest_layer"]), mode=job["mode"],
            population=job["population"], weight=job["weight"], cost=job["cost"],
            n_draws=int(job["n_draws"]), sigma=float(job["sigma"]), beta=float(job["beta"]),
            seed=int(job["seed"]), origin_id=job["origin_id"], dest_name=job["dest_name"])
        folder = res.save(job["out"], name)
        print(f"wrote {folder / name}_*")


if __name__ == "__main__":
    main()
