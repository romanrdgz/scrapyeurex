#! /usr/bin/env python
# -*- coding: utf-8 -*
import os
import scrapy
from scrapy.crawler import CrawlerProcess
from scrapyEurex.spiders.daxspider import DaxSpider
from scrapyEurex.spiders.estx50spider import Estx50Spider
from datetime import datetime
import time


session_date_format = '%Y%m%d'
session_date = datetime.now().strftime(session_date_format)

try:
    process = CrawlerProcess({
        'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)',
        'FEED_FORMAT': 'json',
        'FEED_URI': os.path.join('data', 'ESTX50', '{}.json'.format(session_date)),
        'DOWNLOAD_DELAY': 3,
        'LOG_STDOUT': True,
        'LOG_FILE': 'scrapy_output.txt',
        'ROBOTSTXT_OBEY': False,
        'RETRY_ENABLED': True,
        'RETRY_HTTP_CODES': [500, 503, 504, 400, 404, 408],
        'RETRY_TIMES': 5
    })
    process.crawl(Estx50Spider)
    process = CrawlerProcess({
        'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)',
        'FEED_FORMAT': 'json',
        'FEED_URI': os.path.join('data', 'DAX', '{}.json'.format(session_date)),
        'DOWNLOAD_DELAY': 3,
        'LOG_STDOUT': True,
        'LOG_FILE': 'scrapy_output.txt',
        'ROBOTSTXT_OBEY': False,
        'RETRY_ENABLED': True,
        'RETRY_HTTP_CODES': [500, 503, 504, 400, 404, 408],
        'RETRY_TIMES': 5
    })
    process.crawl(DaxSpider)
    process.start()  # the script will block here until the crawling is finished
except Exception as e:
    print('ERROR while crawling EUREX option chains: {}'.format(e))
else:
    print('Eurex option chains successfuly crawled')
