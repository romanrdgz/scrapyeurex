#! /usr/bin/env python
# -*- coding: utf-8 -*
from selenium import webdriver
import os
import time
import cboe2json


FIVE_MINUTES = 300
cboe_data_download_url = 'http://www.cboe.com/delayedquote/quote-table-download'
textinput_id = 'ContentTop_C005_txtTicker'
button_id = 'ContentTop_C005_cmdSubmit'
cboe_data_folder = 'raw_cboe_data'

proxy = 'http://ptmproxy.gmv.es'
PROXY_PORT = 80

def get_latest_data_file_url():
    '''
    Instantiates a headless browser and ... TODO
    '''
    profile = webdriver.FirefoxProfile()
    '''
    profile.set_preference('network.proxy.http_port', int(PROXY_PORT))
    profile.set_preference('network.proxy.http', proxy)
    profile.set_preference('network.proxy.ssl_port', int(PROXY_PORT))
    profile.set_preference('network.proxy.ssl', proxy)
    profile.set_preference('network.proxy.ftp', proxy)
    profile.set_preference('network.proxy.ftp_port', int(PROXY_PORT))
    profile.set_preference('network.proxy.socks', proxy)
    profile.set_preference('network.proxy.socks_port', int(PROXY_PORT))
    profile.set_preference('network.proxy.type', 1)
    profile.set_preference('browser.download.panel.shown', False)
    profile.set_preference('browser.helperApps.alwaysAsk.force', False);
    profile.set_preference('browser.download.manager.showWhenStarting', False);
    profile.set_preference('browser.download.folderList', 2)
    profile.set_preference('browser.download.dir', os.path.join(os.getcwd(), cboe_data_folder))
    profile.set_preference('browser.helperApps.neverAsk.saveToDisk', "text/plain")
    '''
    # browser = webdriver.Firefox(firefox_profile=profile)
    browser = webdriver.PhantomJS()
    browser.get(cboe_data_download_url)        
    textinput = browser.find_element_by_id(textinput_id)
    button = browser.find_element_by_id(button_id)
    textinput.clear()
    textinput.send_keys('SPY')
    button.click()

    
if __name__ == '__main__':

    get_latest_data_file_url()
    
    # Convert data to json
    #meff2json.meff_to_json(meff_data_folder + download_url.split('/')[-1])
    