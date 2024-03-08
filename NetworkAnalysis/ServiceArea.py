# An example showing how to perform service area analysis using a feature class for input facilities.
import arcpy
arcpy.CheckOutExtension("network")

nds = "C:/data/NorthAmerica.gdb/Routing/Routing_ND"
nd_layer_name = "Routing_ND"
input_facilities = "C:/data/io.gdb/Facilities"
output_polygons = "C:/data/io.gdb/ServiceAreaPolygons"

# Create a network dataset layer and get the desired travel mode for analysis
arcpy.nax.MakeNetworkDatasetLayer(nds, nd_layer_name)
nd_travel_modes = arcpy.nax.GetTravelModes(nd_layer_name)
travel_mode = nd_travel_modes["Driving Time"]

# Instantiate a ServiceArea solver object
service_area = arcpy.nax.ServiceArea(nd_layer_name)
# Set properties
service_area.timeUnits = arcpy.nax.TimeUnits.Minutes
service_area.defaultImpedanceCutoffs = [5, 10, 15]
service_area.travelMode = travel_mode
service_area.outputType = arcpy.nax.ServiceAreaOutputType.Polygons
service_area.geometryAtOverlap = arcpy.nax.ServiceAreaOverlapGeometry.Split
# Load inputs
service_area.load(arcpy.nax.ServiceAreaInputDataType.Facilities, input_facilities)
# Solve the analysis
result = service_area.solve()

# Export the results to a feature class
if result.solveSucceeded:
    result.export(arcpy.nax.ServiceAreaOutputDataType.Polygons, output_polygons)
else:
    print("Solve failed")
    print(result.solverMessages(arcpy.nax.MessageSeverity.All))