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
from datetime import datetime 
import pandas as pd

from selenium import webdriver
from selenium.webdriver.common.by import By


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
class AvitoItemParser:
    
    @classmethod
    def transform(cls,elem):
        return {
        'title': cls._title(elem),
        'price': cls._price(elem),
        # 'price_cur': cls._price_cur(elem),
        'address': cls._address(elem),
        'description': cls._description(elem),
        'url': cls._url(elem), 
        # 'avito_id': cls._avito_id(elem), 
        'development': cls._development(elem),
        }
        
    @classmethod
    def _title(cls,elem):
        return cls._get_text(
            elem,
            ".//*/h3[contains(@itemprop,'name')]"
        )
        
#     @classmethod
#     def _price(cls,elem):
#         return cls._get_data(
#             elem,
#             ".//*/p[contains(@data-marker,'item-price')]"
#         )

#    @classmethod
#    def _price_cur(cls,elem):
#        return cls._get_attr(
#            elem,
#            ".//*/meta[contains(@itemprop,'priceCurrency')]",
#            'content',
#        )
    
    @classmethod
    def _price(cls,elem):
        return cls._get_attr(
            elem,
            ".//*/meta[@itemprop='price']",
            'content',
        )
    
    @classmethod
    def _address(cls,elem):
        return cls._get_text(
            elem,
            ".//*/div[contains(@data-marker,'item-address')]"
        )
    
    @classmethod
    def _description(cls,elem):
        return cls._get_text(
            elem,
            ".//*/div[contains(@class,'item-description')]"
        )
    
    @classmethod
    def _development(cls,elem):
        return cls._get_text(
            elem,
            ".//*/p[contains(@data-marker,'item-development-name')]"
        )    

    @classmethod
    def _avito_id(cls,elem):
        return cls._get_attr( elem, '.', 'data-item-id', )
  
    @classmethod
    def _url(cls,elem):
        aid = cls._avito_id(elem)
        return '' if aid is None else f'https://www.avito.ru/{aid}'
    
    @staticmethod
    def _get_text(elem,xpath):
        try:
            return elem.find_element(By.XPATH, xpath).text
        except:
            return ''
        
    @staticmethod
    def _get_attr(elem,xpath,attr):
        try:
            return elem.find_element(By.XPATH, xpath).get_attribute(attr)
        except:
            return ''      

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
class AvitoPageParser:

    @classmethod
    def transform(cls,root):
        return [
            AvitoItemParser.transform(item)
            for item in root.find_elements(
                By.XPATH,
                "//*/div[contains(@data-marker,'item')]"
            )   
        ]  

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
class AvitoParser:

    @classmethod
    def transform(cls,driver,max_pages=1024):
        data = []
        for n in range(1,max_pages):
            page =  [ item for item in AvitoPageParser().transform(driver) if len(item['url'])>0 ]
            data.extend( page )
            logging.info(f'page {n}: {len(page)} items')
            try:
                cls._paginator_next(driver)
            except:
                break
                
        return data
        
    @classmethod
    def _paginator_next(cls,driver):
        a = driver.find_element(
                By.XPATH,
            "//*/a[contains(@data-marker,'pagination-button/nextPage')]"
            )
        href = a.get_attribute('href')
        driver.get(href)
        return cls



# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
if __name__ == '__main__': pass
