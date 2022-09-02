#!python3
# -*- coding: utf-8 -*-
#
#  скачиваем данные с помощью виртуального браузера 
#
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

import logging

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.options import FirefoxProfile

# !pacman -S firefox firefox-i18n-r  geckodriver
# !pip install selenium

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
class DownloaderSeleniumFirefox():
    
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
        html = ''
        try:
            html = self._read_page(url) # читаем страницу 

        except Exception as e:
            logging.error(e) # перехватываем и логируем описания возникших ошибок

        finally: # завершение процесса чтения
            return  html # выдаём полученный html
        
    # читаем страницу по url
    def _read_page(self,url): 
        self._driver.get(url)
        return self._driver.page_source

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
if __name__ == '__main__': pass
