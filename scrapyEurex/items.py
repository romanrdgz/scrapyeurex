# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class OptionItem(scrapy.Item):
    session_date = scrapy.Field()
    strike = scrapy.Field()
    expiration_date = scrapy.Field()
    right = scrapy.Field()
    open_price = scrapy.Field()
    high_price = scrapy.Field()
    low_price = scrapy.Field()
    percentage_diff_to_prev_day = scrapy.Field()
    last_price = scrapy.Field()
    volume = scrapy.Field()
    open_interest = scrapy.Field()
    open_interest_date = scrapy.Field()
