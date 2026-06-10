"""
run_walk_service_area.py

Runs a 5/10/20-minute walk Service Area solve against school points using the
Overture_Walk_ND network dataset and exports polygons to Streets_Network.gdb.

Run from:
  - ArcGIS Pro Python window:  exec(open(r"C:/Users/amcclary/Documents/GitHub/Transportation/StreetNetwork/run_walk_service_area.py").read())
  - Command prompt:             python run_walk_service_area.py
"""

# Python 3.13 no longer re-exports datetime_CAPI from the datetime namespace —
# arcpy's NA C extension needs it there via PyCapsule_Import before it loads.
import _datetime
import datetime
if not hasattr(datetime, "datetime_CAPI") and hasattr(_datetime, "datetime_CAPI"):
    datetime.datetime_CAPI = _datetime.datetime_CAPI

import arcpy
import os

# =============================================================================
# CONFIGURATION
# =============================================================================
GDB_PATH         = r"F:\GIS\PROJECTS\Transportation\Streets Network\Streets_Network.gdb"
FDS_NAME         = "OvertureStreets"
ND_NAME          = "Overture_Walk_ND"
POINTS_FC        = os.path.join(GDB_PATH, "School")
SA_OUT_FC        = os.path.join(GDB_PATH, "Walk_ServiceArea_5_10_20min")

CUTOFFS          = [5, 10, 20]   # minutes
IMPEDANCE        = "WalkTime"
SA_LAYER_NAME    = "Walk_ServiceArea"
SEARCH_TOLERANCE = "500 Meters"

# =============================================================================
# DERIVED PATHS
# =============================================================================
FDS_PATH = os.path.join(GDB_PATH, FDS_NAME)
ND_PATH  = os.path.join(FDS_PATH, ND_NAME)

# =============================================================================
# SOLVE
# =============================================================================
print(f"Network Dataset: {ND_PATH}")
if not arcpy.Exists(ND_PATH):
    raise FileNotFoundError(f"Network Dataset not found: {ND_PATH}")

arcpy.CheckOutExtension("network")

arcpy.ResetEnvironments()
arcpy.env.workspace = GDB_PATH

sa_result = arcpy.na.MakeServiceAreaLayer(
    in_network_dataset         = ND_PATH,
    out_network_analysis_layer = SA_LAYER_NAME,
    impedance_attribute        = IMPEDANCE,
    default_break_values       = " ".join(str(c) for c in CUTOFFS),
    nesting_type               = "DISKS",   # cumulative polygons, not rings
)
layer_name = sa_result.getOutput(0)
print("Service area layer created.")

fac_count = int(arcpy.management.GetCount(POINTS_FC)[0])
print(f"Adding {fac_count} facilities...")
arcpy.na.AddLocations(
    in_network_analysis_layer = layer_name,
    sub_layer                 = "Facilities",
    in_table                  = POINTS_FC,
    search_tolerance          = SEARCH_TOLERANCE,
)

print("Solving...")
arcpy.na.Solve(layer_name, ignore_invalids="SKIP")
print("Solve complete.")

sublayer_names = arcpy.na.GetNAClassNames(layer_name)
poly_key  = next(k for k in sublayer_names if "Polygon" in k)
poly_name = sublayer_names[poly_key]

if arcpy.Exists(SA_OUT_FC):
    arcpy.management.Delete(SA_OUT_FC)
arcpy.management.CopyFeatures(str(layer_name) + "\\" + poly_name, SA_OUT_FC)

n = int(arcpy.management.GetCount(SA_OUT_FC)[0])
print(f"\nDone: {n} polygons -> {SA_OUT_FC}")
