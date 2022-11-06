import geopandas as gpd
import pandas as pd
import shapely.geometry
from shapely.geometry import Polygon
import json
import random
import plotly
import plotly.graph_objects as go

__all__ = ["plot_polygons", "make_table", "dummy_pols", "dummy_scores", "ser_to_ian"]

def plot_polygons(poly_json, scores, start_lat=55, start_lon=8, zoom=4):

    fig = go.Figure()

    fig.add_traces(go.Choroplethmapbox(
        geojson=poly_json,
        name="Perimeter",
        hovertemplate =
        'Score = %{score}'+
        '<br>Id = %{id}',
        locations= scores['id'].astype(str),
        z = scores['score'].astype(float),
        colorbar_title = "Scores",
        colorscale="RdYlGn"))

    fig.update_layout(
        # title="Plot Title",
        # title_x=0.5,
        # title_y=0.92,
        # font=dict(
        #     family="Comic Sans MS",
        #     size=24),
        width=900, height=600,
        mapbox = dict(center= dict(lat=start_lat, lon=start_lon),         
        zoom=zoom,
        style='light'
        ))

    fig.update_layout(mapbox_style="open-street-map")
    
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

def make_table(ids, scores):

    lis = go.Figure(data=[go.Table(
        header=dict(values=['BlobId', 'Scores'],
                    line_color='darkslategray',
                    fill_color='lightskyblue',
                    align='left'),
        cells=dict(values=[ids, # 1st column
                        scores], # 2nd column
                line_color='darkslategray',
                fill_color='lightcyan',
                align='left'))
    ])

    lis.update_layout(width=400, height=300)
    
    return json.dumps(lis, cls=plotly.utils.PlotlyJSONEncoder)

def dummy_pols():

    p1 = Polygon([(12, 50), (11, 50), (11, 49)])
    p2 = Polygon([(8, 51), (9, 50), (9, 51)])
    p3 = Polygon([(10, 50), (11, 50), (11, 51)])

    pol_list = [p1, p2, p3]
    g = gpd.GeoSeries(pol_list)

    return json.loads(g.to_json())


def dummy_scores():

    return pd.DataFrame([[0,10],[1,60],[2,100]], columns = ['id','score'])

def ser_to_ian(dictionary):

    return 0