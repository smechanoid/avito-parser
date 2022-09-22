#!python3
# -*- coding: utf-8 -*-
#
#  дашборд 
# 
#  Evgeny S. Borisov <parser@mechanoid.su>
# 
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
from dash import Dash
from dash import dcc, html, Input, Output

import plotly.express as px
import dash_leaflet as dl
import dash_leaflet.express as dlx
import geojson
import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon

pd.options.plotting.backend = 'plotly'

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

def load_data(file_path='data/data_flat.pkl'):
    # cols = ['avito_id','title','adr','latitude','longitude','priceM','nrooms',]
    data = pd.read_pickle(file_path)
    data['tooltip'] = data.apply(lambda d: d['title']+' | '+str(d['priceM'])+'M | '+d['adr'],axis=1)
    data['dt'] = pd.to_datetime( data['ts'].dt.date )
    return data


def convert_data(df):
    # берём объявления с геометкой
    df = df[ (~df['latitude'].isnull()) ].reset_index(drop=True)
    # выкидываем 'ущербные' варианты 
    df = df.query('~(is_studio|is_apartment|is_part|is_auction|is_openspace|is_SNT|is_roof)&(nrooms>0)&(nrooms<4)')
    return gpd.GeoDataFrame( df, geometry = gpd.points_from_xy( df['longitude'], df['latitude']), crs='epsg:4326', )

    return gdf


def load_frames(frames_path='data/frames/'):  # загружаем области поиска
    frames_index = pd.read_csv(f'{frames_path}/_index.tsv',sep='\t')
    swap_coo = lambda coo : [ (c[1],c[0]) for c in coo ]
    df2poly = lambda df : Polygon(swap_coo(df.values))
    return  gpd.GeoDataFrame([ 
            { 'area_name':nm, 'geometry': df2poly( pd.read_csv(f'{frames_path}/{f}',header=None) ) } 
            for nm,f in frames_index.values
        ],crs='epsg:4326',)


def stat(data):
    return  (
        data.query('priceM>1.')
        .groupby(['nrooms','dt'])
        ['priceM'].describe(percentiles=[.1,.25,.5,.75,.9])
    )

def plot_stat(stat): 
    return (
           (
                stat['count']
                    .reset_index()
                    .rename(columns={'nrooms':'комнаты'})
                    .pivot(index='dt',columns='комнаты',values='count')
                    [[1,2,3]]
                    .plot.bar(barmode='group',title='количество предложений') 
            ),
            stat.loc[1,['min','25%','50%']].plot(title='цена на 1к', markers=True), 
            stat.loc[2,['min','25%','50%']].plot(title='цена на 2к', markers=True),
            stat.loc[3,['min','25%','50%']].plot(title='цена на 3к', markers=True), 
        )


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

data = convert_data( load_data() )
frames = load_frames()


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

app = Dash()

app.layout = html.Div(
    children=[
        html.Div(
            style={ 'width':'40%','float':'left',}, 
            children=[
                html.Div(id='frame-text'),
                dcc.Dropdown( frames['area_name'].tolist()+ ['- все районы -', ], '- все районы -', id='frame-select', ), 
                html.Div( id='stat-area', style={'overflow-y': 'scroll','height':'95vh'},),
                ]
         ),
        html.Div(
            style={'width':'60%','float':'right',}, 
            children=[
                dl.Map(id='map-area',
                    center = [44.,33.,],    
                    style = { 'width':'100%', 'height':'98vh', 'margin':'auto', 'display':'block', },
                    ),
                ]
            ),
       ]
)



# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

@app.callback(
    Output(component_id='stat-area', component_property='children'),
    Input(component_id='frame-select', component_property='value'),
)
def update_frame(frame_name):
    frame_ = frames[ frames['area_name']==frame_name ]
    data_ = data.sjoin( frame_, how='inner', predicate='within') if len(frame_)>0 else data
    return [ 
            dcc.Graph( 
                figure=f.update_layout(
                    xaxis_tickangle=-45,
                    legend=dict(
                        orientation='h',
                        yanchor='bottom', y=1.,
                        xanchor='right', x=1.
                        ),
                    ) 
                ) 
            for f in plot_stat(stat(data_)) 
            ]


@app.callback(
    Output(component_id='map-area', component_property='children'),
    Input(component_id='frame-select', component_property='value'),
)
def update_map(frame_name):
    items = [ dl.TileLayer(), ]
    data_ = data[~data['latitude'].isna()]

    frame_ = frames[ frames['area_name']==frame_name ]
    if len(frame_)>0: 
        polygon = dl.Polygon( positions = [ (y,x) for x,y in frame_.iloc[0]['geometry'].exterior.coords ] )
        items.append( dl.LayerGroup(polygon) )
        data_ = data_.sjoin( frame_, how='inner', predicate='within')
 
    if len(data_)<1 : return items
 
    points = dlx.dicts_to_geojson( 
            data_[['url','tooltip','latitude','longitude']]
            .rename(columns={'latitude':'lat','longitude':'lon','url':'name',})
            .T.to_dict().values()
            )
 
    items.append( dl.GeoJSON( data=points, zoomToBounds=True,cluster=True ) )

    return items




# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

if __name__ == '__main__': 
    app.run_server() 
    # app.run_server(debug=True, use_reloader=False)

