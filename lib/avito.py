#!python3
# -*- coding: utf-8 -*-
#
#  парсер объявлений Авито.ру
#
#  Evgeny S. Borisov <parser@mechanoid.su>  
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

# import sys 
# import os
import logging

import re
from datetime import datetime as dtm

# from tqdm.notebook import tqdm
import pandas as pd
from bs4 import BeautifulSoup

from datetime import datetime as dtm
# from os import listdir

from lib.parser import AdsListParser

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
class AvitoParser(AdsListParser):
    
    def __init__(self,driver,base_url='https://www.avito.ru/',):
        super().__init__(
            driver=driver, 
            base_url=base_url,
            item_tag=['div',{'data-marker':'item'},],
            paginator_url_param='p',
        )
        logging.info('AvitoParser: init')

        self._npages = 0


    def _parse_item(self,tag): 
        return { 'avito_id': tag.attrs['data-item-id'], 'text':tag.text, } 
 
    def _is_last_page(self,root,p): 
        return (p+1) > self._npages
 
    # загрузить список объявлений не более page_limit страниц 
    def load(self, req_param, npage_start=1, npage_end=100, keep_html=False,): 

        self._npages = self._parse_pages_count( self._base_url + '?' + req_param+'&p=1'  )
        logging.info(f'AvitoParser: {self._npages} pages for read')
        return super().load(req_param=req_param, npage_start=npage_start, npage_end=npage_end, keep_html=keep_html,) 

    def _parse_pages_count(self, url):
        _,root,_= self._read_page(url,npage=1) 
        pp = re.sub( r'.*?p=', '', root.find_all('a',{'class':'pagination-page'})[-1].attrs['href'] ) 
        return 1 if not re.match(r'\d{1,3}', pp) else int(pp)
 


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
class AvitoParserRealty(AvitoParser):
    
    @classmethod
    def _parse_item(cls,tag):
        return {    
            'avito_id': tag.attrs['data-item-id'],   # https://www.avito.ru/<avito_id>
            'title': cls._parse_item_tile(tag),
            'price': cls._parse_item_price(tag),
            'obj_name': cls._parse_item_dev_name(tag),
            'adr': cls._parse_item_adr(tag),
            'description': cls._parse_item_description(tag),
            }
        
    @staticmethod
    def _parse_item_tile(tag):
        try:
            return tag.find('a',attrs={'itemprop':'url'}).attrs['title']
        except:
            return ''    
      
    @staticmethod
    def _parse_item_price(tag):
        try:
            return tag.find('meta',attrs={'itemprop':'price'}).attrs['content']
        except:
            return ''
        
    @staticmethod
    def _parse_item_dev_name(tag):
        try:
            return tag.find('div',{'data-marker':'item-development-name'}).text
        except:
            return '' 

    @staticmethod
    def _parse_item_adr(tag):
        regex_address = re.compile('geo-address-.*')
        try:
            return tag.find('div',{'class':regex_address}).text
            # return tag.find('span',{'class':regex_address}).text
        except:
            return '' 
            
    @staticmethod
    def _parse_item_description(tag):
        regex_address = re.compile('geo-address-.*')
        try:
            return tag.find('meta',attrs={'itemprop':'description'}).attrs['content']
        except:
            return ''

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
class AvitoDataCleanerRealtyFlat:
    
    def transform(self,data):
        #symb_lat = 'yexapocEXAPOCTHKBM'
        #symb_rus = 'уехаросЕХАРОСТНКВМ'
        #l2r = str.maketrans(symb_lat,symb_rus)

        df = data.copy()
        df['title'] = df['title'].str.lower().str.extract( r'.*«(.*)».*',expand=False)
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
            df['adr'].str.match('.*СТ .*') 
            | df['adr'].str.match('.*СНТ .*') 
            | df['adr'].str.lower().str.match('.*садов.*')
        )

        df['adr'] = (
            df['adr'] 
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

        # df['avito_id'] = df['avito_id'].astype(int)

        df['price'] = df['price'].astype(int)
        df['nrooms'] = df['nrooms'].fillna('0').astype(int)
        df['floor'] = df['floor'].fillna('0').astype(int)
        df['nfloors'] = df['nfloors'].fillna('0').astype(int)
        df['area'] = df['area'].fillna('0.').astype(float)
        df['priceM'] = df['price']/1e6
        df['is_last_floor'] = ( df['floor'] == df['nfloors'] )

        return df

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
class AvitoDataCleanerRealtyLand:
    
    def transform(self,data):
        df = data.copy()
        
        #symb_lat = 'yexapocEXAPOCTHKBM'
        #symb_rus = 'уехаросЕХАРОСТНКВМ'
        #l2r = str.maketrans(symb_lat,symb_rus) 
        
        df['title'] = df['title'].str.extract( r'«(.*)»',expand=False) 
        #.apply(lambda s: s.translate(l2r) )
        
        area = df['title'].str.extract( r'(\d+,?\d*)\s*(сот|га)',expand=True)
        area.columns=['area','area_unit']
        df = pd.concat([df,area],axis=1)
                       
        df['is_IJS'] = df['title'].str.lower().str.match(r'.*ижс.*')
        df['obj_name'] = df['obj_name'].fillna('')
        
        df['area'] = df['area'].fillna('0.').str.replace(',','.').astype(float)
        df.loc[ df['area_unit']=='га', 'area' ] = df.query('area_unit=="га"')['area']*100.
        df = df.drop(columns=['area_unit'])
        
        df['price'] = df['price'].astype(int)
        df['priceM'] = df['price']/1e6
        df['priceMU'] = df['priceM']/df['area']

        area_bins = [ 0., 1., 2., 4., 8., 20., 1e6, ]
        labels = [ '<1', '1-2','2-4', '4-8', '8-20', '20+' ]
        # labels = [ 'tiny', 'small','medium', 'big', 'large', 'huge' ]
        df['area_size_category'] = pd.cut( df['area'], bins = area_bins, labels=labels)

        return df

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
class AvitoDataCleanerRealtyHouse:
    
    def transform(self,data): 
        df = data.copy()
        df['title'] = df['title'].str.lower().str.extract( r'.*«(.*)».*',expand=False)
        
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
            df['adr'].str.match('.*СТ.*') 
            | df['adr'].str.match('.*СНТ.*') 
            | df['adr'].str.match('.*ТСН.*') 
            | df['adr'].str.lower().str.match('.*садов')
        ) 
        
        area = df['title'].str.extract( r'(\d+,?\d*)\s*(сот|га)',expand=True)
        area.columns=['land_area','land_area_unit']
        df = pd.concat([df,area],axis=1)
                       
        df['obj_name'] = df['obj_name'].fillna('')
        
        df['house_area'] = df['house_area'].fillna('0.').str.replace(',','.').astype(float)
        df['land_area'] = df['land_area'].fillna('0.').str.replace(',','.').astype(float)
        df.loc[ df['land_area_unit']=='га', 'land_area' ] = df.query('land_area_unit=="га"')['land_area']*100.
        df = df.drop(columns=['land_area_unit'])
        
        df['price'] = df['price'].astype(int)
        df['priceM'] = df['price']/1e6

        # [ 'tiny', 'small','medium', 'big', 'large', 'huge' ]
        df['land_size_category'] = pd.cut( 
                df['land_area'], 
                bins =  [ 0., 1., 2., 4., 8., 20., 1e6, ], 
                labels = [ '<1', '1-2','2-4', '4-8', '8-20', '20+' ],
        )
        
        df['house_size_category'] = pd.cut( 
                df['house_area'], 
                bins = [ 0., 30., 50., 70., 150., 300., 1e6, ], 
                labels = [ '<30', '30-50','50-70', '70-150', '150-300', '300+' ],
            )
        
        return df

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
if __name__ == '__main__': pass
