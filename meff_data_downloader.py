#! /usr/bin/env python
# -*- coding: utf-8 -*
from selenium import webdriver
import urllib
import os
import time
import meff2json


FIVE_MINUTES = 300
meff_data_download_url = "http://www.meff.com/aspx/DerEnergia/DescargaFicheros.aspx?id=esp"
meff_home = "http://www.meff.com"
meff_data_folder = "raw_meff_data/"
proxies = {
    #'http': 'http://myproxy.addr.ess:80'
}


def get_latest_data_file_url():
    '''
    Instantiates a headless browser and get latest available data file from MEFF website
    '''
    browser = webdriver.PhantomJS()
    browser.get(meff_data_download_url)        
    element_to_download = browser.find_elements_by_css_selector("a[href*='/docs/Ficheros/Descarga/dME']")[0]
    download_url = meff_home + element_to_download.get_attribute('href').split("javascript:sacaVentana('")[1].split("')")[0].replace('ME', 'RV')
    return download_url
    
    
def download_data_file(download_url):
    try:
        proxy = urllib.request.ProxyHandler(proxies)
        opener = urllib.request.build_opener(proxy)
        urllib.request.install_opener(opener)
        urllib.request.urlretrieve(download_url, meff_data_folder + download_url.split('/')[-1])
    except Exception as e:
        print('ERROR while trying to download data file with URL {}: {}'.format(download_url, e))
    else:
        print('MEFF daily data successfully downloaded from URL {}'.format(download_url))

    
if __name__ == '__main__':
    # First get a list of already downloaded raw files
    already_downloaded = os.listdir(meff_data_folder)
 
    found = True
    download_url = None
    while(found):
        # Get latest data file URL
        download_url = get_latest_data_file_url()

        found = False
        # Check if latest file has already been downloaded
        for datafile in already_downloaded:
            if download_url.endswith(datafile):
                found = True
        if found:
            time.sleep(FIVE_MINUTES)
    
    # Download latest data file
    download_data_file(download_url)
    
    # Convert data to json
    meff2json.meff_to_json(meff_data_folder + download_url.split('/')[-1])
    