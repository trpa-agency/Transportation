"""CrashAnalysis_HighInjuryNetwork.py
    Created data:
    Last Updated:
    Contac:
"""

# import packages
import arcpy
import os
from arcgis.features import FeatureLayer
import pandas as pd

# set overwrite to true
arcpy.env.overwriteOutput = True

# enterprise Geodatabase connection
sdeBase = "F:\GIS\DB_CONNECT\Vector.sde"

# set workspace - Need to modify this to be universal
arcpy.env.workspace = "F:\GIS\PROJECTS\Transportation\Vision Zero\CrashAnalysis\Crash Analysis.gdb"
geodatabase         = r"F:\GIS\PROJECTS\Transportation\Vision Zero\CrashAnalysis\Crash Analysis.gdb"

# in memory output file path
memory_workspace = "memory" + "\\"

# input fcs
streetNetwork = "Tahoe_OSM_Streets_Split_HalfMileMax"
crashData = "Tahoe_Crash"
# output fc
output_feature_class = "Tahoe_OSM_Streets_Crashes"

# List of input and join field names
input_field_names = ["UniqueID", "Shape_Length",  
                     "CrashRate", "Miles", "FatalityRate"]

join_field_names = ["Num_Killed", "Num_Injured", "Num_Ped_Killed", "Num_Ped_Injured", 
                    "Num_Bicyclist_Killed", "Num_Bicyclist_Injured", 
                    "Crash_Severity_Numeric", "Crash_Rate_Weighted",
                    "Bicycle_Involved_Numeric", "Pedestrian_Involved_Numeric"]

# crash data rest endpoint
map_service_url = 'https://maps.trpa.org/server/rest/services/LTInfo_Monitoring/MapServer/108'

# Create a feature layer object
feature_layer = FeatureLayer(map_service_url)

# Query the features and convert them to a spatially enabled DataFrame
sdf = pd.DataFrame.spatial.from_layer(feature_layer)

# Save the spatially enabled DataFrame to a geodatabase
sdf.spatial.to_featureclass(location=os.path.join(geodatabase, crashData), sanitize_columns= False)
print("Data has been saved to the geodatabase.")

# Functions
# get weighted value as numeric
def crash_severity_numeric(field1_value, field2_value, field3_value):
    if field1_value == 'Fatal':
        return 5
    elif field1_value == 'Severe injury':
        return 3
    elif field2_value == 'Y':
        return 2
    elif field3_value == 'Y':
        return 2
    else:
        return 1  # Default value for other cases
    
# assign threhsold
def assign_value(row, threshold):
    if row['Miles'] > threshold:
        return 'above_threshold'
    else:
        return 'below_threshold'

# segments to HIN based on victim threshold
def identify_HIN_segments(df, segment_threshold, victim_field, unique_id_field, rank_fields):
    df['threshold_status']=df.apply(assign_value, args=(segment_threshold,), axis = 1)
    #Sort the rows by the relevant fields (crash rate and numeric crash severity)
    df_sorted = df.sort_values(by=rank_fields, ignore_index = True, ascending = False)
    total_victims = df_sorted[victim_field].sum()
    #remove rows that are below the chosen length threshold
    df_sorted = df_sorted.loc[df_sorted['threshold_status']=='above_threshold']
    #Get the cumulative number of victims
    df_sorted['Cumulative_Victims'] = df_sorted[victim_field].cumsum()
    #Group them by the rankings and then return the minimum of the group so if any segment that is exactly tied matches 
    #they will all be included
    df_sorted['Grouped_Cumulative_Victims_Min']=df_sorted.groupby(rank_fields)['Cumulative_Victims'].transform('min')
    #Filter down to just ones to get to .65
    df_HIN = df_sorted[df_sorted['Grouped_Cumulative_Victims_Min']<= (.65 * total_victims)]
    #Sum up the totals of the filtered records and divide by total. 
    #This number would ideally be very close to .65
    percent_included = df_HIN[victim_field].sum()/total_victims
    #Get the threshold values for inclusion within the HIN 
    threshold = df_HIN[rank_fields].min()
    threshold_1 = threshold[0]
    threshold_2 = threshold[1]
    #Get a list of all ids to be included
    HIN_IDs = df_HIN[unique_id_field]

    return HIN_IDs, percent_included, threshold_1, threshold_2     
# coded value fields to capture which segments are in the HIN for each mode
def addHIN(fc, idList, field_name):
    # Update the new field based on presence in the list of Object IDs
    with arcpy.da.UpdateCursor(fc, ['UniqueID', field_name]) as cursor:
        for row in cursor:
            value = row[0]
            if value in idList.values:
                row[1] = 1
            else:
                row[1] = 0   
            cursor.updateRow(row)

### TRANSFORM DATA ###
arcpy.AddField_management("Tahoe_Crash", 'Crash_Severity_Numeric', "LONG")
arcpy.AddField_management("Tahoe_Crash", 'Crash_Rate_Weighted', "DOUBLE")
# Use CalculateField_management to apply the function to the new field
expression = "crash_severity_numeric(!Crash_Severity!, !Bicycle_Involved!, !Pedestrian_Involved!)"  
code_block = """def crash_severity_numeric(field1_value, field2_value, field3_value):
    if field1_value == 'Fatal':
        return 5
    elif field1_value == 'Severe injury':
        return 3
    elif field2_value == 'Y':
        return 2
    elif field3_value == 'Y':
        return 2
    else:
        return 1 """  # Define the function here

# 
arcpy.CalculateField_management("Tahoe_Crash", 
                                "Crash_Severity_Numeric",
                                expression, "PYTHON3", code_block)
print("Calculation complete.")

#
arcpy.AddField_management("Tahoe_Crash", 
                          'Bicycle_Involved_Numeric', "LONG")
expression = "crash_severity_numeric(!Bicycle_Involved!)" 
code_block = """def crash_severity_numeric(field1_value):
    if field1_value == 'Y':
        return 1
    else:
        return 0 """  # Define the function here

#
arcpy.CalculateField_management("Tahoe_Crash", 
                                "Bicycle_Involved_Numeric", 
                                expression, "PYTHON3", code_block)
print("Calculation complete.")

#
arcpy.AddField_management("Tahoe_Crash", 'Pedestrian_Involved_Numeric', "LONG")
expression = "crash_severity_numeric(!Pedestrian_Involved!)" 
code_block = """def crash_severity_numeric(field1_value):
    if field1_value == 'Y':
        return 1
    else:
        return 0 """  # Define the function here

#
arcpy.CalculateField_management("Tahoe_Crash", 
                                "Pedestrian_Involved_Numeric", 
                                expression, "PYTHON3", code_block)

print("Calculation complete.")

# Snap Tahoe Crash feature class to Streets network
arcpy.edit.Snap(
    in_features="Tahoe_Crash",
    snap_environment="Tahoe_OSM_Streets EDGE '0.25 Miles'"
)
print("Snap complete.")

# List of fields to be joined using SUM
fields_to_sum = ["Num_Killed", "Num_Injured", "Num_Ped_Killed", 
                 "Num_Ped_Injured", 
                 "Num_Bicyclist_Killed", "Num_Bicyclist_Injured", 
                 "Crash_Severity_Numeric",
                "Bicycle_Involved_Numeric", "Pedestrian_Involved_Numeric"]

# Create a field map object
field_mappings = arcpy.FieldMappings()

# Get the field info for the target feature class
target_field_info = arcpy.ListFields(streetNetwork)

# Add fields from the target feature class to the field mappings
for field in target_field_info:
    if field.name in input_field_names:
        input_field_map = arcpy.FieldMap()
        input_field_map.addInputField(streetNetwork, 
                                      field.name)
        # Set the merge rule to SUM for selected fields
        if field.name in fields_to_sum:
            input_field_map.mergeRule = "SUM"
        
        field_mappings.addFieldMap(input_field_map)

# Get the field info for the join feature class
join_field_info = arcpy.ListFields(crashData)

# Add fields from the join feature class to the field mappings
for field in join_field_info:
    if field.name in join_field_names:
        join_field_map = arcpy.FieldMap()
        join_field_map.addInputField(crashData, 
                                     field.name)
        # Set the merge rule to SUM for selected fields
        if field.name in fields_to_sum:
            join_field_map.mergeRule = "SUM"
        field_mappings.addFieldMap(join_field_map)

# Add a field map for the number_of_records field (count of a specific field)
num_records_field_map = arcpy.FieldMap()
num_records_field_map.addInputField(crashData, "County")
num_records_output_field = num_records_field_map.outputField
num_records_output_field.name = "Number_Of_Crashes"  # Change to your desired field name
num_records_output_field.aliasName = "Number Of Crashes"
num_records_output_field.type = "LONG"  # Change to appropriate data type
num_records_field_map.outputField = num_records_output_field
num_records_field_map.mergeRule = "COUNT"
field_mappings.addFieldMap(num_records_field_map)
print("field mappings complete for spatial join")

# Perform the spatial join using the specified field mappings
arcpy.analysis.SpatialJoin(streetNetwork, 
    crashData, 
    output_feature_class,
    join_operation="JOIN_ONE_TO_ONE",
    join_type="KEEP_ALL",
    field_mapping = field_mappings,
    match_option="INTERSECT",
    search_radius=None,
    distance_field_name="")
print("Spatial Join of crashes to streets complete.")

arcpy.management.CalculateField(
    in_table= output_feature_class,
    field="Miles",
    expression="!Shape_Length! *  0.000621371",
    expression_type="PYTHON3",
    code_block="",
    enforce_domains="NO_ENFORCE_DOMAINS"
)
print("Miles Calculation complete.")

arcpy.management.CalculateField(
    in_table=output_feature_class,
    field="Crash_Severity_Numeric",
    expression="0 if !Crash_Severity_Numeric! == None else !Crash_Severity_Numeric!",
    expression_type="PYTHON3",
    code_block="",
    field_type="FLOAT",
    enforce_domains="NO_ENFORCE_DOMAINS"
)
print("Crash_Severity_Numeric Calculation complete.")

arcpy.management.CalculateField(
    in_table=output_feature_class,
    field="Pedestrian_Involved_Numeric",
    expression="0 if !Pedestrian_Involved_Numeric! == None else !Pedestrian_Involved_Numeric!",
    expression_type="PYTHON3",
    code_block="",
    field_type="FLOAT",
    enforce_domains="NO_ENFORCE_DOMAINS"
)
print("Pedestrian_Involved_NumericCalculation complete.")

arcpy.management.CalculateField(
    in_table=output_feature_class,
    field="Bicycle_Involved_Numeric",
    expression="0 if !Bicycle_Involved_Numeric! == None else !Bicycle_Involved_Numeric!",
    expression_type="PYTHON3",
    code_block="",
    field_type="FLOAT",
    enforce_domains="NO_ENFORCE_DOMAINS"
)
print("Bicycle_Involved_Numeric Calculation complete.")

arcpy.management.CalculateField(
    in_table=output_feature_class,
    field="Number_Of_Crashes",
    expression="0 if !Number_Of_Crashes! == None else !Number_Of_Crashes!",
    expression_type="PYTHON3",
    code_block="",
    field_type="FLOAT",
    enforce_domains="NO_ENFORCE_DOMAINS"
)
print("Number_Of_Crashes Calculation complete.")

arcpy.management.CalculateField(
    in_table=output_feature_class,
    field="Crash_Rate_Weighted",
    expression="int(!Crash_Severity_Numeric!) / (!Miles!*8)",
    expression_type="PYTHON3",
    code_block="",
    enforce_domains="NO_ENFORCE_DOMAINS"
)
print("Crash_Rate_Weighted Calculation complete.")

arcpy.management.CalculateField(
    in_table=output_feature_class,
    field="Crash_Rate_Ped",
    expression="!Pedestrian_Involved_Numeric! / (!Miles!*8)",
    expression_type="PYTHON3",
    code_block="",
    enforce_domains="NO_ENFORCE_DOMAINS"
)
print("Crash_Rate_Ped Calculation complete.")

arcpy.management.CalculateField(
    in_table=output_feature_class,
    field="Crash_Rate_Bike",
    expression="!Bicycle_Involved_Numeric! / (!Miles!*8)",
    expression_type="PYTHON3",
    code_block="",
    enforce_domains="NO_ENFORCE_DOMAINS"
)
print("Crash_Rate_Bike Calculation complete.")

arcpy.management.CalculateField(
    in_table=output_feature_class,
    field="Crash_Rate_Total",
    expression="!Number_Of_Crashes! / (!Miles!*8)",
    expression_type="PYTHON3",
    code_block="",
    enforce_domains="NO_ENFORCE_DOMAINS"
)
print("Crash_Rate_Total calculation complete.")

# add fields for HIN totals
arcpy.AddField_management(output_feature_class, 'ped_HIN_0', "SHORT")
arcpy.AddField_management(output_feature_class, 'ped_HIN_05', "SHORT")
arcpy.AddField_management(output_feature_class, 'ped_HIN_tenth', "SHORT")
arcpy.AddField_management(output_feature_class, 'bike_HIN_0', "SHORT")
arcpy.AddField_management(output_feature_class, 'bike_HIN_tenth', "SHORT")
arcpy.AddField_management(output_feature_class, 'bike_HIN_05', "SHORT")
arcpy.AddField_management(output_feature_class, 'car_HIN_0', "SHORT")
arcpy.AddField_management(output_feature_class, 'car_HIN_tenth', "SHORT")
arcpy.AddField_management(output_feature_class, 'car_HIN_05', "SHORT")
print("HIN fields added.")

# totals of victims per mile/mode
#Convert feature class to dataframe
crash_df = pd.DataFrame.spatial.from_featureclass(output_feature_class)
Summary_Fields = ['Num_Killed', 'Num_Injured', 'Num_Ped_Killed','Num_Ped_Injured', 'Num_Bicyclist_Killed', 'Num_Bicyclist_Injured']

crash_df[Summary_Fields]= crash_df[Summary_Fields].fillna(0)
crash_df['Total_Victims'] = crash_df['Num_Killed'] + crash_df['Num_Injured']
crash_df['Total_Ped'] = crash_df['Num_Ped_Killed'] +crash_df['Num_Ped_Injured']
crash_df['Total_Bicyclist'] = crash_df['Num_Bicyclist_Killed'] + crash_df['Num_Bicyclist_Injured']
crash_df['Total_Car'] = crash_df['Total_Victims'] - (crash_df['Total_Ped'] + crash_df['Total_Bicyclist'])
crash_df['Victims_Per_Mile'] = crash_df['Total_Victims']/crash_df['Miles']
crash_df['Car_Victims_Per_Mile']  =crash_df['Total_Car']/crash_df['Miles']
crash_df['Bike_Victims_Per_Mile'] =crash_df['Total_Bicyclist']/crash_df['Miles']
crash_df['Ped_Victims_Per_Mile']  =crash_df['Total_Ped']/crash_df['Miles']
print("Pandas to get HIN segments...")

# run for different segment lenghth thresholds and for mode types
#Bring in csv to dataframe with variable values
#Iterate through the dataframe and make a new dataframe that contains results
parameter_df = pd.read_csv('HIN_Parameters.csv')
result_column_names = ['HIN_IDs','Percent_Included','Threshold_Value_1','Threshold_Value_2']
HIN_df = pd.concat([parameter_df, parameter_df.apply(lambda row: pd.Series(identify_HIN_segments(crash_df,row['Segment_Threshold'], 
                                                                                                 row['Victim_Field'], 'UniqueID',
                                                                                                 [row['Rank_Field_1'],row['Rank_Field_2']])), axis=1)], axis=1)
# Rename the result columns
HIN_df.columns = list(parameter_df.columns) + result_column_names

#Use the results dataframe to add the HIN fields to the crash feature class
HIN_df.apply(lambda row:pd.Series(addHIN(output_feature_class,row['HIN_IDs'],row['HIN_Name'])),axis=1)
results_df = HIN_df.drop('HIN_IDs', axis=1)
results_df.to_csv('results.csv')

print("Done adding HIN")

# create stacked HIN by mode
# We have a list of ID's for each HIN
# Create a new feature class and append each of those segments to it with an additional field populated with the field name

existing_fc = "Tahoe_OSM_Streets_Crashes"

# Define the path to the new feature class that will store the unpivoted data
new_fc_name = "High_Injury_Network_ModeStacked"

# List of fields to unpivot
fields_to_unpivot = ["ped_HIN_0",
                    "ped_HIN_05",
                    "ped_HIN_tenth",
                    "bike_HIN_0",
                    "bike_HIN_05",
                    "bike_HIN_tenth",
                    "car_HIN_0",
                    "car_HIN_05",
                    "car_HIN_tenth"]


# List of fields to keep from the original feature class
fields_to_keep = ["UniqueID",
                "Miles"
                ,"Num_Killed"
                ,"Num_Injured"
                ,"Num_Ped_Killed"
                ,"Num_Ped_Injured"
                ,"Num_Bicyclist_Killed"
                ,"Num_Bicyclist_Injured"
                ,"Crash_Severity_Numeric"
                ,"Crash_Rate_Weighted"
                ,"Bicycle_Involved_Numeric"
                ,"Pedestrian_Involved_Numeric"
                ,"Number_Of_Crashes"
                ,"Crash_Rate_Ped"
                ,"Crash_Rate_Bike"
                ,"Crash_Rate_Total"]

# Get the coordinate system from the existing feature class
desc = arcpy.Describe(existing_fc)
spatial_reference = desc.spatialReference

# Create a new polyline feature class to store the unpivoted data
arcpy.CreateFeatureclass_management(arcpy.env.workspace, new_fc_name, "POLYLINE", spatial_reference=spatial_reference)

# Add fields to the new feature class for the values, field names, and fields to keep
for field in fields_to_keep:
    field_info = arcpy.ListFields(existing_fc, field)[0]
    arcpy.AddField_management(new_fc_name, field, field_info.type, field_info.precision, field_info.scale, field_info.length)


arcpy.AddField_management(new_fc_name, "Value", "TEXT")
arcpy.AddField_management(new_fc_name, "HIN_Type", "TEXT")


# Use an insert cursor to add unpivoted features to the new feature class
with arcpy.da.InsertCursor(new_fc_name, ["SHAPE@", "Value", "HIN_Type", *fields_to_keep]) as cursor:
    # Use a search cursor to iterate through the existing features
    with arcpy.da.SearchCursor(existing_fc, ["SHAPE@", *fields_to_unpivot, *fields_to_keep]) as search_cursor:
        for row in search_cursor:
            # For each field to unpivot, add a new feature with the value and field name
            for field_name in fields_to_unpivot:
                value = str(row[fields_to_unpivot.index(field_name) + 1])  # Get the field value
                field_name = field_name  # Get the field name
                if value == '1':
                    cursor.insertRow((row[0], value, field_name, *row[len(fields_to_unpivot)+1:]))

print("Polyline feature class has been stacked while keeping selected fields.")