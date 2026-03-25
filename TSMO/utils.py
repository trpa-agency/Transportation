import pandas as pd
import numpy as np
from arcgis import GIS
from arcgis.features import FeatureLayer
import arcpy
from datetime import datetime
# Decode a Google-encoded polyline string into a list of (lat, lon) tuples
def decode_polyline(encoded):
    points = []
    index = lat = lng = 0
    while index < len(encoded):
        result, shift = 0, 0
        while True:
            b = ord(encoded[index]) - 63
            index += 1
            result |= (b & 0x1F) << shift
            shift += 5
            if b < 0x20:
                break
        lat += (~(result >> 1) if result & 1 else result >> 1)
        result, shift = 0, 0
        while True:
            b = ord(encoded[index]) - 63
            index += 1
            result |= (b & 0x1F) << shift
            shift += 5
            if b < 0x20:
                break
        lng += (~(result >> 1) if result & 1 else result >> 1)
        points.append((lat / 1e5, lng / 1e5))
    return points

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

# write a dataframe to a geodatabase table
def df_to_gdb_table(df, table_path):
    if arcpy.Exists(table_path):
        arcpy.management.Delete(table_path)
    df = df.copy()
    dtypes = []
    for col in df.columns:
        if df[col].dtype == object:
            max_len = df[col].fillna('').astype(str).str.len().max()
            max_len = max(int(max_len), 1)
            df[col] = df[col].fillna('').astype(str)
            dtypes.append((col, f'U{max_len}'))
        elif df[col].dtype in ('float64', 'float32'):
            df[col] = df[col].fillna(0)
            dtypes.append((col, '<f8'))
        elif df[col].dtype == 'int64':
            df[col] = df[col].fillna(0).astype(np.int64)
            dtypes.append((col, '<i8'))
        elif df[col].dtype == 'int32':
            df[col] = df[col].fillna(0).astype(np.int32)
            dtypes.append((col, '<i4'))
        else:
            df[col] = df[col].fillna('').astype(str)
            dtypes.append((col, 'U255'))
    arr = np.array([tuple(row) for row in df.itertuples(index=False)], dtype=dtypes)
    arcpy.da.NumPyArrayToTable(arr, table_path)

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

