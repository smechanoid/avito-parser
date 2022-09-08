#!python3
# -*- coding: utf-8 -*-
#
#  парсер объявлений ЦИАН.ру
#
#  Evgeny S. Borisov <parser@mechanoid.su>  
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

# import sys 
# import os
import logging

import re
from datetime import datetime as dtm
from time import sleep
from random import random

# from tqdm.notebook import tqdm
import pandas as pd
from bs4 import BeautifulSoup

from datetime import datetime as dtm
# from os import listdir

from lib.parser import AdsListParser

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
class CianParser(AdsListParser):
    
    def __init__(self,driver,base_url='https://www.cian.ru/cat.php',random_delay=10.,):
        super().__init__(
            driver=driver, 
            base_url=base_url,
            item_tag=['article',{'data-name':'CardComponent',},],
            paginator_url_param='p',
        )
        self._random_delay = random_delay
        logging.info('CianParser: downloader init')
    
    def _read_page(self,url,npage=1): 
        logging.debug(f'CianParser: {url}')
        if self._random_delay>0.: 
            ds = random()*self._random_delay
            logging.debug(f'CianParser: delay {ds:.2f} sec')
            sleep( ds )
        return super()._read_page(url,npage=npage)
    
    def _is_last_page(self,root,p): 
        try:
            pl = root.find('div',{'data-name':'Pagination',}).find_all('li')[-1].text.strip()
            logging.debug(f'CianParser: page {p}, last page "{pl}"')
            if pl=='..': return False
            return p>=int(pl)
        except Exception as e:
            logging.warning(f'CianParser: parse pagination error: {e}')
            return True
        
    def _parse_item(self,tag): 
        return { 
             'OfferTitle': self._get_title(tag),
          'OfferSubtitle': self._get_subtitle(tag),
               'Deadline': self._get_deadline(tag),
              'MainPrice': self._get_price(tag),
              'PriceInfo': self._get_price_m(tag),
               'GeoLabel': self._get_adr(tag),
              'TimeLabel': self._get_ts( tag ),  
               'LinkArea': self._get_link( tag ),
            'Description': self._get_descr(tag),
            }
    
    @staticmethod
    def _get_deadline(tag):
        try:
            return tag.find('span',{'data-mark':'Deadline',}).text
        except:
            return ''
        
    @staticmethod
    def _get_title(tag):
        try:
            return tag.find('span',{'data-mark':'OfferTitle',}).text
        except:
            return ''
        
    @staticmethod
    def _get_subtitle(tag):
        try:
            return tag.find('span',{'data-mark':'OfferSubtitle',}).text
        except:
            return ''
        
    @staticmethod
    def _get_price(tag):
        try:
            return tag.find('span',{'data-mark':'MainPrice',}).text
        except:
            return ''

    @staticmethod
    def _get_price_m(tag):
        try:
            return tag.find('p',{'data-mark':'PriceInfo',}).text
        except:
            return ''
        
    @staticmethod
    def _get_adr(tag):
        try:
            return [ t.text for t in tag.find_all('a',{'data-name':'GeoLabel',}) ]
        except:
            return []
    
    @staticmethod
    def _get_ts(tag):
        try:
            return [ t.text for t in tag.find('div',{'data-name':'TimeLabel',}).find_all('span') ]
        except:
            return []
        
    @staticmethod
    def _get_link(tag):
        try:
            return tag.find('div',{'data-name':'LinkArea',}).find('a').attrs['href']
        except:
            return ''
        
    @staticmethod
    def _get_descr(tag):
        try:
            return tag.find('div',{'data-name':'Description',}).text
        except:
            return ''


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
class CianDataCleaner:
    
    def transform(self,data):
        df = data.copy()
        df = df.rename(
            columns={
                'OfferTitle':'title',
                'OfferSubtitle':'obj_name',
                'Description':'description',
                'LinkArea':'cian_url',
            }
        )
        
        df['nrooms'] = df['title'].str.extract( r'.*(\d)-к.*',expand=False)
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
        
        df['adr'] = df['GeoLabel'].apply(lambda s: ', '.join(s) )
        
        df['is_SNT'] = (
            df['adr'].str.match('.*СТ .*') 
            | df['adr'].str.match('.*СНТ .*') 
            | df['adr'].str.lower().str.match('.*садов.*')
        )

        df['adr'] = (
            df['adr'] 
                .apply(lambda s: re.sub(r'(\d)(к\d)',r'\1 \2',s))
                .apply(lambda s: re.sub(r'\bр-н\b',' район ',s) )
                .apply(lambda s: re.sub(r'\bмкр\.',' микрорайон ',s) )
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

        df['price'] = df['MainPrice'].apply( lambda s: int( re.sub(r'\D','',s) ) )
        df['nrooms'] = df['nrooms'].fillna('0').astype(int)
        df['floor'] = df['floor'].fillna('0').astype(int)
        df['nfloors'] = df['nfloors'].fillna('0').astype(int)
        df['area'] = df['area'].fillna('0.').astype(float)
        df['priceM'] = df['price']/1e6
        df['is_last_floor'] = ( df['floor'] == df['nfloors'] )

        cols=[
            'title',
            'obj_name',
            'adr',
            'nrooms',
            'floor',
            'nfloors',
            'area',
            'is_studio',
            'is_apartment',
            'is_part',
            'is_auction',
            'is_openspace',
            'is_roof',
            'is_SNT',
            'price',
            'priceM',
            'is_last_floor',
            'cian_url',
            'description',
            'cian_page',
            'ts',

            # 'OfferSubtitle',
            # 'Deadline',
            # 'MainPrice',
            # 'PriceInfo',
            # 'GeoLabel',
            # 'TimeLabel',

            ]
        return df[cols]


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
if __name__ == '__main__': pass
