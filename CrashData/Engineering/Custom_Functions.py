import pandas as pd
import numpy as np
import arcpy

def renamecolumns(df, column_mapping,drop_columns):
    if drop_columns:
        df = df.rename(columns=column_mapping).drop(columns=[col for col in df.columns if col not in column_mapping])
    else:
        df = df.rename(columns=column_mapping) 
    return df

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

def import_lookup_dictionary(lookup_csv, key_column, value_column, filter_column_1, filter_condition_1,filter_column_2, filter_condition_2):
    df = pd.read_csv(lookup_csv)
    filtered_df = df[(df[filter_column_1] == filter_condition_1)&(df[filter_column_2] == filter_condition_2)]
    dictionary = filtered_df.set_index(key_column)[value_column].to_dict()
    return dictionary

def update_field_from_dictionary(df, df_lookup, field_name,filter_column_1,filter_condition_1,key_column, value_column, exact_match):
    filtered_lookup = df_lookup[(df_lookup[filter_column_1] == filter_condition_1)&
                                (df_lookup['Field_Name'] == field_name)]
    dictionary = filtered_lookup.set_index(key_column)[value_column].to_dict()
    if not dictionary:
        print(f"WARNING: No lookup keys found for field '{field_name}' where {filter_column_1} == '{filter_condition_1}'")
        return df
    if exact_match:
        # Normalize keys and values so the match ignores capitalization and extra whitespace
        normalized_dictionary = {str(k).strip().lower(): v for k, v in dictionary.items()}
        normalized_values = df[field_name].astype(str).str.strip().str.lower()
        unmatched = df[field_name].notna() & ~normalized_values.isin(normalized_dictionary.keys())
        warn_unmatched(df.loc[unmatched, field_name], field_name)
        df[field_name]=normalized_values.map(normalized_dictionary)
    else:
        df = update_if_contains(df, field_name,dictionary)
    return df

def update_if_contains(df, column_to_update, lookup_dictionary):
    matched = pd.Series(False, index=df.index)
    original_values = df[column_to_update].copy()
    for key, value in lookup_dictionary.items():
        mask = df[column_to_update].astype(str).str.contains(key, case=False, na=False)
        df.loc[mask, column_to_update] = value
        matched |= mask
    unmatched = original_values.notna() & ~matched
    warn_unmatched(original_values[unmatched], column_to_update)
    return df

def warn_unmatched(unmatched_values, field_name):
    # Print a warning listing values that had no matching key in the lookup
    if unmatched_values.empty:
        return
    unique_values = unmatched_values.unique()
    print(f"WARNING: {len(unmatched_values)} rows in '{field_name}' had no matching lookup key "
          f"({len(unique_values)} unique values): {list(unique_values)}")
def fieldJoinCalc(updateFC, updateFieldsList, sourceFC, sourceFieldsList):
    from time import strftime  
    print ("Started data transfer: " + strftime("%Y-%m-%d %H:%M:%S"))
#     log.info("Started data transfer: " + strftime("%Y-%m-%d %H:%M:%S"))
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
#     log.info("Finished data transfer: " + strftime("%Y-%m-%d %H:%M:%S"))
    
def update_if_contains_inplace(df, column_to_update, lookup_dictionary):
    for key, value in lookup_dictionary.items():
        df.loc[df[column_to_update].astype(str).str.contains(key, case=False, na=False), column_to_update] = value

    # Set values to the specified fill_value for keys not found in the dictionary
    # Default value is null
    #df.loc[~df[column_to_update].isin(lookup_dictionary.keys()), column_to_update] = fill_value

