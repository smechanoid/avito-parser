#!python3
# -*- coding: utf-8 -*-
#
#  парсер объявлений ЦИАН.ру
#
#  Evgeny S. Borisov <parser@mechanoid.su>  
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
import logging
import sys 
import re
import pandas as pd

# from selenium import webdriver
from selenium.webdriver.common.by import By

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
class CianItemParser:
    
    @classmethod
    def transform(cls,elem):
        return { 
             'title': cls._title(elem),
          'subtitle': cls. _subtitle(elem),
              'price': cls._price(elem),
              # 'price_info': cls._price_m(elem),
               'address': cls._address(elem),
           'description': cls._description(elem),
               'url': cls._url( elem ),
               'deadline': cls._deadline(elem),
              # 'TimeLabel': cls._get_ts(elem),
            }
        

    @classmethod
    def _title(cls,elem):
        return cls._get_text(
            elem,
            ".//*/span[contains(@data-mark,'OfferTitle')]"
        )

    @classmethod
    def _subtitle(cls,elem):
        return cls._get_text(
            elem,
            ".//*/span[contains(@data-mark,'OfferSubtitle')]"
        )
    
    @classmethod
    def _deadline(cls,elem):
        return cls._get_text(
            elem,
            ".//*/span[contains(@data-mark,'Deadline')]"
        )
    
    @classmethod
    def _price(cls,elem):
        return cls._get_text(
            elem,
            ".//*/span[contains(@data-mark,'MainPrice')]"
        ).replace('₽','').replace(' ','')
    
#    @classmethod
#    def _price_m(cls,elem):
#        return cls._get_text(
#            elem,
#            ".//*/p[contains(@data-mark,'PriceInfo')]"
#        )
#
    @classmethod
    def _address(cls,elem):
        return ', '.join( 
            cls._get_text_list(
                elem,
                ".//*/a[contains(@data-name,'GeoLabel')]"
            )
        )
    
#    @classmethod
#    def _get_ts(cls,elem):
#        return cls._get_text(
#            elem,
#            ".//*/div[contains(@data-name,'TimeLabel')]"
#        )    
    
    @classmethod
    def _url(cls,elem):
        return cls._get_attr(
            elem,
            ".//*/div[contains(@data-name,'LinkArea')]/*/a",
            'href'
        )   
    
    @classmethod
    def _description(cls,elem):
        return cls._get_text(
            elem,
            ".//*/div[contains(@data-name,'Description')]"
        )  
    
    @staticmethod
    def _get_text(elem,xpath):
        try:
            return elem.find_element(By.XPATH, xpath).text
        except:
            return ''
        
    @staticmethod
    def _get_text_list(elem,xpath):
        try:
            return [
                t.text for t in elem.find_elements(By.XPATH,xpath)
            ]
        except:
            return []  
        
#    @staticmethod
#    def _get_href_list(elem,xpath):
#        try:
#            return [
#                    t.get_attribute('href') for t in elem.find_elements(By.XPATH,xpath)
#                ]
#        except:
#            return []         
        
    @staticmethod
    def _get_attr(elem,xpath,attr):
        try:
            return elem.find_element(By.XPATH, xpath).get_attribute(attr)
        except:
            return ''

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
class CianPageParser:

    @classmethod
    def transform(cls,root):
        return [
            CianItemParser.transform(item)
            for item in root.find_elements(
                By.XPATH,
                "//*/article[contains(@data-name,'CardComponent')]"
            )   
        ]     

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
class CianParser:

    @classmethod
    def transform(cls,driver,max_pages=1024):
        data = []
        for n in range(1,max_pages):
            page =  CianPageParser().transform(driver)
            data.extend( page )
            logging.info(f'page {n}: {len(page)} items')
            try:
                cls._paginator_next(driver)
            except:
                break
                
        return data
            
        
    @classmethod
    def _paginator_next(cls,driver):
        nav = driver.find_element(
                By.XPATH,
                "//*/nav[contains(@data-name,'Pagination')]"
            )
        a = nav.find_element(By.LINK_TEXT,'Дальше')
        href = a.get_attribute('href')
        driver.get(href)
        return cls


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
if __name__ == '__main__': pass
