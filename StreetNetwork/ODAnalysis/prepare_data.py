"""Package the Tahoe inputs into data/ (reference only; the packaged files are already in data/).

This records where the bundled data came from. It reads the PROTECT ra2ce_v2 inputs, keeps the
columns the OD analysis needs, and writes three GeoPackages:

    data/tahoe_streets.gpkg       Overture drivable street network (97,814 segments)
    data/tahoe_origins.gpkg       2,201 hex-grid origins with population and an equity weight
    data/tahoe_destinations.gpkg  one layer per destination set

You only need to run this to rebuild data/ from a newer PROTECT run:

    python prepare_data.py --src <PROTECT>/scripts/ra2ce_v2/static/network
"""
import argparse
from pathlib import Path

import geopandas as gpd
import pandas as pd

HERE = Path(__file__).resolve().parent
DEFAULT_SRC = HERE.parents[2] / "PROTECT" / "scripts" / "ra2ce_v2" / "static" / "network"

# output layer -> (source shapefile stem, name column, type column)
DESTINATIONS = {
    "evacuation_exits":   ("tahoe_od_evacuation",          "Location",  None),
    "law_enforcement":    ("tahoe_od_locallawenforcement", "NAME",      "TYPE"),
    "medical_facilities": ("tahoe_od_medicalfacilities",   "NAME",      "TYPE"),
    "emergency_shelters": ("tahoe_od_evacuationshelters",  "Name",      "Type"),
    "schools":            ("tahoe_od_schools",             "NAME",      "TYPE"),
    "fresh_food":         ("tahoe_od_freshfoodlocations",  "NAME",      "DESCRIPTIO"),
}


def main(src: Path, out: Path):
    out.mkdir(parents=True, exist_ok=True)

    streets = gpd.read_file(src / "overture_split.shp",
                            columns=["segment_id", "class", "name", "In_Basin"])
    streets = streets.rename(columns={"In_Basin": "in_basin"})
    streets.insert(0, "street_id", range(len(streets)))
    streets.to_file(out / "tahoe_streets.gpkg", layer="streets", driver="GPKG")
    print(f"streets: {len(streets):,}")

    # origins: hex-grid points; equity weight = the block group's poverty weight
    # (1 + normalised poverty rate), 1.0 where an origin falls outside every block group
    o = gpd.read_file(src / "Origins.shp")
    bg = gpd.read_file(src / "blockgroup.shp").to_crs(o.crs)
    w = pd.read_csv(src / "blockgroup_weights.csv").set_index("region")["weight"]
    sj = gpd.sjoin(o[["geometry"]], bg[["region_nam", "geometry"]], how="left", predicate="within")
    sj = sj[~sj.index.duplicated(keep="first")]
    origins = gpd.GeoDataFrame({
        "origin_id": o["OBJECTID"].astype(int),
        "population": o["POPULATION"].fillna(0).astype(float),
        "below_poverty": o["below_pove"].fillna(0).astype(float),
        "blockgroup": sj["region_nam"],
        "equity_wt": sj["region_nam"].map(w).fillna(1.0).astype(float),
    }, geometry=o.geometry, crs=o.crs)
    origins.to_file(out / "tahoe_origins.gpkg", layer="origins", driver="GPKG")
    print(f"origins: {len(origins):,}, population {origins.population.sum():,.0f}")

    dest_path = out / "tahoe_destinations.gpkg"
    dest_path.unlink(missing_ok=True)
    for layer, (stem, name_col, type_col) in DESTINATIONS.items():
        d = gpd.read_file(src / f"{stem}_destinations.shp")
        g = gpd.GeoDataFrame({
            "dest_id": range(len(d)),
            "name": d[name_col].fillna("").astype(str),
            "type": d[type_col].fillna("").astype(str) if type_col else layer.replace("_", " "),
        }, geometry=d.geometry, crs=d.crs)
        g.to_file(dest_path, layer=layer, driver="GPKG")
        print(f"destinations/{layer}: {len(g)}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", type=Path, default=DEFAULT_SRC, help="PROTECT ra2ce_v2 static/network folder")
    ap.add_argument("--out", type=Path, default=HERE / "data")
    a = ap.parse_args()
    main(a.src, a.out)
