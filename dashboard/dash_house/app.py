#!python3
# -*- coding: utf-8 -*-
#
#  дашборд 
# 
#  Evgeny S. Borisov <parser@mechanoid.su>
# 
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
import os
import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon
import plotly.express as px
from dash import Dash, dcc, html, Input, Output
import dash_leaflet as dl
import dash_leaflet.express as dlx

pd.options.plotting.backend = 'plotly'

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

ID_MAP = 'map-area'
ID_STAT = 'stat-area'
ID_PLACE = 'place-select'
ID_HOUSE_SIZE = 'house-size-select'
# ID_FRAME = 'frame-select'
ID_PRICE = 'price-slider'
ID_PRICE_LABEL = 'price-label'
ID_RESET_BUTTON = 'reset-button'

HOUSE_SIZE_DEFAULT = '- все -'   
# FRAME_NAME_DEFAULT = '- все -'
PLACE_DEFAULT = 'sevastopol'



# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def load_data(file_path='data/data_house.pkl'): # загружаем список объявлений
    df = pd.read_pickle(file_path)
    df['tooltip'] = df.apply(lambda d: d['title']+' | '+str(d['priceM'])+'M | '+d['adr'],axis=1)
    df['dt'] = pd.to_datetime( df['ts'].dt.date )
    return df


def data_filter(df):
    return df[
            ~( # выкидываем 'ущербные' варианты
                df['latitude'].isna()  # берём только объявления с геометкой 
                |df['is_part']
            )
            & (df['house_area']>40.) # ограничиваем количество комнат
            & (df['priceM']>1.) # ограничиваем цену
        ].reset_index(drop=True)


def convert_geodata(df): # конвертируем геометку
    return gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df['longitude'],df['latitude']), crs='epsg:4326',)



# def load_frames_index(file_path='data/frames/_index.tsv'): # загружаем индекс областей на карте для фильтрации объявлений по району
#     df = pd.read_csv(file_path,sep='\t')
#     fpath = os.path.dirname(file_path)
#     df['geometry_file'] = df['geometry_file'].apply(lambda s: os.path.join(fpath,s))
#     return df
# 
# def load_frames(index): # загружаем области поиска
#     swap_coo = lambda coo : [ (c[1],c[0]) for c in coo ] # координаты из яндекс-карт нужно переставлять местами 
#     return  gpd.GeoDataFrame([ 
#             { 
#                 'area_name':nm, # название района
#                 'geometry': Polygon( swap_coo( pd.read_csv(f,header=None).values ) ) } # собираем полигон по точкам для поля geometry
#             for nm,f in index.values
#         ],
#         crs='epsg:4326', # система координат яндекс-карт
#         )

def stat(df):
    return (
        # df.groupby(['place','house_size_category','dt'])
        df.groupby(['house_size_category','dt'])
        ['priceM'].describe(percentiles=[.25,.5,])
    )


def diagram_count(df_stat):
    return [(
        df_stat['count']
        .reset_index()
        .pivot(index='dt',columns='house_size_category',values='count')
        .plot.bar(barmode='group',title='количество предложений') 
    ),]

def diagram_price(df_stat):
    return [
        df_stat.loc[hs,['min','25%','50%']]
        .plot(title=f'цена на дома {hs} м2', markers=True) 
        for hs in df_stat.reset_index()['house_size_category'].unique()
    ]

def plot_stat(df_stat): 
    return diagram_count( df_stat) + diagram_price( df_stat ) 




# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
# загружаем данные
data = convert_geodata( data_filter( load_data() ) ) # фильтрованные объявления с геометкой
places = sorted(set(data['place']))
house_size = list(data['house_size_category'].cat.categories)

#frame_index = load_frames_index() # список областей поиска
#frame_names = frame_index['place_name'].tolist()
#frames = load_frames(frame_index) # координаты областей поиска
#del frame_index

prices = sorted(
    set(
        data.groupby(['place','dt'])['priceM']
        .describe(percentiles=[.01,.05,.1,.25,.5,.75,.95])
        .drop(columns=['count','mean','std','max','min'])
        .max()
    )
)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
# рисуем дашборд
def panel_control(places,house_size): # панель управления
    return html.Div(style= {'margin':'5px',}, children = [
                # выбор комнаты
                html.Div( dcc.Dropdown(id=ID_PLACE, options=places, value=PLACE_DEFAULT,clearable=False,), style= { 'width':'40%','float':'left',}, ),  
                # выбор района
                html.Div( dcc.Dropdown(id=ID_HOUSE_SIZE, options= [HOUSE_SIZE_DEFAULT,] + house_size, value=HOUSE_SIZE_DEFAULT,clearable=False ), style= {'width':'20%','float':'left',}, ), 
                # выбор области поиска
                # html.Div( dcc.Dropdown(id=ID_FRAME, options= [FRAME_NAME_DEFAULT,] + frame_names, value=FRAME_NAME_DEFAULT), style= {'width':'40%','float':'left',}, ), 
                # html.Div( html.Button('сброс',id=ID_RESET_BUTTON, title='сброс'), style= {'width':'10%','float':'left', 'padding':'7px',}, )
            ]
            )

def panel_stat(): # панель с диаграммами
    return html.Div( id=ID_STAT, style={'overflow-y':'auto','height':'95vh','clear':'left'}, )
         

def panel_map_control(prices):
    return html.Div(style= {'margin':'5px',},children = [
                html.Div( 
                    dcc.RangeSlider(
                        id=ID_PRICE, 
                        min=prices[0], 
                        max=prices[-1], 
                        # step=None,
                        value=[prices[0],prices[-1]], 
                        marks = { p:f'{p:.1f}M' for p in prices },
                    ),
                    style= {'float':'left','width':'80%',}, 
                ), 
                html.Div( html.Label(f'цена до {prices[-1]:.1f}M',id=ID_PRICE_LABEL), style= { 'float':'left',}, ),  
            ],
            )


def panel_map(prices, map_center_coo=[44.,33.,]): # панель с картой
    return html.Div(children =[
            panel_map_control(prices),
            dl.Map(
                id=ID_MAP,
                center=map_center_coo,
                style={'width':'100%','height':'94vh','margin':'auto','display':'block',},
                ) 
            ])


app = Dash()
app.layout = html.Div(
    children=[
        html.Div( # левая панель
            style= { 'width':'40%','float':'left',},
            children = [
                panel_control(places,house_size,), # панель управления
                panel_stat(), # панель с диаграммами
            ]
        ),
        html.Div( # правая панель
            style={'width':'60%','float':'right',},
            children = [
                panel_map(prices), # правая панель с картой
            ]
        )
    ],
)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
def pack_diagram(fig):
    legend={'orientation':'h', 'yanchor':'bottom', 'y':1., 'xanchor':'right', 'x':1.}   
    return dcc.Graph( figure = fig.update_layout( xaxis_tickangle=-45, legend=legend,) )

@app.callback( # обработчик событий "выбор района и/или количества комнат из списка"
    Output(component_id=ID_STAT, component_property='children'),
    Input(component_id=ID_PLACE, component_property='value'),
    Input(component_id=ID_HOUSE_SIZE, component_property='value'),
#    Input(component_id=ID_FRAME, component_property='value'),
)
def update_stat(place,house_size,): # обновление диаграмм при изменении района поиска
    data_ = data.query(f'place=="{place}"') 
    if len(data_)<1: return [ html.Span('no data'), ]

#     # отрезаем объявления по области на карте
#     if frame_name != FRAME_NAME_DEFAULT:
#         frame_ = frames[ frames['area_name']==frame_name ] # координаты района
#         data_ = data_.sjoin( frame_, how='inner', predicate='within') 
#         if len(data_)<1: return [ html.Span('no data'), ]

    if house_size!=HOUSE_SIZE_DEFAULT:
        data_ = data_.query(f'house_size_category=="{house_size}"')
        if len(data_)<1: return [ html.Span('no data'), ]

    return [ pack_diagram(f) for f in plot_stat(stat(data_)) ] # рисуем диаграммы
 

def convert_frame_geometry(fg): # конвертируем данные геофрейма района в формат карт
    return dl.Polygon( positions = [ (y,x) for x,y in fg.exterior.coords ] )

def convert_data_points(df):  # конвертируем данные геофрейма позиций в формат карт
    return dlx.dicts_to_geojson( 
            df[['url','tooltip','latitude','longitude']]
            .rename(columns={'latitude':'lat','longitude':'lon','url':'name',})
            .T.to_dict().values()
            )

@app.callback( # обработчик события "выбор района из списка"
    Output(component_id=ID_MAP, component_property='children'),
    Input(component_id=ID_PLACE, component_property='value'),
    Input(component_id=ID_HOUSE_SIZE, component_property='value'),    
#    Input(component_id=ID_FRAME, component_property='value'), # обработчик события "выбор района из списка"
    Input(component_id=ID_PRICE, component_property='value'), # обработчик события "ограничение цены"
)
def update_map(place,house_size,price): # обновление меток на карте при изменении параметров поиска
    layers = [ dl.TileLayer(), ] # базовый слой OSM

    data_ = data.query(f'place=="{place}"').drop_duplicates('url') 
    if len(data_)<1: return  layers

    if house_size!=HOUSE_SIZE_DEFAULT:
        data_ = data_.query(f'house_size_category=="{house_size}"')
        if len(data_)<1: return layers

    data_ = data_[ data_['priceM'].between(*price) ] 
    if len(data_)<1 : return layers

    # обозначаем точки на карте
    return layers + [dl.GeoJSON( data=convert_data_points(data_), zoomToBounds=True, cluster=True ), ]

@app.callback( # обработчик события "изменение фильтра цены"
    Output(component_id=ID_PRICE_LABEL, component_property='children'),
    Input(component_id=ID_PRICE, component_property='value'), # обработчик события "ограничение цены"
)
def update_price_label(price): # обновление меток на карте при изменении района поиска
    return f'цена от {price[0]:.1f}M до {price[1]:.1f}M'




# @app.callback(
#     Output(ID_PLACE, 'children'),
#     Input(ID_RESET_BUTTON, 'n_clicks'),
# )
# def reset_button_click(): pass
# # ID_HOUSE_SIZE

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

if __name__ == '__main__': 
    app.run_server() 
    # app.run_server(debug=True, use_reloader=False)

