#!python3
# -*- coding: utf-8 -*-
#
#  дашборд 
# 
#  Evgeny S. Borisov parser@mechanoid.su
# - - - - - - - - - - - - - - - - 

import pandas as pd
from greppo import app
import geopandas as gpd
from shapely.geometry import Polygon

# pip install shapely==1.8.2
# pip install greppo==0.0.32


# FIXME: некорректное отображение адресов на карте

# - - - - - - - - - - - - - - - - 
def load_data(data_file = 'data/data_flat.pkl'):
    # cols = ['title','adr','latitude','longitude','priceM','ts']
    df = pd.read_pickle(data_file)
    df['dt'] = pd.to_datetime( df['ts'].dt.date )
    
    # берём объявления с геометкой
    df = df[ (~df['latitude'].isnull()) ].reset_index(drop=True)

    # выкидываем 'ущербные' варианты 
    df = df.query('~(is_studio|is_apartment|is_part|is_auction|is_openspace|is_SNT|is_roof)&(nrooms>0)&(nrooms<4)')
    gdf = gpd.GeoDataFrame( df, geometry = gpd.points_from_xy( df['longitude'], df['latitude']), crs='epsg:4326', )

    # del df

    return gdf

# def load_frames(frames_path= 'data/frames/'):  # загружаем области поиска
#     frames_index = pd.read_csv(f'{frames_path}/_index.tsv',sep='\t')
#     swap_coo = lambda coo : [ (c[1],c[0]) for c in coo ]
#     df2poly = lambda df : Polygon(swap_coo(df.values))
#     return  gpd.GeoDataFrame([ 
#         { 'area_name':nm, 'geometry': df2poly( pd.read_csv(f'{frames_path}/{f}',header=None) ) } 
#         for nm,f in frames_index.values
#     ],crs='epsg:4326',)


def calc_stat(gdf):
    return (
        gdf.query('priceM>1.')
        .groupby(['nrooms','dt'])
        ['priceM']
        .describe(percentiles=[.1,.25,.5,.75,.9])
    )


# - - - - - - - - - - - - - - - - 
# app.display( name='title', value='Vector demo',)
# app.display( name='description', value='A Greppo demo app for vector data using GeoJSON data.',)

# - - - - - - - - - - - - - - - - 
# app.base_layer( provider='CartoDB Positron',) 

app.base_layer(
    name='Open Street Map',
    visible=True,
    url='https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    subdomains=None,
    attribution='(C) OpenStreetMap contributors',
)

# - - - - - - - - - - - - - - - - 

# frames = load_frames()
frames = gpd.read_file('data/frames.geojson')

frame_names = frames['area_name'].values.tolist()
# frame_select = app.multiselect(
#     name = "районы", 
#     options = frame_names,
#     default = [frame_names[0],],
# )

frame_select = app.select(
    name = "районы", 
    options = frame_names,
    default = frame_names[0],
)

app.display( name='title', value=frame_select,)

app.overlay_layer(
    data=frames[frames['area_name']==frame_select],
    name='район',
    description="description",
    style={"fillColor": "#00b9b9"},
    visible=True,
)

# - - - - - - - - - - - - - - - - 

cols = ['title','adr','latitude','longitude','priceM','nrooms','geometry']
# gdf = load_data()

# фильтруем данные по области
# gdf = gpd.read_file('data/data_flat.geojson').sjoin( frames[frames['area_name']==frame_select], how='inner', predicate='within')[cols].reset_index(drop=True)
gdf = load_data()

app.vector_layer(
    data=gdf.sjoin( frames[frames['area_name']==frame_select], how='inner', predicate='within')[cols],
    name='avito',
    description='avito',
    style={'color': '#e41a1c'},
    visible=True,
)


# FIXME: добавить обработку пустых списков


# - - - - - - - - - - - - - - - - 

stat = calc_stat(gdf)

stat_cols = ['min','25%','50%']
stat_colors = ['rgb(200, 50, 150)', 'rgb(100, 50, 150)', 'rgb(100, 50, 10)']

nroom = 1
app.line_chart(
    name='цены на квартиры',
    description=f'цена на {nroom}к',
    x = [ d.strftime('%m/%d/%Y') for d in stat.loc[nroom,stat_cols].index ],
    y=stat.loc[nroom,stat_cols].values.T.tolist(),
    label=stat_cols,
    color=stat_colors,
)

nroom = 2
app.line_chart(
    name='цены на квартиры',
    description=f'цена на {nroom}к',
    x = [ d.strftime('%m/%d/%Y') for d in stat.loc[nroom,stat_cols].index ],
    y=stat.loc[nroom,stat_cols].values.T.tolist(),
    label=stat_cols,
    color=stat_colors,
)

nroom = 3
app.line_chart(
    name='цены на квартиры',
    description=f'цена на {nroom}к',
    x = [ d.strftime('%m/%d/%Y') for d in stat.loc[nroom,stat_cols].index ],
    y=stat.loc[nroom,stat_cols].values.T.tolist(),
    label=stat_cols,
    color=stat_colors,
)



# buildings_gdf_filtered = buildings_gdf[buildings_gdf.building == filter_select.get_value()[0]]
# 
# app.overlay_layer(
#     buildings_gdf_filtered,
#     title="Buildings",
#     description="Buildings in a neighbourhood in Amsterdam",
#     style={"fillColor": "#F87979"},
#     visible=True,
# )


