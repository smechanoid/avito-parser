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
 


def load_data(data_file = 'data/data_flat.pkl'):
    # cols = ['title','adr','latitude','longitude','priceM','ts']
    df = pd.read_pickle(data_file)
    df['dt'] = pd.to_datetime( df['ts'].dt.date )
    
    # берём объявления с геометкой
    df = df[ (~df['latitude'].isnull()) ].reset_index(drop=True)

    # выкидываем "ущербные" варианты 
    df = df.query('~(is_studio|is_apartment|is_part|is_auction|is_openspace|is_SNT|is_roof)&(nrooms>0)&(nrooms<4)')
    gdf = gpd.GeoDataFrame( df, geometry = gpd.points_from_xy( df['longitude'], df['latitude']), crs='epsg:4326', )

    # del df

    return gdf



def calc_stat(gdf):
    return (
        gdf.query('priceM>1.')
        .groupby(['nrooms','dt'])
        ['priceM']
        .describe(percentiles=[.1,.25,.5,.75,.9])
    )


gdf = load_data()
stat = calc_stat(gdf)

gdf_ = gdf[['avito_id','title','adr','latitude','longitude','priceM','nrooms','dt','geometry']].sample(100)

# app.display( name='title', value='Vector demo',)
# app.display( name='description', value='A Greppo demo app for vector data using GeoJSON data.',)
# app.base_layer( provider="CartoDB Positron",) 

app.base_layer(
    name="Open Street Map",
    visible=True,
    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    subdomains=None,
    attribution='(C) OpenStreetMap contributors',
)

app.vector_layer(
    data=gdf_.drop(columns=['dt',]),
    name="avito",
    description="avito",
    style={"color": "#e41a1c"},
    visible=True,
)


stat_cols = ['min','25%','50%']
stat_colors = ["rgb(200, 50, 150)", "rgb(100, 50, 150)", "rgb(100, 50, 10)"]

nroom = 1
app.line_chart(
    name="цены на квартиры",
    description=f"цена на {nroom}к",
    x = [ d.strftime("%m/%d/%Y") for d in stat.loc[nroom,stat_cols].index ],
    y=stat.loc[nroom,stat_cols].values.T.tolist(),
    label=stat_cols,
    color=stat_colors,
)

nroom = 2
app.line_chart(
    name="цены на квартиры",
    description=f"цена на {nroom}к",
    x = [ d.strftime("%m/%d/%Y") for d in stat.loc[nroom,stat_cols].index ],
    y=stat.loc[nroom,stat_cols].values.T.tolist(),
    label=stat_cols,
    color=stat_colors,
)

nroom = 3
app.line_chart(
    name="цены на квартиры",
    description=f"цена на {nroom}к",
    x = [ d.strftime("%m/%d/%Y") for d in stat.loc[nroom,stat_cols].index ],
    y=stat.loc[nroom,stat_cols].values.T.tolist(),
    label=stat_cols,
    color=stat_colors,
)


