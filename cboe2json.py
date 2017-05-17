#! /usr/bin/env python
# -*- coding: utf-8 -*
import pandas as pd
from argparse import ArgumentParser
from os import path
from datetime import datetime


column_names = ['name', 'last_price', 'volume', 'open_interest']
columns_dtypes = {'name': str, 'last_price': float, 'volume': int, 'open_interest': int}
expiration_month_codes = {'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5, 'F': 6, 'G': 7, 'H': 8, 'I': 9, 'J': 10, 'K': 11, 'L': 12, 'M': 1, 'N': 2, 'O': 3, 'P': 4, 'Q': 5, 'R': 6, 'S': 7, 'T': 8, 'U': 9, 'V': 10, 'W': 11, 'X': 12}
ticker = None

def cboe_to_json(input_file_path: str):
    # Check if given input file exists
    if path.exists(input_file_path) and path.isfile(input_file_path):
        # Check ticker and session date in the first lines of the file
        ticker = 'SPY'
        session_date = '05/05/2017'
        
        # Load calls
        dfc = pd.read_csv(input_file_path, sep=',', decimal='.', header=None, names=column_names, dtype=columns_dtypes, usecols=[0, 1, 5, 6], skiprows=3)
        dfc['right'] = 'C'
        dfc = dfc.join(dfc['name'].apply(contract_name_to_columns))
        print(dfc)
        
        # Load puts
        dfp = pd.read_csv(input_file_path, sep=',', decimal='.', header=None, names=column_names, dtype=columns_dtypes, usecols=[7, 8, 12, 13], skiprows=3)
        dfp['right'] = 'P'
        dfp = dfp.join(dfp['name'].apply(contract_name_to_columns))
        
        dfc.to_json('test.json', orient='records')
        
        
def contract_name_to_columns(name: str):
    tokens = name.split()
    strike = float(tokens[2])
    name = tokens[-1]
    # date comes after '(' and the ticker, and takes 5 chars
    start_pos = 1 + len(ticker)
    expiration_date = cboe_strdate_to_datetime(name[start_pos:start_pos+5])
    return pd.Series({'strike': strike, 'expiration_date': expiration_date})
    
    
def cboe_strdate_to_datetime(strdate: str):
    '''
    CBOE date format comes in the following 5 char format:
    - 2 first chars are for the year
    - 2 next charts are for the day of month
    - last char is a capital letter A-L for call option months 0-12, M-X for put option months
    '''
    year = 2000 + int(strdate[0:2])
    day = int(strdate[2:4])
    month = expiration_month_codes[strdate[4]]
    return datetime(year=year, month=month, day=day).strftime('%d/%m/%Y')


if __name__ == '__main__':
    # Configure the command line options
    parser = ArgumentParser()
    parser.add_argument('-i', '--input_file', type=str, required=True,
                        help='Determines the single daily zip file or folder to convert')
    args = parser.parse_args()
    
    if path.exists(args.input_file):
        if path.isfile(args.input_file):
            cboe_to_json(args.input_file)
        elif path.isdir(args.input_file):
            # Convert all available daily files data
            [cboe_to_json(path.join(args.input_file, f)) for f in listdir(args.input_file) if path.isfile(path.join(args.input_file, f)) and f.lower().endswith('.dat')]
    