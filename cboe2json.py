#! /usr/bin/env python
# -*- coding: utf-8 -*
import pandas as pd
from argparse import ArgumentParser
import os
from datetime import datetime
import re


column_names = ['name', 'last_price', 'volume', 'open_interest']
columns_dtypes = {'name': str, 'last_price': float, 'volume': int, 'open_interest': int}
expiration_month_codes = {'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5, 'F': 6, 'G': 7, 'H': 8, 'I': 9, 'J': 10, 'K': 11, 'L': 12, 'M': 1, 'N': 2, 'O': 3, 'P': 4, 'Q': 5, 'R': 6, 'S': 7, 'T': 8, 'U': 9, 'V': 10, 'W': 11, 'X': 12}
ticker = None

def cboe_to_json(input_file_path: str, output_folder: str):
    try:
        # Get session date from the input filename
        session_date_input_format = '%Y%m%d'
        session_date_output_format = '%d/%m/%Y'
        numbers_in_path = re.findall('\d+', input_file_path)
        session_date = datetime.strptime(numbers_in_path[-1], session_date_input_format).strftime(session_date_output_format)
        
        # Load calls
        dfc = pd.read_csv(input_file_path, sep=',', decimal='.', header=None, names=column_names, dtype=columns_dtypes, usecols=[0, 1, 5, 6], skiprows=3)
        dfc = dfc[dfc.name.str.contains('-') == False]  # Keep contract names without '-' (not exchange specific)
        dfc['right'] = 'C'
        dfc['session_date'] = session_date
        dfc = dfc.join(dfc['name'].apply(contract_name_to_columns))
        
        # Load puts
        dfp = pd.read_csv(input_file_path, sep=',', decimal='.', header=None, names=column_names, dtype=columns_dtypes, usecols=[7, 8, 12, 13], skiprows=3)
        dfp = dfp[dfp.name.str.contains('-') == False]  # Keep contract names without '-' (not exchange specific)
        dfp['right'] = 'P'
        dfp['session_date'] = session_date
        dfp = dfp.join(dfp['name'].apply(contract_name_to_columns))
        
        df = pd.concat([dfc, dfp])
        
        output_path = '{}.json'.format(numbers_in_path[-1])
        if output_folder:
            output_path = os.path.join(output_folder, output_path)
        df.to_json(output_path, orient='records')
    except Exception as e:
        print('ERROR while reading file {}: {}'.format(input_file_path, e))
        
        
def contract_name_to_columns(name: str):
    tokens = name.split()
    strike = float(tokens[2])
    contract_name = tokens[-1]
    numbers_in_contract_name = re.findall('\d+', contract_name)
    start_pos = contract_name.index(numbers_in_contract_name[0])
    expiration_date = cboe_strdate_to_datetime(contract_name[start_pos:start_pos+5])
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
    parser.add_argument('-o', '--output_folder', type=str,
                        help='Determines the output  folder')   
    args = parser.parse_args()
    
    output_folder = None
    if args.output_folder:
        output_folder = args.output_folder
    
    if os.path.exists(args.input_file):
        if os.path.isfile(args.input_file):
            print('Reading file {}'.format(args.input_file))
            cboe_to_json(args.input_file, output_folder)
        elif os.path.isdir(args.input_file):
            # Convert all available daily files data
            [cboe_to_json(os.path.join(args.input_file, f), output_folder) for f in os.listdir(args.input_file) if os.path.isfile(os.path.join(args.input_file, f)) and f.lower().endswith('.dat')]
    else:
        print('ERROR: input file {} does not exist'.format(args.input_file))