#!python3
# -*- coding: utf-8 -*-
#
#  парсер объявлений Авито.ру
#
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

import sys 
import os
import logging

from abc import ABC, abstractmethod

import re
from datetime import datetime as dt

from tqdm import tqdm
import pandas as pd
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.options import FirefoxProfile

# !pacman -S firefox firefox-i18n-r  geckodriver
# !pip install selenium

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
class AvitoDownloader(ABC):
    
    def __init__(self,profile_path):
        self._options = Options()
        self._options.profile = FirefoxProfile(profile_path) 
        self._options.headless = True
        logging.info('downloader init')


    def load(self,url,page_limit=None):         
        driver = webdriver.Firefox(options=self._options)
        logging.info('open virtual browser')

        driver.get(url)
        html = [ driver.page_source, ]
        root = BeautifulSoup(html[0])
        pages = self._get_pages_count(root)
        if not(page_limit is None): pages = min(pages,page_limit+1)
        data = self._parse_page(root,npage=1)
        logging.info(f'{pages} pages for read')

        logging.info('start read and parse pages...')
      
        # for p in tqdm(range(2,4)):
        for p in tqdm(range(2,pages)):
            driver.get(url+f'&p={p}')
            html.append( driver.page_source )
            root = BeautifulSoup(html[-1])
            data.extend( self._parse_page( root, npage=p )  )

        driver.quit()    
        
        return pd.DataFrame(data).dropna(), html

    @classmethod
    def _parse_page(cls, root, npage):
        return [ cls._parse_item(tag)|{'avito_page':npage,} for tag in root.find_all('div',{'data-marker':'item'}) ]
        
    @abstractmethod
    def _parse_item(tag): pass
    # def _parse_item(tag): return dict()

    @staticmethod
    def _get_pages_count(root):
        pp = re.sub( r'.*?p=', '', root.find_all('a',{'class':'pagination-page'})[-1].attrs['href'] ) 
        return 1 if not re.match(r'\d{1,3}', pp) else int(pp)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
class AvitoDownloaderRealty(AvitoDownloader):
    
    @classmethod
    def _parse_item(cls,tag):
        return {    
            'avito_id': tag.attrs['data-item-id'],   # https://www.avito.ru/<id>
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
            return tag.find('span',{'class':regex_address}).text
        except:
            return '' 
            
    @staticmethod
    def _parse_item_description(tag):
        regex_address = re.compile('geo-address-.*')
        try:
            return tag.find('meta',attrs={'itemprop':'description'}).attrs['content']
        except:
            return ''        

        
# 'cur':tag.find('meta',attrs={'itemprop':'priceCurrency'}).attrs['content'],
# tag.find('div',attrs={'data-marker':'item-address'}).text,           


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
class AvitoDataCleanerRealty:
    
    @staticmethod
    def transform(data):
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
                .str.replace(' ш.,',' шоссе,')
                .str.replace('пр-т','проспект')
            )

        # df['is_fiolent'] = (
        #    df['description'].str.lower().str.match('.*фиолент.*')
        #    | df['adr'].str.lower().str.match('.*фиолент.*')
        #)
        # df[ df['adr'].str.match('.*СТ .*') ]
        # df[ df['adr'].str.match('.*СНТ .*') ]
        # df[ df['adr'].str.match('.*садов.*') ]
        # df[ df['description'].str.match('.*садов.*') ]
        # df['avito_id'] = df['avito_id'].astype(int)

        df['price'] = df['price'].astype(int)
        df['nrooms'] = df['nrooms'].fillna('0').astype(int)
        df['floor'] = df['floor'].fillna('0').astype(int)
        df['nfloors'] = df['nfloors'].fillna('0').astype(int)
        df['area'] = df['area'].fillna('0.').astype(float)
        df['priceM'] = df['price']/1e6
        df['is_last_floor'] = ( df['floor'] == df['nfloors'] )

        cols = [
         'adr',
         'obj_name',
         'title',
         'priceM',
         'nrooms',
         'floor',
         'nfloors',
         'area',
         'is_studio',
         'is_apartment',
         'is_part',
         'is_auction',
         'is_openspace',
         'is_SNT',
         # 'is_fiolent',   
         'is_last_floor', 
         'is_roof',   
         'description',
         'price',
         'avito_page',
         'avito_id',
        ]

        return df[cols]



# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
if __name__ == '__main__': pass
