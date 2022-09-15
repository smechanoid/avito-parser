#!python3
# -*- coding: utf-8 -*-
#
# определяем геометки по адресу
#
#  Evgeny S. Borisov <parser@mechanoid.su>  
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

# import sys 
# import os
import logging

import re
# from datetime import datetime as dt
import requests
from requests.exceptions import HTTPError

from tqdm.notebook import tqdm
import pandas as pd

from geopy.geocoders import Nominatim

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
class Geocoder:
    
    def transform(self, adr, show_pbar=False):
        # ищем геометку по адресу
        pos =(
            pd.DataFrame( adr.progress_apply(self._get_coo).tolist() )
            if show_pbar
            else pd.DataFrame( adr.apply(self._get_coo).tolist() )
        )
        return pd.concat([ adr, pos ],axis=1)
        
    def _get_coo(self,adr):
            return {'latitude':None,'longitude':None, }
 

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
class GeocoderOSM(Geocoder):
    
    def __init__(self,):
        user_agent='Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0'
        self._geolocator = Nominatim(user_agent=user_agent)
        super().__init__()
        
    def _get_coo(self,adr):
        adr_ = adr.split(',')
        loc = self._geolocator.geocode(adr_) # пробуем определить координаты
        truncated = False
        while True:
            if not (loc is None): # нашел...
                return {'latitude':loc.latitude,'longitude':loc.longitude,'truncated':truncated } #,adr_

            # ...не нашел...
            if( len(adr_) < 3 ): break # адрес слишком короткий для сокращения
            adr_ = adr_[:-1] # выкидываем часть адреса (номер дома)
            loc = self._geolocator.geocode( adr_) # ... и пробуем ещё раз
            truncated = True

        return {'latitude':None,'longitude':None,'truncated':None, }


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
class GeocoderYandex(Geocoder):
    
    def __init__(self,key):
        #user_agent='Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0'
        self._key=key
        super().__init__()
   
    def _get_coo(self,adr):
        loc = self._req(adr)
        try:
            coo = loc[0]['GeoObject']['Point']['pos'].split()
            return { l:float(c) for l,c in zip(['longitude','latitude'],coo) }
            
        except:
            return {'latitude':None,'longitude':None, }
        
    def _req(self,adr):
        url = f'https://geocode-maps.yandex.ru/1.x/?lang=ru_RU&apikey={self._key}&geocode={adr}'
        try:
            r = requests.get(url,params={'format':'json',})
            r.raise_for_status() 
            logging.debug('HttpGetRequest: request success')
            return r.json()['response']['GeoObjectCollection']['featureMember']

        except HTTPError as http_err:
            logging.error(f'HttpGetRequest: request : {http_err}')

        except Exception as err:
            logging.error(f'HttpGetRequest: request : {err}')

        return None



# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
class AddressTransformer:
    
    def transform(self,adr):  # чистим строку адреса
        symb_lat = 'yexapocEXAPOCTHKBM'
        symb_rus = 'уехаросЕХАРОСТНКВМ'
        l2r = str.maketrans(symb_lat,symb_rus) 
        return (
                adr
                .apply(lambda s: s.translate(l2r) )
                .apply(lambda s: re.sub(r'\bмикрорайон\b',' ',s))
                .apply(lambda s: re.sub(r'\bмуниципальный округ\b',' район ',s))
                .apply(lambda s: re.sub(r'\bкотт?еджный пос[ёе]лок\b',' ',s))
                .apply(lambda s: re.sub(r'\bпос[ёе]лок\b',' ',s))
                .apply(lambda s: re.sub(r',\s*,',', ',s))
                .apply(lambda s: re.sub(r' +',' ',s))
            )
        
# # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
# class AddressTransformerSev(AddressTransformer):
#     
#     def transform(self,adr): 
#         symb_lat = 'yexapocEXAPOCTHKBM'
#         symb_rus = 'уехаросЕХАРОСТНКВМ'
#         l2r = str.maketrans(symb_lat,symb_rus) 
#         return (
#                 adr
#                 .apply(lambda s: s.translate(l2r) )
#                 .apply(lambda s: re.sub(r'\b[Сс]евастополь\b','',s))
#                 .apply(lambda s: re.sub(r'\bмикрорайон\b',' ',s))
#                 .apply(lambda s: re.sub(r'\bмуниципальный округ\b',' район ',s))
#                 .apply(lambda s: re.sub(r'\bкотт?еджный пос[ёе]лок\b',' ',s))
#                 .apply(lambda s: re.sub(r'\bпос[ёе]лок\b',' ',s))
#                 .apply(lambda s: re.sub(r'^','Севастополь, ',s))
#                 # .apply(lambda s: re.sub(r'[Сс]евастополь.*село\b','Крым, село ',s))
#                 .apply(lambda s: re.sub(r',\s*,',', ',s))
#                 .apply(lambda s: re.sub(r' +',' ',s))
#             )
# 
#     
    
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
class LocationUpdater:

    def __init__(self, locator=GeocoderOSM() ):   #, address_transformer=AddressTransformer(),):
        #  self._atr = address_transformer
        self._locator = locator
    
    def transform(self,adr,loc=pd.DataFrame([],columns=['adr','latitude','longitude',]),show_pbar=False,):
        logging.info(f'LocationUpdater: {len(loc)} addresses in location table')
        
        # собираем все адреса в один список
        loc_all = loc.merge(adr,how='outer',on='adr').drop_duplicates().reset_index(drop=True)
        logging.info(f'LocationUpdater: {len(loc_all)} addresses total')
        
        # собираем все адреса с геопозицией
        loc_def = loc_all[~loc_all['latitude'].isnull()].reset_index(drop=True)
        logging.info(f'LocationUpdater: {len(loc_def)} addresses defined')
        
        # собираем все адреса без геопозиции
        loc_undef = loc_all[loc_all['latitude'].isnull()][['adr']].reset_index(drop=True)
        logging.info(f'LocationUpdater: {len(loc_undef)} addresses undefined')
        
        if len(loc_undef)<1: return loc_def.reset_index(drop=True)  

        # adr_tr = self._atr.transform(loc_undef['adr']) # чистим адреса для определения геопозиции
        # adr_tr = loc_undef['adr'] # чистим адреса для определения геопозиции

        loc_undef_tr = self._locator.transform(  loc_undef['adr'], show_pbar=show_pbar ) # ищем геопозицию

        # восстанавливаем соответствие оригинальных и очищенных адресов 
        loc_undef = pd.concat([
                loc_undef,
                loc_undef_tr.drop(columns=['adr',]),
            ],axis=1)

        loc_undef = loc_undef[ ~loc_undef['longitude'].isnull() ].reset_index(drop=True)

        logging.info(f'LocationUpdater: {len(loc_undef)} new addresses found')

        # собираем обновлённую таблицу адресов
        return pd.concat([loc_def,loc_undef]).reset_index(drop=True)  
    


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
if __name__ == '__main__': pass
