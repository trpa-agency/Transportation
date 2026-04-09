## A set of utility functions to help with the data processing and analysis
from pathlib import Path
import pandas as pd
import plotly.express as px
from arcgis.features import FeatureLayer, GeoAccessor, GeoSeriesAccessor
import arcpy
import pytz
from datetime import datetime
from time import strftime
import os
import pathlib
from pathlib import Path


import numpy as np
import pickle
# external connection packages
from sqlalchemy.engine import URL
from sqlalchemy import create_engine

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

# Trendline
def trendline(
    df,
    path_html,
    div_id,
    x,
    y,
    color,
    color_sequence,
    sort,
    orders,
    x_title,
    y_title,
    format,
    hovertemplate,
    markers,
    hover_data,
    tickvals,
    ticktext,
    tickangle,
    hovermode,
    custom_data,
    additional_formatting=None,
):
    df = df.sort_values(by=sort)
    config = {"displayModeBar": False}
    fig = px.line(
        df,
        x=x,
        y=y,
        color=color,
        color_discrete_sequence=color_sequence,
        category_orders=orders,
        markers=markers,
        hover_data=hover_data,
        custom_data=custom_data,
    )
    fig.update_layout(
        yaxis=dict(title=y_title),
        xaxis=dict(title=x_title, showgrid=False),
        hovermode=hovermode,
        template="plotly_white",
        dragmode=False,
        legend_title=None,
    )
    fig.update_traces(hovertemplate=hovertemplate)
    fig.update_yaxes(tickformat=format)
    fig.update_xaxes(
        tickvals=tickvals,
        ticktext=ticktext,
        tickangle=tickangle,
    )
    fig.update_layout(additional_formatting)
    fig.write_html(
        config=config,
        file=path_html,
        include_plotlyjs="directory",
        div_id=div_id,
    )


# Stacked Percent Bar chart
def stackedbar(
    df,
    path_html,
    div_id,
    x,
    y,
    color,
    color_sequence,
    orders,
    y_title,
    x_title,
    custom_data,
    hovertemplate,
    hovermode,
    format,
    name=None,
    additional_formatting=None,
    orientation=None,
    facet=None,
    facet_row=None,
):
    config = {"displayModeBar": False}
    fig = px.bar(
        df,
        x=x,
        y=y,
        color=color,
        barmode="stack",
        facet_col=facet,
        facet_row=facet_row,
        color_discrete_sequence=color_sequence,
        category_orders=orders,
        orientation=orientation,
        custom_data=custom_data,
    )

    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))

    fig.update_layout(
        yaxis=dict(tickformat=format, hoverformat=format, title=y_title),
        xaxis=dict(title=x_title),
        hovermode=hovermode,
        template="plotly_white",
        dragmode=False,
        legend_title=None,
    )
    fig.for_each_yaxis(lambda yaxis: yaxis.update(showticklabels=True, tickformat=format))
    # fig.for_each_yaxis(lambda yaxis: yaxis.update(tickfont = dict(color = 'rgba(0,0,0,0)')), secondary_y=True)
    fig.update_yaxes(
        col=2, row=1, showticklabels=False, tickfont=dict(color="rgba(0,0,0,0)"), title=None
    )
    fig.update_yaxes(
        col=3, row=1, showticklabels=False, tickfont=dict(color="rgba(0,0,0,0)"), title=None
    )
    fig.update_xaxes(tickformat=".0f")
    fig.update_traces(hovertemplate=hovertemplate)
    fig.update_layout(additional_formatting)

    fig.write_html(
        config=config,
        file=path_html,
        include_plotlyjs="directory",
        div_id=div_id,
    )

# Helper function to transform regular data to sankey format
# Returns data and layout as dictionary
def genSankey(df,category_cols=[],value_cols='',title='Sankey Diagram'):
    # maximum of 6 value cols -> 6 colors
    colorPalette = ['#4B8BBE','#306998','#FFE873','#FFD43B','#646464']
    labelList = []
    colorNumList = []
    for catCol in category_cols:
        labelListTemp =  list(set(df[catCol].values))
        colorNumList.append(len(labelListTemp))
        labelList = labelList + labelListTemp
        
    # remove duplicates from labelList
    labelList = list(dict.fromkeys(labelList))
    
    # define colors based on number of levels We probab
    colorList = []
    for idx, colorNum in enumerate(colorNumList):
        colorList = colorList + [colorPalette[idx]]*colorNum
        
    # transform df into a source-target pair
    for i in range(len(category_cols)-1):
        if i==0:
            sourceTargetDf = df[[category_cols[i],category_cols[i+1],value_cols]]
            sourceTargetDf.columns = ['source','target','count']
        else:
            tempDf = df[[category_cols[i],category_cols[i+1],value_cols]]
            tempDf.columns = ['source','target','count']
            sourceTargetDf = pd.concat([sourceTargetDf,tempDf])
        sourceTargetDf = sourceTargetDf.groupby(['source','target']).agg({'count':'sum'}).reset_index()
        
    # add index for source-target pair
    sourceTargetDf['sourceID'] = sourceTargetDf['source'].apply(lambda x: labelList.index(x))
    sourceTargetDf['targetID'] = sourceTargetDf['target'].apply(lambda x: labelList.index(x))
    
    # creating the sankey diagram
    data = dict(
        type='sankey',
        node = dict(
          pad = 15,
          thickness = 20,
          line = dict(
            color = "black",
            width = 0.5
          ),
          label = labelList,
          color = colorList
        ),
        link = dict(
          source = sourceTargetDf['sourceID'],
          target = sourceTargetDf['targetID'],
          value = sourceTargetDf['count']
        )
      )
    
    layout =  dict(
        title = title,
        font = dict(
          size = 10
        )
    )
       
    fig = dict(data=[data], layout=layout)
    return fig

# function to forecast units on vacant parcels
def forecast_residential_units(df, condition, target_sum, reason):
    # filter to parcels available for development
    sdfAvailable = df.loc[eval(condition)]
    running_sum = 0
    rows_to_fill = []
    # Loop through the rows and fill the 'new_column'
    for idx, row in sdfAvailable.iterrows():
        # Calculate the remaining amount that can be filled
        remaining_amount = target_sum - running_sum
        if row['MAX_UNITS'] <= remaining_amount:
            # If the current row's value fits, add it to the column
            df.loc[idx, 'FORECASTED_RESIDENTIAL_UNITS'] = row['MAX_UNITS']
            running_sum += row['MAX_UNITS']
            if row['MAX_UNITS'] > 0:
                rows_to_fill.append(idx)
            if row['MAX_UNITS'] == remaining_amount:
                break
        elif remaining_amount > 0:
            # If it exceeds the remaining amount, fill with the remaining value
            df.loc[idx, 'FORECASTED_RESIDENTIAL_UNITS'] = remaining_amount
            running_sum += remaining_amount
            if row['MAX_UNITS'] > 0:
                rows_to_fill.append(idx)
            break
        else:
            continue
    # reason for development
    df.loc[rows_to_fill, 'FORECAST_REASON'] = reason
    df_summary = pd.DataFrame({'Reason': [reason], 'Parcels_Available':[len(sdfAvailable)], 'Parcels_Used':[len(rows_to_fill)],
                                'Total_Forecasted_Units': [running_sum], 'Total_Remaining_Units': [target_sum - running_sum]})   
    return df, df_summary  

# build a function to forecast residential units for infill parcels
def forecast_residential_units_infill(df, condition, target_sum, reason):
    # filter to parcels available for development
    sdfAvailable = df.loc[eval(condition)]
    running_sum = 0
    rows_to_fill = []
    # Loop through the rows and fill the 'new_column'
    for idx, row in sdfAvailable.iterrows():
        # Calculate the remaining amount that can be filled
        remaining_amount = target_sum - running_sum
        if row['POTENTIAL_UNITS'] <= remaining_amount:
            # If the current row's value fits, add it to the column
            df.loc[idx, 'FORECASTED_RESIDENTIAL_UNITS'] = row['POTENTIAL_UNITS']
            running_sum += row['POTENTIAL_UNITS']
            if row['POTENTIAL_UNITS'] > 0:
                rows_to_fill.append(idx)
            if row['POTENTIAL_UNITS'] == remaining_amount:
                break
        elif remaining_amount > 0:
            # If it exceeds the remaining amount, fill with the remaining value
            df.loc[idx, 'FORECASTED_RESIDENTIAL_UNITS'] = remaining_amount
            running_sum += remaining_amount
            if row['POTENTIAL_UNITS'] > 0:
                rows_to_fill.append(idx)
            break
        else:
            continue
    # reason for development
    df.loc[rows_to_fill, 'FORECAST_REASON'] = reason
    df_summary = pd.DataFrame({'Reason': [reason], 'Parcels_Available':[len(sdfAvailable)], 'Parcels_Used':[len(rows_to_fill)],
                                'Total_Forecasted_Units': [running_sum], 'Total_Remaining_Units': [target_sum - running_sum]})   
    return df, df_summary

# function to get the target sum
def get_target_sum(df, Jurisdiction, Unit_Pool, zoning_type):
    if zoning_type == 'MF':
        return df.loc[(df['Jurisdiction'] == Jurisdiction) & (df['Unit_Pool'] == Unit_Pool), 'Future_Units_Adjusted_MF'].values[0]
    elif zoning_type == 'SF':
        return df.loc[(df['Jurisdiction'] == Jurisdiction) & (df['Unit_Pool'] == Unit_Pool), 'Future_Units_Adjusted_SF'].values[0]
    elif zoning_type == 'Infill':
        return df.loc[(df['Jurisdiction'] == Jurisdiction) & (df['Unit_Pool'] == Unit_Pool), 'Future_Units_Adjusted_Infill'].values[0]
    return df.loc[(df['Jurisdiction'] == Jurisdiction) & (df['Unit_Pool'] == Unit_Pool), 'Future_Units_Adjusted'].values[0]

# function to check parcels meeting criteria
def check_parcel_condition(df, condition):
    sdfAvailable = df.loc[eval(condition)]
    # summarize parcel count, total potential units, and total existing units
    df_summary = pd.DataFrame({'Parcels_Available':[len(sdfAvailable)], 
                               'Total_Max_Units':[sdfAvailable['MAX_UNITS'].sum()],
                               'Total_Potential_Units':[sdfAvailable['POTENTIAL_UNITS'].sum()],
                               'Total_Existing_Units':[sdfAvailable['Residential_Units'].sum(),]}
                               )
    return df_summary
def get_parcel_conditions():
    ##------------------------------------ Conditional Statements for Forecasting Residential Unit Development------------------------------ ##
    # vacant buildable criteria
    vacant_buildable_criteria        = "(df['EXISTING_LANDUSE'] == 'Vacant') & (df['OWNERSHIP_TYPE'] == 'Private') & (df['RETIRED'] == 'No') & (df['IPES_SCORE'] > 0)"
    placer_vacant_buildable_criteria = "(df['EXISTING_LANDUSE'] == 'Vacant') & (df['OWNERSHIP_TYPE'] == 'Private') & (df['RETIRED'] == 'No') & (df['IPES_SCORE'] > 726)" 

    # Within TRPA Boundary as condition for all
    trpa_boundary_criteria = "(df['WITHIN_TRPA_BNDY'] == 1)"
    bonus_unit_criteria    = "(df['WITHIN_BONUSUNIT_BNDY'] == 'Yes')"
    no_zoning_criteria     = "(df['HOUSING_ZONING'] != 'NA')"
    sf_only_criteria       = "(df['HOUSING_ZONING'] == 'SF_only')"
    mf_only_criteria       = "(df['HOUSING_ZONING'] == 'MF_only')"
    sf_mf_criteria         = "(df['HOUSING_ZONING'].isin(['SF/MF', 'MF_only']))"
    adu_criteria           = "(df['ADU_ALLOWED'] == 'Yes') & (df['Residential_Units']>0)"
    towncenter_condition   = "(~df['TOWN_CENTER'].isna())"
    top_10_condition       = "(df['TOP_TEN_POTENTIAL_UNITS'] == 'Yes')"
    condo_size_condition   = "(df['PARCEL_ACRES'] >= 0.15)&(~df['EXISTING_LANDUSE'].isin(['Condominium', 'Condomunium Common Area']))"
    ready_to_forecast      = "(df['FORECAST_REASON'].isna())&(df['OWNERSHIP_TYPE'] == 'Private')"

    # setup f string to change jurisdiction in bonus condition
    bonus_vacant_condition_template  = ("(df['JURISDICTION'] == '{}') & "  + 
                                        bonus_unit_criteria + " & " + trpa_boundary_criteria + " & " + 
                                        vacant_buildable_criteria + " & " + sf_mf_criteria + " & " + 
                                        ready_to_forecast + " & " + condo_size_condition)
    vacant_condition_template        = ("(df['JURISDICTION'] == '{}') & "  + 
                                        trpa_boundary_criteria + " & " + 
                                        vacant_buildable_criteria + " & " + sf_mf_criteria + " & " + 
                                        ready_to_forecast + " & " + condo_size_condition)
    placer_vacant_condition_template = ("(df['JURISDICTION'] == '{}') & " + 
                                        trpa_boundary_criteria + " & " + placer_vacant_buildable_criteria + " & " + 
                                        sf_mf_criteria + " & " + 
                                        ready_to_forecast + " & " + condo_size_condition)
    infill_condition_template        = ("(df['JURISDICTION'] == '{}') & "  + 
                                        trpa_boundary_criteria + " & " + vacant_buildable_criteria + " & " + 
                                        sf_mf_criteria + " & " + 
                                        ready_to_forecast + " & " + top_10_condition)
    adu_condition_template           = ("(df['JURISDICTION'] == '{}') & "  + 
                                        trpa_boundary_criteria + " & " + adu_criteria + " & " + 
                                        ready_to_forecast)
    towncenter_condition_template    = ("(df['JURISDICTION'] == '{}') & "  + 
                                        trpa_boundary_criteria + " & " + towncenter_condition + " & " + 
                                        ready_to_forecast)

    # list of jurisdictions
    jurisdictions = ['CSLT', 'DG', 'PL', 'WA','TRPA']
    # loop through jurisdictions in bonus_condition
    for j in jurisdictions:
        condition = bonus_vacant_condition_template.format(j)
    ##------------------------------------ Conditional Statements for Forecasting Residential Unit Development------------------------------ ##
    # vacant buildable criteria
    vacant_buildable_criteria        = "(df['EXISTING_LANDUSE'] == 'Vacant') & (df['OWNERSHIP_TYPE'] == 'Private') & (df['RETIRED'] == 'No') & (df['IPES_SCORE'] > 0)"
    placer_vacant_buildable_criteria = "(df['EXISTING_LANDUSE'] == 'Vacant') & (df['OWNERSHIP_TYPE'] == 'Private') & (df['RETIRED'] == 'No') & (df['IPES_SCORE'] > 726)" 

    # Within TRPA Boundary as condition for all
    trpa_boundary_criteria = "(df['WITHIN_TRPA_BNDY'] == 1)"
    bonus_unit_criteria    = "(df['WITHIN_BONUSUNIT_BNDY'] == 'Yes')"
    no_zoning_criteria     = "(df['HOUSING_ZONING'] != 'NA')"
    sf_only_criteria       = "(df['HOUSING_ZONING'] == 'SF_only')"
    mf_only_criteria       = "(df['HOUSING_ZONING'] == 'MF_only')"
    sf_mf_criteria         = "(df['HOUSING_ZONING'].isin(['SF/MF', 'MF_only']))"
    adu_criteria           = "(df['ADU_ALLOWED'] == 'Yes') & (df['Residential_Units']>0)"
    towncenter_condition   = "(~df['TOWN_CENTER'].isna())"
    top_10_condition       = "(df['TOP_TEN_POTENTIAL_UNITS'] == 'Yes')"
    condo_size_condition   = "(df['PARCEL_ACRES'] >= 0.15)&(~df['EXISTING_LANDUSE'].isin(['Condominium', 'Condomunium Common Area']))"
    ready_to_forecast      = "(df['FORECAST_REASON'].isna())&(df['OWNERSHIP_TYPE'] == 'Private')"

    ##------------------------------------------------- Jurisdiction Specific Conditions ---------------------------------------------------- ##

    # jurisdiction bonus unit conditions
    CSLT_Bonus_SF_condition       = "(df['JURISDICTION'] == 'CSLT')" + " & " + bonus_unit_criteria + " & " + trpa_boundary_criteria + " & " + vacant_buildable_criteria + " & " + sf_mf_criteria + " & " + ready_to_forecast + " & " + condo_size_condition
    CSLT_Bonus_MF_condition       = "(df['JURISDICTION'] == 'CSLT')" + " & " + bonus_unit_criteria + " & " + trpa_boundary_criteria + " & " + vacant_buildable_criteria + " & " + sf_mf_criteria + " & " + ready_to_forecast + " & " + condo_size_condition
    CSLT_Bonus_infill_condition   = "(df['JURISDICTION'] == 'CSLT')" + " & " + bonus_unit_criteria + " & " + trpa_boundary_criteria + " & " + sf_mf_criteria + " & " + ready_to_forecast+ " & " + condo_size_condition

    DG_Bonus_SF_condition         = "(df['JURISDICTION'] == 'DG')" + " & " + bonus_unit_criteria + " & " + trpa_boundary_criteria + " & " + vacant_buildable_criteria + " & " + sf_mf_criteria + " & " + ready_to_forecast+ " & " + condo_size_condition
    DG_Bonus_MF_condition         = "(df['JURISDICTION'] == 'DG')" + " & " + bonus_unit_criteria + " & " +  trpa_boundary_criteria + " & " + vacant_buildable_criteria + " & " + sf_mf_criteria + " & " + ready_to_forecast+ " & " + condo_size_condition
    DG_Bonus_infill_condition     = "(df['JURISDICTION'] == 'DG')" + " & " + bonus_unit_criteria + " & " +  trpa_boundary_criteria +  " & " + sf_mf_criteria + " & " + ready_to_forecast + " & " + condo_size_condition

    PL_Bonus_SF_condition         = "(df['JURISDICTION'] == 'PL')" + " & " + bonus_unit_criteria + " & " + trpa_boundary_criteria + " & " + placer_vacant_buildable_criteria + " & " + sf_mf_criteria + " & " + ready_to_forecast+ " & " + condo_size_condition
    PL_Bonus_MF_condition         = "(df['JURISDICTION'] == 'PL')" + " & " + bonus_unit_criteria + " & " + trpa_boundary_criteria + " & " + placer_vacant_buildable_criteria + " & " + sf_only_criteria + " & " + ready_to_forecast+ " & " + condo_size_condition
    PL_Bonus_infill_condition     = "(df['JURISDICTION'] == 'PL')" + " & " + bonus_unit_criteria + " & " + trpa_boundary_criteria + " & " + sf_mf_criteria + " & " + ready_to_forecast+ " & " + condo_size_condition

    WA_Bonus_MF_condition         = "(df['JURISDICTION'] == 'WA')" + " & " + bonus_unit_criteria + " & " + trpa_boundary_criteria + " & " + vacant_buildable_criteria + " & " + sf_only_criteria + " & " + ready_to_forecast+ " & " + condo_size_condition
    WA_Bonus_SF_condition         = "(df['JURISDICTION'] == 'WA')" + " & " + bonus_unit_criteria + " & " + trpa_boundary_criteria + " & " + vacant_buildable_criteria + " & " + sf_only_criteria + " & " + ready_to_forecast+ " & " + condo_size_condition
    WA_Bonus_infill_condition     = "(df['JURISDICTION'] == 'WA')" + " & " + bonus_unit_criteria + " & " + trpa_boundary_criteria + " & " + sf_mf_criteria + " & " + ready_to_forecast+ " & " + condo_size_condition

    # jurisdiction general conditions
    CSLT_MF_condition             = "(df['JURISDICTION'] == 'CSLT') & " + trpa_boundary_criteria + " & " + vacant_buildable_criteria + " & " + sf_mf_criteria + " & " + ready_to_forecast + " & " + condo_size_condition
    CSLT_SF_condition             = "(df['JURISDICTION'] == 'CSLT') & " + trpa_boundary_criteria + " & " + vacant_buildable_criteria + " & " + sf_only_criteria + " & " + ready_to_forecast + " & " + condo_size_condition
    CSLT_infill_condition         = "(df['JURISDICTION'] == 'CSLT') & " + trpa_boundary_criteria + " & " + sf_mf_criteria + " & " + ready_to_forecast + " & " + condo_size_condition

    DG_MF_condition               = "(df['JURISDICTION'] == 'DG') & " + trpa_boundary_criteria + " & " + vacant_buildable_criteria + " & " + sf_mf_criteria + " & " + ready_to_forecast + " & " + condo_size_condition
    DG_SF_condition               = "(df['JURISDICTION'] == 'DG') & " + trpa_boundary_criteria + " & " + vacant_buildable_criteria + " & " + sf_only_criteria + " & " + ready_to_forecast + " & " + condo_size_condition
    DG_infill_condition           = "(df['JURISDICTION'] == 'DG') & " + trpa_boundary_criteria + " & " + sf_mf_criteria + " & " + ready_to_forecast + " & " + condo_size_condition

    EL_MF_condition               = "(df['JURISDICTION'] == 'EL') & " + trpa_boundary_criteria + " & " + vacant_buildable_criteria + " & " + sf_mf_criteria + " & " + ready_to_forecast + " & " + condo_size_condition  
    EL_SF_condition               = "(df['JURISDICTION'] == 'EL') & " + trpa_boundary_criteria + " & " + vacant_buildable_criteria + " & " + sf_only_criteria + " & " + ready_to_forecast + " & " + condo_size_condition
    EL_infill_condition           = "(df['JURISDICTION'] == 'EL') & " + trpa_boundary_criteria + " & " + sf_mf_criteria + " & " + ready_to_forecast + " & " + condo_size_condition

    PL_MF_condition               = "(df['JURISDICTION'] == 'PL') & " + trpa_boundary_criteria + " & " + placer_vacant_buildable_criteria + " & " + sf_mf_criteria + " & " + ready_to_forecast + " & " + condo_size_condition
    PL_SF_condition               = "(df['JURISDICTION'] == 'PL') & " + trpa_boundary_criteria + " & " + placer_vacant_buildable_criteria + " & " + sf_only_criteria + " & " + ready_to_forecast + " & " + condo_size_condition
    PL_infill_condition           = "(df['JURISDICTION'] == 'PL') & " + trpa_boundary_criteria + " & " + sf_mf_criteria + " & " + ready_to_forecast + " & " + condo_size_condition

    WA_MF_condition               = "(df['JURISDICTION'] == 'WA') & " + trpa_boundary_criteria + " & " + vacant_buildable_criteria + " & " + sf_mf_criteria + " & " + ready_to_forecast + " & " + condo_size_condition
    WA_SF_condition               = "(df['JURISDICTION'] == 'WA') & " + trpa_boundary_criteria + " & " + vacant_buildable_criteria + " & " + sf_only_criteria + " & " + ready_to_forecast + " & " + condo_size_condition
    WA_infill_condition           = "(df['JURISDICTION'] == 'WA') & " + trpa_boundary_criteria + " & " + sf_mf_criteria + " & " + ready_to_forecast + " & " + condo_size_condition

    # TRPA pool conditions
    # bonus unit conditions
    TRPA_Bonus_MF_condition       = bonus_unit_criteria + " & " + trpa_boundary_criteria + " & " + vacant_buildable_criteria + " & " + sf_mf_criteria + " & " + ready_to_forecast+ " & " + condo_size_condition
    TRPA_Bonus_SF_condition       = bonus_unit_criteria + " & " + trpa_boundary_criteria + " & " + vacant_buildable_criteria + " & " + sf_only_criteria + " & " + ready_to_forecast+ " & " + condo_size_condition
    TRPA_Bonus_infill_condition   = bonus_unit_criteria + " & " + trpa_boundary_criteria + " & " + sf_mf_criteria + " & " + ready_to_forecast+ " & " + condo_size_condition
    # general conditions
    TRPA_MF_condition             = trpa_boundary_criteria + " & " + vacant_buildable_criteria + " & " + sf_mf_criteria + " & " + ready_to_forecast+ " & " + condo_size_condition
    TRPA_SF_condition             = trpa_boundary_criteria + " & " + vacant_buildable_criteria + " & " + sf_only_criteria + " & " + ready_to_forecast+ " & " + condo_size_condition
    TRPA_infill_condition         = trpa_boundary_criteria + " & " + sf_mf_criteria + " & " + ready_to_forecast+ " & " + condo_size_condition

    # Town Center Pool Conditions
    TC_MF_condition               = trpa_boundary_criteria + " & " + towncenter_condition + " & " + vacant_buildable_criteria + " & " + sf_mf_criteria + " & " + ready_to_forecast + " & " + condo_size_condition
    TC_SF_condition               = trpa_boundary_criteria + " & " + towncenter_condition + " & " + vacant_buildable_criteria + " & " + sf_mf_criteria + " & " + ready_to_forecast + " & " + condo_size_condition
    TC_infill_condition           = trpa_boundary_criteria + " & " + towncenter_condition + " & " + sf_mf_criteria + " & " + ready_to_forecast + " & " + condo_size_condition

    # ADU Pool Conditions
    TRPA_ADU_condition            = trpa_boundary_criteria + " & " + adu_criteria + " & " + ready_to_forecast + " & " + condo_size_condition

    # Scenario 2 Conditions
    # These will all be set to 0 in the main input files
    TRPA_Affordable_condition       = trpa_boundary_criteria + " & " + towncenter_condition + " & " + sf_mf_criteria + " & " + ready_to_forecast + " & " + condo_size_condition
    TRPA_Moderate_condition         = trpa_boundary_criteria + " & " + bonus_unit_criteria + " & " + sf_mf_criteria + " & " + ready_to_forecast + " & " + condo_size_condition
    TRPA_Achievable_Bonus_condition         = trpa_boundary_criteria + " & " + bonus_unit_criteria + " & " + sf_mf_criteria + " & " + ready_to_forecast + " & " + condo_size_condition
    TRPA_Achievable_General_condition       = trpa_boundary_criteria + " & " + sf_mf_criteria + " & " + ready_to_forecast + " & " + condo_size_condition
    TRPA_Affordable_by_Design_condition       = trpa_boundary_criteria + " & " + sf_mf_criteria + " & " + ready_to_forecast + " & " + condo_size_condition
    conditions = {
                    'CSLT_Bonus_SF'      : CSLT_Bonus_SF_condition, 
                    'CSLT_Bonus_MF'      : CSLT_Bonus_MF_condition, 
                    'CSLT_Bonus_Infill'  : CSLT_Bonus_infill_condition,
                    'DG_Bonus_SF'        : DG_Bonus_SF_condition,
                    'DG_Bonus_MF'        : DG_Bonus_MF_condition,
                    'DG_Bonus_Infill'    : DG_Bonus_infill_condition,
                    'PL_Bonus_SF'        : PL_Bonus_SF_condition,
                    'PL_Bonus_MF'        : PL_Bonus_MF_condition,
                    'PL_Bonus_Infill'    : PL_Bonus_infill_condition,
                    'WA_Bonus_SF'        : WA_Bonus_SF_condition,
                    'WA_Bonus_MF'        : WA_Bonus_MF_condition,
                    'WA_Bonus_Infil'     : WA_Bonus_infill_condition,
                    'CSLT_General_MF'    : CSLT_MF_condition,
                    'CSLT_General_SF'    : CSLT_SF_condition,
                    'CSLT_General_Infill': CSLT_infill_condition,
                    'DG_General_MF'      : DG_MF_condition,
                    'DG_General_SF'      : DG_SF_condition,
                    'DG_General_Infill'  : DG_infill_condition,
                    'EL_General_MF'      : EL_MF_condition,
                    'EL_General_SF'      : EL_SF_condition,
                    'EL_General_Infill'  : EL_infill_condition,
                    'PL_General_MF'      : PL_MF_condition,
                    'PL_General_SF'      : PL_SF_condition,
                    'PL_General_Infill'  : PL_infill_condition,
                    'WA_General_MF'      : WA_MF_condition,
                    'WA_General_SF'      : WA_SF_condition,
                    'WA_General_Infill'  : WA_infill_condition,
                    'TRPA_Bonus_MF'      : TRPA_Bonus_MF_condition,
                    'TRPA_Bonus_SF'      : TRPA_Bonus_SF_condition,
                    'TRPA_Bonus_Infill'  : TRPA_Bonus_infill_condition,
                    'TRPA_General_MF'    : TRPA_MF_condition,
                    'TRPA_General_SF'    : TRPA_SF_condition,
                    'TRPA_General_Infill': TRPA_infill_condition,
                    'TRPA_ADU'           : adu_criteria,
                    'TC_MF'              : TC_MF_condition,
                    'TC_SF'              : TC_SF_condition,
                    'TC_Infill'          : TC_infill_condition,
                    'TRPA_Affordable'    : TRPA_Affordable_condition,
                    'TRPA_Moderate'      : TRPA_Moderate_condition,
                    'TRPA_Achievable_Bonus' : TRPA_Achievable_Bonus_condition,
                    'TRPA_Achievable_General' : TRPA_Achievable_General_condition,
                    'TRPA_Affordable_by_Design' : TRPA_Affordable_by_Design_condition
                    }
    return conditions
# get SQL connection
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

# save to pickle
def to_pickle(data, filename):
    with open(filename, 'wb') as f:
        pickle.dump(data, f)
    print(f'{filename} pickled')

# save to pickle and feature class
def to_pickle_fc(data, filename):
    data.spatial.to_featureclass(filename)
    with open(filename, 'wb') as f:
        pickle.dump(data, f)
    print(f'{filename} pickled and saved as feature class')

# get a pickled file as a dataframe
def from_pickle(filename):
    with open(filename, 'rb') as f:
        data = pickle.load(f)
    print(f'{filename} unpickled')
    return data

def read_sql_no_geom(query, conn):
    """pd.read_sql wrapper that skips geometry/geography columns for SDE tables.

    pyodbc raises ProgrammingError (ODBC type -151/-152) when SELECT * includes
    a geometry or geography column. This rewrites SELECT * to an explicit column
    list by introspecting INFORMATION_SCHEMA, then runs the query.
    """
    import re
    if not re.search(r'SELECT\s+\*', query, re.IGNORECASE):
        return pd.read_sql(query, conn)
    match = re.search(r'FROM\s+([\w\.\[\]]+)', query, re.IGNORECASE)
    if not match:
        return pd.read_sql(query, conn)
    table_ref = match.group(1).replace('[', '').replace(']', '')
    parts     = table_ref.split('.')
    schema    = parts[-2] if len(parts) >= 2 else None
    table     = parts[-1]
    schema_filter = f"TABLE_SCHEMA = '{schema}' AND " if schema else ''
    col_query = (
        f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
        f"WHERE {schema_filter}TABLE_NAME = '{table}' "
        f"AND DATA_TYPE NOT IN ('geometry', 'geography') "
        f"ORDER BY ORDINAL_POSITION"
    )
    df_cols  = pd.read_sql(col_query, conn)
    col_list = ', '.join(f'[{c}]' for c in df_cols['COLUMN_NAME'])
    new_query = re.sub(r'SELECT\s+\*', f'SELECT {col_list}', query, flags=re.IGNORECASE)
    return pd.read_sql(new_query, conn)


def fix_sedf_geometry(sdf, geom_col='SHAPE'):
    """Ensure an ArcGIS SEDF's geometry column contains ArcGIS Geometry objects.

    When geopandas is imported alongside arcgis, both libraries register an
    extension dtype named 'geometry'. After .loc[] or .copy(), pandas may
    reconstruct the SHAPE column using geopandas' extension type, storing
    shapely objects instead of ArcGIS Geometry and breaking .spatial accessor
    calls like to_featureclass(). Call this after from_featureclass() and
    after any .loc[] filtering.

    Usage:
        sdf = fix_sedf_geometry(pd.DataFrame.spatial.from_featureclass(fc))
        filtered = fix_sedf_geometry(sdf.loc[sdf['YEAR'] == 2022])
    """
    from arcgis.geometry import Geometry
    if geom_col not in sdf.columns:
        return sdf
    result = sdf.copy()
    def _coerce(g):
        if g is None:
            return None
        if isinstance(g, Geometry):
            return g
        if hasattr(g, '__geo_interface__'):   # shapely geometry
            return Geometry(g.__geo_interface__)
        return g
    result[geom_col] = [_coerce(g) for g in result[geom_col].to_numpy(dtype=object)]
    return result

def get_commercial_zones(df):
    columns_to_keep = ['Zoning_ID', 'Category', 'Density']
    # filter Use_Type to Multiple Family Dwelling
    df = df.loc[df['Category'] == 'Commercial']
    return df[columns_to_keep]

def get_tourist_zones(df):
    columns_to_keep = ['Zoning_ID', 'Category', 'Density']
    # filter Use_Type to Multiple Family Dwelling
    df = df.loc[df['Category'] == 'Tourist Accommodation']
    return df[columns_to_keep]

# function to get where Zoningin_ID Use_Type = Multi-Family and Density
def get_mf_zones(df):
    columns_to_keep = ['Zoning_ID', 'Use_Type', 'Density']
    # filter Use_Type to Multiple Family Dwelling
    df = df.loc[df['Use_Type'] == 'Multiple Family Dwelling']
    return df[columns_to_keep]

# function to get where Zoningin_ID Use_Type = Multi-Family and Density
def get_sf_zones(df):
    columns_to_keep = ['Zoning_ID', 'Use_Type', 'Density']
    # filter Use_Type to Multiple Family Dwelling
    df = df.loc[df['Use_Type'] == 'Single Family Dwelling']
    return df[columns_to_keep]

def get_mf_only_zones(df):
    columns_to_keep = ['Zoning_ID', 'Use_Type', 'Density']
    # filter Use_Type to Single Family Dwelling and not Multiple Family Dwelling
    dfMF = get_mf_zones(df)
    dfSF = get_sf_zones(df)
    # get Zoning_ID that are in both dataframes
    df = dfMF.loc[~dfMF['Zoning_ID'].isin(dfSF['Zoning_ID'])]
    return df[columns_to_keep]

def get_sf_only_zones(df):
    columns_to_keep = ['Zoning_ID', 'Use_Type', 'Density']
    # filter Use_Type to Single Family Dwelling and not Multiple Family Dwelling
    dfMF = get_mf_zones(df)
    dfSF = get_sf_zones(df)
    df = dfSF.loc[~dfSF['Zoning_ID'].isin(dfMF['Zoning_ID'])]
    return df[columns_to_keep]

def get_sf_mf_zones(df):
    columns_to_keep = ['Zoning_ID', 'Use_Type', 'Density']
    # get SF and MF zones
    dfSF = get_sf_zones(df)
    dfMF = get_mf_zones(df)
    # add the two dataframes together
    df = pd.concat([dfSF, dfMF])
    # only keep duplicate Zoning_ID
    df = df[df.duplicated(subset=['Zoning_ID'], keep=False)]
    return df[columns_to_keep]

def get_recieving_zones(df):
    columns_to_keep = ['Zoning_ID', 'SPECIAL_DESIGNATION']
    # filter transfer recieving
    df = df.loc[df['SPECIAL_DESIGNATION'] == 'Receive']
    return df[columns_to_keep]

def get_sending_zones(df):
    columns_to_keep = ['Zoning_ID', 'SPECIAL_DESIGNATION']
    df = df.loc[df['SPECIAL_DESIGNATION'] == 'Transfer']
    return df[columns_to_keep]
