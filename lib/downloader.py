#!python3
# -*- coding: utf-8 -*-
#
#  запрос данных у сервера 
#
#  Evgeny S. Borisov <parser@mechanoid.su>  
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

import logging

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.options import FirefoxProfile
import requests
from requests.exceptions import HTTPError
# import json

# !pacman -S firefox firefox-i18n-r  geckodriver
# !pip install selenium


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
class HttpGetRequest:

    def __init__( self, header_params=None, ):
        self._header_params = header_params
        # header_params = {  'x-auth-token': token, 'Content-Type': 'application/x-www-form-urlencoded', }  
        

    def get(self, url, params=None):
        # params = { 'from':d_start, 'to':d_end, }
                
        try:
            response = requests.get(url,headers=self._header_params,params=params,)
            response.raise_for_status() 
            logging.debug('HttpGetRequest: request success')
            return response.text

        except HTTPError as http_err:
            logging.error(f'HttpGetRequest: request : {http_err}')

        except Exception as err:
            logging.error(f'HttpGetRequest: request : {err}')

        return ''    


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
class DownloaderSimple:

    # загрузить данные по url
    def get(self,url):
        header_params = {
             'Content-Type':'text', 
             'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0'
             }
        # 'application/json; charset=utf-8'
        # 'text/html; charset=utf-8'
        return HttpGetRequest(header_params).get(url)

  
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
class DownloaderSeleniumFirefox:
    
    def __init__(self,profile_path,is_headless=True):
        logging.info('DownloaderSeleniumFirefox: downloader init')
        # параметры виртуального браузера
        options = Options()
        options.profile = FirefoxProfile(profile_path) 
        options.headless = is_headless
        logging.info('DownloaderSeleniumFirefox: open virtual browser')
        self._driver = webdriver.Firefox(options=options) # ссылка на браузер

    def __del__(self):
        self._driver.quit() # закрываем браузер
        logging.info('DownloaderSeleniumFirefox: close virtual browser')


    # загрузить данные по url
    def get(self,url):  
        logging.debug('DownloaderSeleniumFirefox: read page')
        try:
            return self._read_page(url) # читаем страницу 

        except Exception as e:
            logging.error(e) # перехватываем и логируем описания возникших ошибок

        return ''
        
    # читаем страницу по url
    def _read_page(self,url): 
        self._driver.get(url)
        return self._driver.page_source


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
if __name__ == '__main__': pass
