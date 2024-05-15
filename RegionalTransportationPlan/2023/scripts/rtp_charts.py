import numpy as np
import pandas as pd
import plotly.graph_objects as go

from utils import (
    # get_fs_data,
    # get_fs_data_spatial,
    # get_fs_data_spatial_query,
    # read_file,
    # stacked_area,
    stackedbar,
    trendline,
)

# get data for transit ridership
def get_data_transit():
    url = "https://www.laketahoeinfo.org/WebServices/GetTransitMonitoringData/CSV/e17aeb86-85e3-4260-83fd-a2b32501c476"

    dfTransit = pd.read_csv(url)
    dfTransit['Month'] = pd.to_datetime(dfTransit['Month'])
    dfTransit['Month'] = dfTransit['Month'].dt.strftime('%Y-%m')
    # filter out rows where RouteType is not Paratransit, Commuter, or Seasonal Fixed
    df = dfTransit.loc[~dfTransit['RouteType'].isin(['Paratransit', 'Commuter', 'Seasonal Fixed Route'])]
    # df = dfTransit.loc[dfTransit['RouteType'] != 'Paratransit']

    # replace transit operator values with abreviations
    df['TransitOperator'] = df['TransitOperator'].replace(
        ['Tahoe Transportation District',
       'Tahoe Truckee Area Regional Transit',
       'South Shore Transportation Management Association'],
       ["TTD", "TART", "SSTMA"])
    # route name = route type + transit operator
    df['RouteName'] = df['RouteType'] + ' - ' + df['TransitOperator']
    # group by RouteType, TransitOperator, and Month with sum of MonthlyRidership
    df = df.groupby(['RouteName', 'Month'])['MonthlyRidership'].sum().reset_index()
    # rename columns to Date, Name, Ridership
    df.rename(columns={'Month':'Date', 'RouteName':'Name', 'MonthlyRidership':'Ridership'}, inplace=True)
    # sort by Date
    df = df.sort_values('Date')
    return df

# html/3.3.a_Transit_Ridership.html
def plot_transit(df):
    trendline(
        df,
        path_html="html/Transit_Ridership_Line.html",
        div_id="Transit_Ridership",
        x="Date",
        y="Ridership",
        color="Name",
        color_sequence=["#023f64", "#7ebfb5", "#a48352", "#FC9A62"],
        sort="Date",
        orders=None,
        x_title="Date",
        y_title="Ridership",
        markers=True,
        hover_data=None,
        tickvals=None,
        ticktext=None,
        tickangle=None,
        hovermode="x unified",
        format=",.0f",
        custom_data=["Name"],
        hovertemplate="<br>".join([
            "<b>%{y:,.0f}</b> riders on",
            "<i>%{customdata[0]}</i> lines"
                ])+"<extra></extra>",
        additional_formatting = dict(
                                    title = "Transit Ridership",
                                    margin=dict(t=20),
                                    legend=dict(
                                        # title="Transit Ridership",
                                        orientation="h",
                                        entrywidth=120,
                                        yanchor="bottom",
                                        y=1.05,
                                        xanchor="right",
                                        x=0.95,
                                        )
                                    )
        )
    df = get_data_transit()
    stackedbar(
        df,
        path_html="html/Transit_Ridership_Bar.html",
        div_id="Transit_Ridership",
        x="Date",
        y="Ridership",
        color="Name",
        color_sequence=["#023f64", "#7ebfb5", "#a48352", "#FC9A62"],
        sort="Date",
        orders=None,
        x_title="Date",
        y_title="Ridership",
        markers=True,
        hover_data=None,
        tickvals=None,
        ticktext=None,
        tickangle=None,
        hovermode="x unified",
        format=",.0f",
        custom_data=["Name"],
        hovertemplate="<br>".join([
            "<b>%{y:,.0f}</b> riders on",
            "<i>%{customdata[0]}</i> lines"
                ])+"<extra></extra>",
        additional_formatting = dict(
                                    title = "Transit Ridership",
                                    margin=dict(t=20),
                                    legend=dict(
                                        # title="Transit Ridership",
                                        orientation="h",
                                        entrywidth=120,
                                        yanchor="bottom",
                                        y=1.05,
                                        xanchor="right",
                                        x=0.95,
                                    ))
                        
    )