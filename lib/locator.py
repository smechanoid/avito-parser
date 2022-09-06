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

from tqdm.notebook import tqdm
import pandas as pd

from geopy.geocoders import Nominatim


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
class GeocoderOSM:
    
    def __init__(self,):
        user_agent='Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0'
        self._geolocator = Nominatim(user_agent=user_agent)
   
    def transform(self,loc,show_pbar=False):
        # ищем геометку по адресу
        pos =(
            loc.progress_apply(self._get_coo).apply(pd.Series)
            if show_pbar
            else loc.apply(self._get_coo).apply(pd.Series)
        )
        return pd.concat([ loc,pos ],axis=1)
        
    def _get_coo(self,adr):
        adr_ = adr.split(',')
        loc = self._geolocator.geocode(adr_) # пробуем определить координаты
        truncated = False
        while True:
            if not (loc is None): # нашел...
                return {'latitude':loc.latitude,'longitude':loc.longitude,'truncated':truncated }#,adr_

            # ...не нашел...
            if( len(adr_) < 3 ): break # адрес слишком короткий для сокращения
            adr_ = adr_[:-1] # выкидываем часть адреса (номер дома)
            loc = self._geolocator.geocode( adr_) # ... и пробуем ещё раз
            truncated = True

        return {'latitude':None,'longitude':None,'truncated':None, }

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
class AddressTransformer:
    
    # чистим строку адреса
    def transform(self,adr): 
        return adr
    
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
class AddressTransformerSev(AddressTransformer):
    
    def transform(self,adr): 
        symb_lat = 'yexapocEXAPOCTHKBM'
        symb_rus = 'уехаросЕХАРОСТНКВМ'
        l2r = str.maketrans(symb_lat,symb_rus) 
        return (
                adr
                .apply(lambda s: s.translate(l2r) )
                .apply(lambda s: re.sub(r'\b[Сс]евастополь\b','',s))
                .apply(lambda s: re.sub(r'\bмикрорайон\b',' ',s))
                .apply(lambda s: re.sub(r'\bмуниципальный округ\b',' район ',s))
                .apply(lambda s: re.sub(r'\bкотт?еджный пос[ёе]лок\b',' ',s))
                .apply(lambda s: re.sub(r'\bпос[ёе]лок\b',' ',s))
                .apply(lambda s: re.sub(r'^','Севастополь, ',s))
                # .apply(lambda s: re.sub(r'[Сс]евастополь.*село\b','Крым, село ',s))
                .apply(lambda s: re.sub(r',\s*,',', ',s))
                .apply(lambda s: re.sub(r' +',' ',s))
            )

    
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
class LocationUpdater:

    def __init__(self,address_transformer=AddressTransformer(),):
        self._atr = address_transformer
    
    def transform(self,adr,loc=pd.DataFrame([],columns=['adr','latitude','longitude','truncated']),show_pbar=False,):
        logging.info(f'LocationUpdater: {len(loc)} addresses in location table')
        
        # собираем все адреса в один список
        loc_all = loc.merge(adr,how='outer').drop_duplicates().reset_index(drop=True)
        logging.info(f'LocationUpdater: {len(loc_all)} addresses total')
        
        # собираем все адреса с геопозицией
        loc_def = loc_all[~loc_all['latitude'].isnull()]
        logging.info(f'LocationUpdater: {len(loc_def)} addresses defined')
        
        # собираем все адреса без геопозиции
        loc_undef = loc_all[loc_all['latitude'].isnull()][['adr']]
        logging.info(f'LocationUpdater: {len(loc_undef)} addresses undefined')
        
        if len(loc_undef)<1: return loc_def.reset_index(drop=True)  

        # чистим адреса без геопозиции
        loc_undef_tr = self._atr.transform(loc_undef['adr'])
        # ищем геопозицию
        loc_undef_tr = GeocoderOSM().transform( loc_undef_tr, show_pbar=show_pbar )
        # собираем список новых адресов
        loc_undef = pd.concat([
                loc_undef,
                loc_undef_tr[['latitude','longitude','truncated']]
            ],axis=1).dropna()
        logging.info(f'LocationUpdater: {len(loc_undef)} new addresses found')

        # собираем обновлённую таблицу адресов
        return pd.concat([loc_def,loc_undef]).reset_index(drop=True)  
        # return loc_def.reset_index(drop=True) if len(loc_undef)<1 else pd.concat([loc_def,loc_undef]).reset_index(drop=True)  
    
# LocationUpdater(address_transformer=AddressTransformerSev(),).transform(data['adr'],loc)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
if __name__ == '__main__': pass
