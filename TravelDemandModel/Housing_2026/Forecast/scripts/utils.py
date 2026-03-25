## A set of utility functions to help with the data processing and analysis
from pathlib import Path
import pandas as pd
import plotly.express as px
from arcgis.features import FeatureLayer, GeoAccessor, GeoSeriesAccessor
import arcpy
import pytz
from datetime import datetime
from time import strftime

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