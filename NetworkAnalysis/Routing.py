# script to route along the network
# An example showing how to perform route analysis using a feature class for input stops.
import arcpy
arcpy.CheckOutExtension("network")

nds = "C:/data/NorthAmerica.gdb/Routing/Routing_ND"
nd_layer_name = "Routing_ND"
input_stops = "C:/data/io.gdb/Stops"
output_routes = "C:/data/io.gdb/Routes"

# Create a network dataset layer and get the desired travel mode for analysis
arcpy.nax.MakeNetworkDatasetLayer(nds, nd_layer_name)
nd_travel_modes = arcpy.nax.GetTravelModes(nd_layer_name)
travel_mode = nd_travel_modes["Driving Time"]

# Instantiate a Route solver object
route = arcpy.nax.Route(nd_layer_name)
# Set properties
route.timeUnits = arcpy.nax.TimeUnits.Minutes
route.travelMode = travel_mode
route.routeShapeType = arcpy.nax.RouteShapeType.TrueShapeWithMeasures
# Load inputs
route.load(arcpy.nax.RouteInputDataType.Stops, input_stops)
# Solve the analysis
result = route.solve()

# Export the results to a feature class
if result.solveSucceeded:
    result.export(arcpy.nax.RouteOutputDataType.Routes, output_routes)
else:
    print("Solved failed")
    print(result.solverMessages(arcpy.nax.MessageSeverity.All))