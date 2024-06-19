#!python3
# -*- coding: utf-8 -*-
#
#
#  Evgeny S. Borisov <parser@mechanoid.su>  
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

# import sys 
# import os
import logging
import re

import pandas as pd
from datetime import datetime 



class CleanerFlat:
    
    @classmethod
    def transform(cls,data):
        #symb_lat = 'yexapocEXAPOCTHKBM'
        #symb_rus = 'уехаросЕХАРОСТНКВМ'
        #l2r = str.maketrans(symb_lat,symb_rus)

        df = data.copy()
        df['title'] = df['title'].str.lower() #.str.extract( r'.*«(.*)».*',expand=False)
        df['nrooms'] = df['title'].str.extract( r'.*(\d)-к. .*',expand=False)
        df['floor'] = df['title'].str.extract( r'.*(\d+)/\d+.эт.*',expand=False)
        df['nfloors'] = df['title'].str.extract( r'.*\d+/(\d+).эт.*',expand=False)
        df['area'] = (
            df['title']
            .str.extract( r'.*, ([\d,]+).*м²,.*',expand=False)
            .str.replace(',','.')
        )

        df['is_studio'] = df['title'].str.lower().str.match(r'.*студи.*')
        df['is_apartment'] = df['title'].str.lower().str.match(r'.*апартамент.*')
        df['is_part'] = df['title'].str.lower().str.match(r'.*дол.*')
        df['is_auction'] = df['title'].str.lower().str.match(r'.*аукци.*')
        df['is_openspace'] = df['title'].str.lower().str.match(r'.*своб.*планир.*')
        df['is_roof'] = df['description'].str.lower().str.match('.*мансард.*')
        df['is_SNT'] = (
            df['address'].str.match('.*СТ .*') 
            | df['address'].str.match('.*СНТ .*') 
            | df['address'].str.lower().str.match('.*садов.*')
        )

        df['address'] = (
            df['address'] 
                .apply(lambda s: re.sub(r'(\d)(к\d)',r'\1 \2',s))
                .apply(lambda s: re.sub(r'\bш\.',' шоссе ',s) )
                .apply(lambda s: re.sub(r'\bпр-т\b',' проспект ',s) )
                .apply(lambda s: re.sub(r'\bпер\.',' перeулок ',s) )
                .apply(lambda s: re.sub(r'\bб-р\b',' бульвар ',s) )
                .apply(lambda s: re.sub(r'\bс\.',' село ',s) )
                .apply(lambda s: re.sub(r'\bпос\. городского типа\b.',' ',s) )
                .apply(lambda s: re.sub(r'\bпос[её]лок городского типа\b.',' ',s) )
                .apply(lambda s: re.sub(r'\bнаб\.',' набережная ',s) )
                .apply(lambda s: re.sub(r'\bпл\.',' площадь ',s) )
                .apply(lambda s: re.sub(r'\bул\.',' улица ',s) )
                .apply(lambda s: re.sub(r'\bпос\.',' посёлок ',s) )
                .apply(lambda s: re.sub(r'\bпр\.',' проезд ',s) )
                .apply(lambda s: re.sub(r'\bпр-д',' проезд ',s) )
                .apply(lambda s: re.sub(r'садоводческое некоммерческое товарищество',' СНТ ',s) )
                .apply(lambda s: re.sub(r'садовое некоммерческое товарищество',' СНТ ',s) )
                .apply(lambda s: re.sub(r'садоводческое товарищество',' СТ ',s) )
                .apply(lambda s: re.sub(r'садовое товарищество',' СТ ',s) )
                .apply(lambda s: re.sub(r',\s*,',', ',s))
                .apply(lambda s: re.sub(r'  +',' ',s))
            )

        df['price'] = df['price'].astype(int)
        df['nrooms'] = df['nrooms'].fillna('0').astype(int)
        df['floor'] = df['floor'].fillna('0').astype(int)
        df['nfloors'] = df['nfloors'].fillna('0').astype(int)
        df['area'] = df['area'].fillna('0.').astype(float)
        df['priceM'] = df['price']/1e6
        df['is_last_floor'] = ( df['floor'] == df['nfloors'] )
        return df

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

class CleanerLand:
    
    @classmethod
    def transform(cls,data):
        df = data.copy()
        
        #symb_lat = 'yexapocEXAPOCTHKBM'
        #symb_rus = 'уехаросЕХАРОСТНКВМ'
        #l2r = str.maketrans(symb_lat,symb_rus) 
        
        df['title'] = df['title'].str.lower()
        # df['title'] = df['title'].str.extract( r'«(.*)»',expand=False) 
        #.apply(lambda s: s.translate(l2r) )
        
        area = df['title'].str.extract( r'(\d+,?\d*)\s*(сот|га)',expand=True)
        area.columns=['area','area_unit']
        df = pd.concat([df,area],axis=1)
                       
        df['is_IJS'] = df['title'].str.lower().str.match(r'.*ижс.*')
        # df['obj_name'] = df['obj_name'].fillna('')
        
        df['area'] = df['area'].fillna('0.').str.replace(',','.').astype(float)
        df.loc[ df['area_unit']=='га', 'area' ] = df.query('area_unit=="га"')['area']*100.
        df = df.drop(columns=['area_unit'])
        
        df['price'] = df['price'].astype(int)
        df['priceM'] = df['price']/1e6
        df['priceMU'] = df['priceM']/df['area']

        #area_bins = [ 0., 1., 2., 4., 8., 20., 1e6, ]
        #labels = [ '<1', '1-2','2-4', '4-8', '8-20', '20+' ]
        # labels = [ 'tiny', 'small','medium', 'big', 'large', 'huge' ]
        #df['area_size_category'] = pd.cut( df['area'], bins = area_bins, labels=labels)

        df['area_size_category'] = pd.cut( 
                df['area'], 
                bins =  [ 0., 1., 2., 4., 8., 12., 20., 1e6, ], 
                labels = [ '<1', '1-2','2-4', '4-8', '8-12', '12-20', '20+' ],
        )

        return df


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
class CleanerHouse:
    
    @classmethod
    def transform(self,data): 
        df = data.copy()
        df['title'] = df['title'].str.lower()
        
        # df['title'] = df['title'].str.lower().str.extract( r'.*«(.*)».*',expand=False)
        
        df['house_area'] = (
            df['title']
            .str.extract( r'([\d,]+)\s*м²',expand=False)
            .str.replace(',','.')
        )

        df['is_part'] = (
            df['description'].str.lower().str.match(r'.*\d+/\d+\s*(часть)?\s*(дом|дол).*')
            | df['description'].str.lower().str.match(r'.*часть\s*(дом|дол).*')
            | df['description'].str.lower().str.match(r'.*продам\s*(дол|часть).*')
            | df['description'].str.lower().str.match(r'.*дуплекс.*')
            | df['description'].str.lower().str.match(r'.*две семьи.*')
        )
        
        df['is_townhouse'] = (
            df['description'].str.lower().str.match(r'.*таунхаус.*')
            | df['title'].str.lower().str.match(r'.*таунхаус.*')
        )

        df['is_SNT'] = (
            df['address'].str.match('.*СТ.*') 
            | df['address'].str.match('.*СНТ.*') 
            | df['address'].str.match('.*ТСН.*') 
            | df['address'].str.lower().str.match('.*садов')
        ) 
        
        area = df['title'].str.extract( r'(\d+,?\d*)\s*(сот|га)',expand=True)
        area.columns=['land_area','land_area_unit']
        df = pd.concat([df,area],axis=1)
                       
        # df['obj_name'] = df['obj_name'].fillna('')
        
        df['house_area'] = df['house_area'].fillna('0.').str.replace(',','.').astype(float)
        df['land_area'] = df['land_area'].fillna('0.').str.replace(',','.').astype(float)
        df.loc[ df['land_area_unit']=='га', 'land_area' ] = df.query('land_area_unit=="га"')['land_area']*100.
        df = df.drop(columns=['land_area_unit'])
        
        df['price'] = df['price'].astype(int)
        df['priceM'] = df['price']/1e6

#        # [ 'tiny', 'small','medium', 'big', 'large', 'huge' ]
#        df['land_size_category'] = pd.cut( 
#                df['land_area'], 
#                bins =  [ 0., 1., 2., 4., 8., 20., 1e6, ], 
#                labels = [ '<1', '1-2','2-4', '4-8', '8-20', '20+' ],
#        )
#        
#        df['house_size_category'] = pd.cut( 
#                df['house_area'], 
#                bins = [ 0., 30., 50., 70., 150., 300., 1e6, ], 
#                labels = [ '<30', '30-50','50-70', '70-150', '150-300', '300+' ],
#            )

        df['land_size_category'] = pd.cut( 
                df['land_area'], 
                bins =  [ 0., 1., 2., 4., 8., 12., 20., 1e6, ], 
                labels = [ '<1', '1-2','2-4', '4-8', '8-12', '12-20', '20+' ],
        )
 
        df['house_size_category'] = pd.cut( 
                df['house_area'], 
                bins = [ 0., 30., 50., 70., 110., 180., 300., 1e6, ], 
                labels = [ '<30', '30-50','50-70', '70-110','110-180', '180-300', '300+' ],
            )
        
 
        return df

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
if __name__ == '__main__': pass
