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

from tqdm.notebook import tqdm
import pandas as pd
from bs4 import BeautifulSoup

from datetime import datetime as dtm
from os import listdir
# from .downloader import DownloaderSeleniumFirefox

#from selenium import webdriver
#from selenium.webdriver.firefox.options import Options
#from selenium.webdriver.firefox.options import FirefoxProfile
# !pacman -S firefox firefox-i18n-r  geckodriver
# !pip install selenium

import re
from datetime import datetime as dtm
from bs4 import BeautifulSoup

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
class AvitoDownloader:
    
    def __init__(self,driver, base_url='https://www.avito.ru'):
        logging.info('AvitoDownloader: downloader init')
        self._base_url = base_url
        self._driver = driver # ссылка на открытый браузер
        
        
    # загрузить список объявлений Авито
    # из раздела url_ext ( 'sevastopol/kvartiry/prodam' )
    # не более page_limit страниц (если неопределенно то все страницы)
    def load(self, avito_path, page_limit=None, show_pbar=False, keep_html=False): 
        html = [] # считанный "чистый" html
        data = [] # данные извлечённые парсером из html
        try:
            if re.match('^http.*',avito_path):
                logging.warning('AvitoDownloader: incorrect avito_path')

            url = self._base_url + '/' + avito_path + '?'
            
            # читаем и парсим оставшиеся страницы списка объявлений (начиная со второй)
            logging.info('AvitoDownloader: start read and parse pages...')

            page,root,src = self._read_page(url) # читаем и парсим первую страницу списка объявлений
            data.extend(page)
            if keep_html: html.append(src)
                
            # считываем количество страниц, на которые поделен список объявлений
            npages = self._get_pages_count(root,page_limit=page_limit)
            
            npages_ = tqdm(range(2,npages+1)) if show_pbar else range(2,npages+1)
            for p in npages_: 
                # читаем и парсим страницу p списка объявлений
                page,_,src = self._read_page(url+f'&p={p}',npage=p) 
                data.extend(page)
                if keep_html: html.append(src)
                           
        except Exception as e:
            logging.error(e) # перехватываем и логируем описания возникших ошибок

        finally: # завершение процесса чтения
            data = pd.DataFrame(data).dropna()
            data['ts']  = dtm.now()
            # выдаём список полученных объявлений и их исходный html
            return (data,html) if keep_html else data 
                 
          
    # читаем страницу Авито по url
    def _read_page(self,url,npage=1): 
        html = self._driver.get(url)
        root = BeautifulSoup(html,'html.parser')
        return self._parse_page(root,npage=npage),root, html,  

    @classmethod
    def _parse_page(cls, root, npage):
        return [ 
            cls._parse_item(tag)|{'avito_page':npage,} 
            for tag in root.find_all('div',{'data-marker':'item'}) 
        ]
        
    @staticmethod
    def _parse_item(tag): 
        return { 'avito_id': tag.attrs['data-item-id'], 'text':tag.text, } # { 'html':str(tag), }

    @classmethod
    def _get_pages_count(cls,root,page_limit):
        pages = cls._parse_pages_count(root)
        logging.info(f'{pages} pages for read')
        if not(page_limit is None): 
            pages = min(pages,page_limit+1)
            logging.info(f'apply page limit - {pages} pages')
        return pages
            
    @staticmethod
    def _parse_pages_count(root):
        pp = re.sub( r'.*?p=', '', root.find_all('a',{'class':'pagination-page'})[-1].attrs['href'] ) 
        return 1 if not re.match(r'\d{1,3}', pp) else int(pp)



# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
class AvitoDownloaderRealty(AvitoDownloader):
    
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
if __name__ == '__main__': pass
