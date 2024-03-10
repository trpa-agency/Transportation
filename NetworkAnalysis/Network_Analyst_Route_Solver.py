## Import system modules
import arcpy
from arcpy import env
import os

try:
    ## Set environment
    route_output = r"//Trpa-fs01/GIS/PROJECTS/Transportation/Active Transportation/Lime Network Analyst"
    ## NA layer data will be saved to the workspace here
    env.workspace = os.path.join(route_output, "Route_test.gdb")
    env.overwriteOutput = True

    ## Define variables
    input_network_dataset = r"//Trpa-fs01/GIS/GIS_DATA/Transportation/Basemap Features/Roads/Streets Network Dataset/Streets_NEW_ND.gdb/Streets_SDC_ND/Streets_CA_NV_ND"
    #network = os.path.join(input_network, "streets", "streets")
    layer_name = "ScooterRouteTest"
    impedance = "Length"
    find_order = "USE_INPUT_ORDER"
    ordering_type = "PRESERVE_BOTH"
    time_windows = "NO_TIMEWINDOWS"
    accumulate_attribute_name = "Length"
    UTurn_policy = "ALLOW_UTURNS"
    #hierarchy = "NO_HIERARCHY"
    output_shape = "TRUE_LINES_WITH_MEASURES"

    ## Create new route layer with inputs specified above
    result_object = arcpy.na.MakeRouteLayer(input_network_dataset, layer_name, impedance, find_order, ordering_type, time_windows, 
                                            accumulate_attribute_name, UTurn_policy, output_shape)

    ## Get the layer object from the result object. The route layer can now be referenced using the layer object
    layer_object = result_object.getOutput(0)

    ## Get names of all sublayers within the route layer
    sublayer_names = arcpy.na.GetNAClassNames(layer_object)
    ## Store layer names we'll use later
    stops_layer_name = sublayer_names["Stops"]
    routes_layer_name = sublayer_names["Routes"]

    ## Define variables to load locations. Sort field is important if we loop the data so we ensure
    ## the analysis is creating routes in order and not failing because the trips are not sorted.
    search_tolerance = "100 Miles"
    sort_field = "trip_id"
    OD_stops = r"//Trpa-fs01/GIS/PROJECTS/Transportation/Active Transportation/Lime Network Analyst/Lime NA.gdb/September_OD_Points_All"

    ## Set up field mapping to define a route ID for each stop.
    ## This ensures each origins and destinations from specific trips are paired properly and
    ## will end up in the same route.
    field_mappings = arcpy.na.NAClassFieldMappings(layer_object, stops_layer_name)
    field_mappings["RouteName"].mappedFieldName = "trip_id"

    ## Add OD points as stops
    arcpy.na.AddLocations(layer_object, stops_layer_name, OD_stops, field_mappings, search_tolerance,
                          sort_field)

    ## Solve the route layer.
    arcpy.na.Solve(layer_object)

    ## Get output routes sublayer and save it to a feature class
    routes_sublayer = layer_object.listLayers(routes_layer_name)[0]
    arcpy.management.CopyFeatures(routes_sublayer, route_output)

    print("Script completed successfully")

except Exception as e:
    # If an error occurred, print line number and error message
    import traceback, sys
    tb = sys.exc_info()[2]
    print("An error occurred on line %i" % tb.tb_lineno)
    print(str(e))
