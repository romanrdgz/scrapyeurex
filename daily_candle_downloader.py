#! /usr/bin/env python
# -*- coding: utf-8 -*
from bs4 import BeautifulSoup
import requests
import csv
import os


url = 'https://es.investing.com/indices/eu-stocks-50-futures-historical-data'
fake_header = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}

data = requests.get(url, headers=fake_header).text.encode('utf-8')
soup = BeautifulSoup(data, 'lxml')
table = soup.find('table', {'id': 'curr_table'})
table_body = table.find('tbody')
first_row = table_body.findAll('tr')[0]
data = []
for cell in first_row.findAll('td'):
    data.append(cell.getText())
    
with open(os.path.join('data', 'ESTX50', 'candlestick_data.csv'), 'a') as f:
    writer = csv.writer(f)
    writer.writerow(data)