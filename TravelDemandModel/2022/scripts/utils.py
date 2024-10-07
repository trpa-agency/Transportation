## A set of utility functions to help with the data processing and analysis
from pathlib import Path
import pandas as pd
#import plotly.express as px
from arcgis.features import FeatureLayer, GeoAccessor, GeoSeriesAccessor
import arcpy
import pytz
from datetime import datetime
from time import strftime 
# external connection packages
from sqlalchemy.engine import URL
from sqlalchemy import create_engine
import os

# check if field exists in data frame and final_schema and if not add it
def check_field(df, fields):
    for field in fields:
        if field not in df.columns:
            df[field] = np.nan
    return df

def get_conn(db):
    # Get database user and password from environment variables on machine running script
    db_user             = os.environ.get('DB_USER')
    db_password         = os.environ.get('DB_PASSWORD')

    # driver is the ODBC driver for SQL Server
    driver              = 'ODBC Driver 17 for SQL Server'
    # server names are
    sql_12              = 'sql12'
    sql_14              = 'sql14'
    # make it case insensitive
    db = db.lower()
    # make sql database connection with pyodbc
    if db   == 'sde_tabular':
        connection_string = f"DRIVER={driver};SERVER={sql_12};DATABASE={db};UID={db_user};PWD={db_password}"
        connection_url = URL.create("mssql+pyodbc", query={"odbc_connect": connection_string})
        engine = create_engine(connection_url)
    elif db == 'tahoebmpsde':
        connection_string = f"DRIVER={driver};SERVER={sql_14};DATABASE={db};UID={db_user};PWD={db_password}"
        connection_url = URL.create("mssql+pyodbc", query={"odbc_connect": connection_string})
        engine = create_engine(connection_url)
    elif db == 'sde':
        connection_string = f"DRIVER={driver};SERVER={sql_12};DATABASE={db};UID={db_user};PWD={db_password}"
        connection_url = URL.create("mssql+pyodbc", query={"odbc_connect": connection_string})
        engine = create_engine(connection_url)
    # else return None
    else:
        engine = None
    # connection file to use in pd.read_sql
    return engine

# Reads in csv file
def read_file(path_file):
    p = Path(path_file)
    p.expanduser()
    data = pd.read_csv(p, low_memory=False)
    return data

# Reads in excel file with sheet index
def read_excel(path_file, sheet_index=0):
    p = Path(path_file)
    p.expanduser()
    data = pd.read_excel(p, sheet_name=sheet_index)
    return data

# Gets feature service data as dataframe with query option
def get_fs_data_query(service_url, query_params):
    feature_layer = FeatureLayer(service_url)
    query_result = feature_layer.query(query_params)
    # Convert the query result to a list of dictionaries
    feature_list = query_result.features
    # Create a pandas DataFrame from the list of dictionaries
    all_data = pd.DataFrame([feature.attributes for feature in feature_list])
    # return data frame
    return all_data

# Gets feature service data as dataframe
def get_fs_data(service_url):
    feature_layer = FeatureLayer(service_url)
    query_result = feature_layer.query()
    # Convert the query result to a list of dictionaries
    feature_list = query_result.features
    # Create a pandas DataFrame from the list of dictionaries
    all_data = pd.DataFrame([feature.attributes for feature in feature_list])
    # return data frame
    return all_data

# # Gets feature service data as spatially enabled dataframe
# def get_fs_data_spatial(service_url):
#     feature_layer = FeatureLayer(service_url)
#     df = feature_layer.query().sdf
#     return df

# Gets feature service data as spatially enabled dataframe
def get_fs_data_spatial(service_url):
    feature_layer = FeatureLayer(service_url)
    sdf = pd.DataFrame.spatial.from_layer(feature_layer)
    return sdf

# Gets feature service as spatially enabled dataframe with query
def get_fs_data_spatial_query(service_url, query_params):
    feature_layer = FeatureLayer(service_url)
    sdf = feature_layer.query(query_params).sdf
    return sdf

# rename columns in a dataframe
def renamecolumns(df, column_mapping,drop_columns):
    if drop_columns:
        df = df.rename(columns=column_mapping).drop(columns=[col for col in df.columns if col not in column_mapping])
    else:
        df = df.rename(columns=column_mapping) 
    return df

# get geodatabase table as dataframe
def import_table_from_fgb(tablename):
    data = []
    # Use SearchCursor to iterate through the feature class
    fields = [field.name for field in arcpy.ListFields(tablename)]
    with arcpy.da.SearchCursor(tablename, fields) as cursor:
        for row in cursor:
            data.append(row)
    # Convert the list of tuples to a Pandas DataFrame
    df = pd.DataFrame(data, columns=fields)
    return df

# build a dictionary from a csv file of lookup values
def import_lookup_dictionary(lookup_csv, key_column, value_column, filter_column_1, filter_condition_1,filter_column_2, filter_condition_2):
    df = pd.read_csv(lookup_csv)
    filtered_df = df[(df[filter_column_1] == filter_condition_1)&(df[filter_column_2] == filter_condition_2)]
    dictionary = filtered_df.set_index(key_column)[value_column].to_dict()
    return dictionary

# update a field based on lookup value
def update_field_from_dictionary(df, df_lookup, field_name,filter_column_1,filter_condition_1,key_column, value_column, exact_match):
    filtered_lookup = df_lookup[(df_lookup[filter_column_1] == filter_condition_1)&
                                (df_lookup['Field_Name'] == field_name)]
    dictionary = filtered_lookup.set_index(key_column)[value_column].to_dict()
    if exact_match:
        df[field_name]=df[field_name].map(dictionary)
    else:
        df = update_if_contains(df, field_name,dictionary)
    return df

# update a field based on lookup value if it contains a key
def update_if_contains(df, column_to_update, lookup_dictionary):
    for key, value in lookup_dictionary.items():
        df.loc[df[column_to_update].str.contains(key), column_to_update] = value
    return df

# update a field inplace on lookup value if it contains a key
def update_if_contains_inplace(df, column_to_update, lookup_dictionary):
    for key, value in lookup_dictionary.items():
        df.loc[df[column_to_update].str.contains(key), column_to_update] = value

# update a feature class field based on another feature class field with the same key
def fieldJoinCalc(updateFC, updateFieldsList, sourceFC, sourceFieldsList):
    print ("Started data transfer: " + strftime("%Y-%m-%d %H:%M:%S"))
    # Use list comprehension to build a dictionary from arcpy SearchCursor  
    valueDict = {r[0]:(r[1:]) for r in arcpy.da.SearchCursor(sourceFC, sourceFieldsList)}  
    with arcpy.da.UpdateCursor(updateFC, updateFieldsList) as updateRows:  
        for updateRow in updateRows:  
            # store the Join value of the row being updated in a keyValue variable  
            keyValue = updateRow[0]  
            # verify that the keyValue is in the Dictionary  
            if keyValue in valueDict:  
                # transfer the value stored under the keyValue from the dictionary to the updated field.  
                updateRow[1] = valueDict[keyValue][0]  
                updateRows.updateRow(updateRow)    
    del valueDict  
    print ("Finished data transfer: " + strftime("%Y-%m-%d %H:%M:%S"))

# convert Unix timestamp to UTC datetime
def convert_to_utc(timestamp):
    return datetime.utcfromtimestamp(timestamp // 1000).replace(tzinfo=pytz.utc)

# function to merge dataframes and filter to records only in the left dataframe
def merge_dataframes(left_df, right_df, left_key, right_key):
    merged_df = pd.merge(left_df, right_df, how='left', left_on=left_key, right_on=right_key)
    return merged_df

# function to merge dataframe with outer join and indicator and keep rows where indicator is left_only
def merge_dataframes_left_only(left_df, right_df, left_key, right_key):
    merged_df = pd.merge(left_df, right_df, how='outer', left_on=left_key, right_on=right_key, indicator=True)
    return merged_df[merged_df['_merge'] == 'left_only']

# function to merge dataframe with outer join and indicator and keep rows where indicator is right_only
def merge_dataframes_right_only(left_df, right_df, left_key, right_key):
    merged_df = pd.merge(left_df, right_df, how='outer', left_on=left_key, right_on=right_key, indicator=True)
    return merged_df[merged_df['_merge'] == 'right_only']

# function to merge dataframe with outer join and indicator and keep rows where indicator is both
def merge_dataframes_both(left_df, right_df, left_key, right_key):
    merged_df = pd.merge(left_df, right_df, how='outer', left_on=left_key, right_on=right_key, indicator=True)
    return merged_df[merged_df['_merge'] == 'both']


# function to merge dataframes and filter to records only in the right dataframe
def merge_dataframes_right(left_df, right_df, left_key, right_key):
    merged_df = pd.merge(left_df, right_df, how='right', left_on=left_key, right_on=right_key)
    return merged_df

# function to merge dataframes and filter to records in both dataframes
def merge_dataframes_inner(left_df, right_df, left_key, right_key):
    merged_df = pd.merge(left_df, right_df, how='inner', left_on=left_key, right_on=right_key)
    return merged_df

# function to merge dataframes and filter to records in either dataframe
def merge_dataframes_outer(left_df, right_df, left_key, right_key):
    merged_df = pd.merge(left_df, right_df, how='outer', left_on=left_key, right_on=right_key)
    return merged_df

# TAZ Crosswalk function
def make_taz_crosswalk(parcel_fc, taz_fc, geography_fc):
        # Define in-memory feature class names
    geo_feature_class = r"memory\geo"
    taz_feature_class = r"memory\taz_geo"

    # Perform first spatial join - order doesn't matter
    arcpy.analysis.SpatialJoin(
        target_features=parcel_fc,
        join_features=taz_fc,
        out_feature_class=taz_feature_class,
        join_operation="JOIN_ONE_TO_MANY",
        join_type="KEEP_ALL",
        match_option="HAVE_THEIR_CENTER_IN"
    )

    # Perform second spatial join
    arcpy.analysis.SpatialJoin(
        target_features=taz_feature_class,
        join_features=geography_fc,
        out_feature_class=geo_feature_class,
        join_operation="JOIN_ONE_TO_MANY",
        join_type="KEEP_ALL",
        match_option="HAVE_THEIR_CENTER_IN"
    )

    # Convert the final joined feature class to a Spatially enabled DataFrame
    sdf_taz_geo = pd.DataFrame.spatial.from_featureclass(geo_feature_class)

    # Select and rename necessary columns
    sdf_taz_geo = sdf_taz_geo[['APN', 'GEOID', 'TRPAID', 'TAZ_1', 'Residential_Units',
                            'TouristAccommodation_Units', 'CommercialFloorArea_SqFt']]
    sdf_taz_geo = sdf_taz_geo.rename(columns={'TAZ_1': 'TAZ'})

    # Group by and aggregate data
    df_parcels_grouped = sdf_taz_geo.groupby(['TAZ', 'TRPAID']).agg({'Residential_Units': 'sum',
                                                                    'TouristAccommodation_Units': 'sum',
                                                                    'CommercialFloorArea_SqFt': 'sum'}).reset_index()

    # Calculate totals and proportions
    df_parcels_grouped['Total_Res_Units'] = df_parcels_grouped.groupby('TAZ')['Residential_Units'].transform('sum')
    df_parcels_grouped['Total_TA_Units'] = df_parcels_grouped.groupby('TAZ')['TouristAccommodation_Units'].transform('sum')
    df_parcels_grouped['Total_CommercialFloorArea_SqFt'] = df_parcels_grouped.groupby('TAZ')['CommercialFloorArea_SqFt'].transform('sum')
    
    # Calculate proportions with checks for zero totals
    df_parcels_grouped['Residential_Units_Proportion'] = df_parcels_grouped.apply(
        lambda row: row['Residential_Units'] / row['Total_Res_Units'] if row['Total_Res_Units'] != 0 else 0, axis=1
    )
    df_parcels_grouped['TouristAccommodation_Units_Proportion'] = df_parcels_grouped.apply(
        lambda row: row['TouristAccommodation_Units'] / row['Total_TA_Units'] if row['Total_TA_Units'] != 0 else 0, axis=1
    )
    df_parcels_grouped['CommercialFloorArea_SqFt_Proportion'] = df_parcels_grouped.apply(
        lambda row: row['CommercialFloorArea_SqFt'] / row['Total_CommercialFloorArea_SqFt'] if row['Total_CommercialFloorArea_SqFt'] != 0 else 0, axis=1
    )

 
    # Fill NaN values with 0
    df_parcels_grouped.fillna(0, inplace=True)
    return df_parcels_grouped