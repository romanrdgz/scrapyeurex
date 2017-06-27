# -*- coding: utf-8 -*-
import scrapy
from scrapyEurex.items import OptionItem
from datetime import date, datetime


class DaxSpider(scrapy.Spider):
    name = "daxspider"
    allowed_domains = ["eurexchange.com"]
    underlying_id = 17254
    url_template = 'http://www.eurexchange.com/exchange-en/products/idx/dax/{underlying_id}!quotesSingleViewOption?callPut={right}&maturityDate={expiration_date}'
    start_urls = ['http://www.eurexchange.com/exchange-en/products/idx/dax/DAX--Options/{}'.format(underlying_id)]
    
    def parse(self, response):
        # Get list of expiration dates
        expiry_dates = response.xpath('//select[@id="maturityDate"]/option/@value').extract()
        
        # Iterate each the page of each expiration date (for both call and put)
        for exp_date in expiry_dates:
            if exp_date:  # Avoids empty value from "All expiries" option
                for r in ['Call', 'Put']:
                    yield scrapy.Request(url=self.url_template.format(underlying_id=self.underlying_id, right=r, expiration_date=exp_date),
                                         callback=self.parse_opt_chain,
                                         meta={'right': r[0], 'expiration_date': exp_date})

    def parse_opt_chain(self, response):
        table_rows = response.xpath('(//table[@class="dataTable"])[1]/tbody/tr')
        # Iterate rows (skip the last one, which only includes the total volume and open interest)
        for row in table_rows[:-1]:
            item = OptionItem()
            item['right'] = response.meta.get('right')
            item['strike'] = float(row.xpath('./td[1]/span/text()').extract()[0].replace(',', ''))
            
            opt_date = datetime.strptime(response.meta.get('expiration_date'), '%Y%m').date()
            for d in range(15, 22):
                opt_date = opt_date.replace(day=d)
                if opt_date.weekday() == 4:
                    break
            item['expiration_date'] = opt_date.strftime('%d/%m/%Y')
            
            item['session_date'] = datetime.strptime(row.xpath('./td[12]/span/text()').extract()[0], '%m/%d/%Y').strftime('%d/%m/%Y')
            item['percentage_diff_to_prev_day'] = float(row.xpath('./td[10]/span/text()').extract()[0].replace('%', '').rstrip())
            item['volume'] = int(row.xpath('./td[15]/span/text()').extract()[0].replace(',', ''))
            item['open_interest'] = int(row.xpath('./td[16]/span/text()').extract()[0].replace(',', ''))
            # Open interest date can be 'n.a.' if no contract has been traded
            try:
                item['open_interest_date'] = datetime.strptime(row.xpath('./td[17]/span/text()').extract()[0], '%m/%d/%Y').strftime('%d/%m/%Y')
            except:
                item['open_interest_date'] = 'n.a.'
            
            last_price = row.xpath('./td[11]/span/text()').extract()[0].replace(',', '')
            try:
                item['last_price'] = float(last_price)
            except ValueError:
                item['last_price'] = 'N/A'
            
            open_price = row.xpath('./td[3]/span/text()').extract()[0].replace(',', '')
            try:
                item['open_price'] = float(open_price)
            except ValueError:
                item['open_price'] = 'N/A'
            
            high_price = row.xpath('./td[4]/span/text()').extract()[0].replace(',', '')
            try:
                item['high_price'] = float(high_price)
            except ValueError:
                item['high_price'] = 'N/A'
                
            low_price = row.xpath('./td[5]/span/text()').extract()[0].replace(',', '')
            try:
                item['low_price'] = float(low_price)
            except ValueError:
                item['low_price'] = 'N/A'
            
            yield item