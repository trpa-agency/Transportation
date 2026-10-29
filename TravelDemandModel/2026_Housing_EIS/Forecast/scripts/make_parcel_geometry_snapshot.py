"""
make_parcel_geometry_snapshot.py
--------------------------------
One-time build of the static parcel geometry snapshot used by run_scenarios.py
to export a spatial parcel layer for each scenario.

Source: Base/data/processed_data/parcels_base_year.gdb/parcels_base_year
        (the base-year parcels that base_parcel_data.parquet was built from)
Output: Forecast/data/processed_data/base_data/parcel_geometry.gdb/parcel_geometry
        (APN + SHAPE only, one polygon per APN, NAD83 UTM 10N)

The source has a handful of APNs stored as stacked identical polygons; only the
first feature per APN is kept. Re-run only if the base-year parcels change -
every scenario run joins to this snapshot by APN, so changing it changes outputs.

Usage
-----
  python make_parcel_geometry_snapshot.py
"""

from pathlib import Path

import arcpy

SCRIPTS_DIR   = Path(__file__).parent
FORECAST_DIR  = SCRIPTS_DIR.parent
EIS_DIR       = FORECAST_DIR.parent
BASE_DATA_DIR = FORECAST_DIR / 'data' / 'processed_data' / 'base_data'

SOURCE_FC    = EIS_DIR / 'Base' / 'data' / 'processed_data' / 'parcels_base_year.gdb' / 'parcels_base_year'
SNAPSHOT_GDB = BASE_DATA_DIR / 'parcel_geometry.gdb'
SNAPSHOT_FC  = SNAPSHOT_GDB / 'parcel_geometry'


def main():
    arcpy.env.overwriteOutput = True

    if not SNAPSHOT_GDB.exists():
        arcpy.management.CreateFileGDB(str(SNAPSHOT_GDB.parent), SNAPSHOT_GDB.name)

    sr = arcpy.Describe(str(SOURCE_FC)).spatialReference
    arcpy.management.CreateFeatureclass(str(SNAPSHOT_GDB), SNAPSHOT_FC.name, 'POLYGON', spatial_reference=sr)
    arcpy.management.AddField(str(SNAPSHOT_FC), 'APN', 'TEXT', field_length=50)

    seen = set()
    skipped = 0
    with arcpy.da.SearchCursor(str(SOURCE_FC), ['APN', 'SHAPE@'], sql_clause=(None, 'ORDER BY OBJECTID')) as s_cur, \
         arcpy.da.InsertCursor(str(SNAPSHOT_FC), ['APN', 'SHAPE@']) as i_cur:
        for apn, shape in s_cur:
            if apn in seen:
                skipped += 1
                continue
            seen.add(apn)
            i_cur.insertRow((apn, shape))

    print(f"Snapshot written: {SNAPSHOT_FC}")
    print(f"  {len(seen):,} parcels ({skipped} duplicate APN features dropped)")


if __name__ == '__main__':
    main()
