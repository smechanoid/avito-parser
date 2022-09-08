#!python3
# -*- coding: utf-8 -*-
#
#  парсер объявлений 
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
# from os import listdir


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
class AdsListParser:
    
    def __init__( self,driver, base_url, item_tag, paginator_url_param='p', ):
        logging.info('AdsListParser: downloader init')
        self._base_url = base_url
        self._paginator_url_param = paginator_url_param
        self._driver = driver
        self._item_tag = item_tag # ['article',{'data-name':'CardComponent',}]

    # загрузить список объявлений не более page_limit страниц 
    def load(self, req_param, npage_start=1, npage_end=100, keep_html=False,): 
        html = [] # считанный "чистый" html
        data = [] # данные извлечённые парсером из html
        try:
            url = self._base_url + '?' + req_param
            
            # читаем и парсим оставшиеся страницы списка объявлений (начиная со второй)
            logging.info('AdsListParser: start read and parse pages...')

            for p in range(npage_start, npage_end):
                # читаем и парсим страницу p списка объявлений
                page,root,src = self._read_page(url+f'&{self._paginator_url_param}={p}',npage=p) 
                data.extend(page)

                if keep_html: html.append(src)
                logging.info(f'AdsListParser: read page {p}')

                if self._is_last_page(root,p): 
                    logging.info('AdsListParser: last page detected')
                    break
                                                
        except Exception as e:
            logging.error(e) # перехватываем и логируем описания возникших ошибок


        data = pd.DataFrame(data)
        data['ts']  = dtm.now()

        # выдаём список полученных объявлений и их исходный html
        return (data,html) if keep_html else data 
          
    # читаем страницу по url
    def _read_page(self,url,npage=1): 
        html = self._driver.get(url)
        root = BeautifulSoup(html,'html.parser')
        return self._parse_page(root,npage=npage),root, html,  

    def _parse_page(self, root, npage):
        return [ 
            self._parse_item(tag)|{'page':npage,} 
            for tag in root.find_all( *self._item_tag )
        ]
    
    def _parse_item(self,tag): 
        return { 'text': tag.text, }

    def _is_last_page(self,root,p): 
        return True



# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
if __name__ == '__main__': pass    
