import arcpy

# workspace
arcpy.env.workspace = r"F:\GIS\PROJECTS\Transportation\Vision Zero\CrashAnalysis\Crash Analysis.gdb"

# get OSM streets for Tahoe

# clip to Tahoe boundary

# dissolve
arcpy.management.Dissolve(
    in_features="Tahoe_OSM_Streets",
    out_feature_class="Tahoe_OSM_Streets_Dissolve",
    dissolve_field=None,
    statistics_fields=None,
    multi_part="SINGLE_PART",
    unsplit_lines="DISSOLVE_LINES",
    concatenation_separator=""
)

# generate ponts along line
arcpy.management.GeneratePointsAlongLines(
    Input_Features="Tahoe_OSM_Streets_Dissolve",
    Output_Feature_Class="Tahoe_OSM_Streets_GeneratePointsAlongLines_HalfMile",
    Point_Placement="DISTANCE",
    Distance="0.5 Miles",
    Percentage=None,
    Include_End_Points="NO_END_POINTS",
    Add_Chainage_Fields="NO_CHAINAGE"
)

# split lines at points
arcpy.management.SplitLineAtPoint(
    in_features="Tahoe_OSM_Streets_Dissolve",
    point_features="Tahoe_OSM_Streets_GeneratePointsAlongLines_HalfMile",
    out_feature_class="Tahoe_OSM_Streets_Split_HalfMileMax",
    search_radius="5 Meters"
)

# add fields for unique id and and miles
fc="Tahoe_OSM_Streets_Split_HalfMileMax"

# Specify the field name and data type
field_name = "Miles"
field_type = "DOUBLE"  # You can choose other data types like "INTEGER", "DOUBLE", etc.

# Add the field
arcpy.management.AddField(fc, field_name, field_type)

# Specify the field name and data type
field_name = "UniqueID"
field_type = "LONG"  # You can choose other data types like "INTEGER", "DOUBLE", etc.

# Add the field
arcpy.management.AddField(fc, field_name, field_type)

# calculate the new fields
arcpy.management.CalculateGeometryAttributes(
    in_features="Tahoe_OSM_Streets_Split_HalfMileMax",
    geometry_property="Miles LENGTH",
    length_unit="MILES_US",
    area_unit="",
    coordinate_system='PROJCS["NAD_1983_UTM_Zone_10N",GEOGCS["GCS_North_American_1983",DATUM["D_North_American_1983",SPHEROID["GRS_1980",6378137.0,298.257222101]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Transverse_Mercator"],PARAMETER["False_Easting",500000.0],PARAMETER["False_Northing",0.0],PARAMETER["Central_Meridian",-123.0],PARAMETER["Scale_Factor",0.9996],PARAMETER["Latitude_Of_Origin",0.0],UNIT["Meter",1.0]]',
    coordinate_format="SAME_AS_INPUT"
)

arcpy.management.CalculateField(
    in_table="Tahoe_OSM_Streets_Split_HalfMileMax",
    field="UniqueID",
    expression="!OBJECTID!",
    expression_type="PYTHON3",
    code_block="",
    field_type="TEXT",
    enforce_domains="NO_ENFORCE_DOMAINS"
)

# Export to Enterprise Geodatabase