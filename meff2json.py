#! /usr/bin/env python
# -*- coding: utf-8 -*
import pandas as pd
import numpy as np
from argparse import ArgumentParser
import shutil
from os import listdir
from os import path
from datetime import datetime as dt
import zipfile


inner_zip_filename = 'today_rv.zip'
contracts_file = 'CCONTRACTS.C2'
contracts_stats_file = 'CCONTRSTAT.C2'
contracts_columns = ['session_date', 'contract_code', 'contract_subgroup', 'contract_type', 'strike', 'expiration_date']
contracts_dtype = {'session_date': str, 'contract_code': str, 'contract_subgroup': str, 'contract_type': str, 'strike': float, 'expiration_date': str}
contracts_stats_columns = ['contract_code', 'high_price', 'low_price', 'open_price', 'last_price', 'volume', 'open_interest']
contracts_stats_dtype = {'contract_code': str, 'high_price': float, 'low_price': float, 'open_price': float, 'last_price': float, 'volume': int, 'open_interest': int}

contract_subgroups = {'20': 'FIE', '23': 'BBVA', '28': 'SAN', '31': 'TEF', '43': 'ITX'}

def meff_to_json(input_file_path, ticker=None):
    # Check if given input file exists
    if path.exists(input_file_path) and path.isfile(input_file_path):
        # Delete tmp folder (if exists)
        if path.exists('tmp') and path.isdir('tmp'):
            shutil.rmtree('tmp')
        
        # First unzip (inside there is another zip file which also has to be unziped)
        outer_zip = zipfile.ZipFile(input_file_path, 'r')
        outer_zip.extractall('tmp')
        outer_zip.close()
        inner_zip = zipfile.ZipFile(path.join('tmp', inner_zip_filename), 'r')
        inner_zip.extractall('tmp')
        inner_zip.close()
        
        # Load contracts file
        contracts_data = pd.read_csv(path.join('tmp', contracts_file), sep=';', decimal=',',
                                     header=None, names=contracts_columns, dtype=contracts_dtype, parse_dates=[0, 5],
                                     usecols=[0, 2, 3, 4, 5, 6])
        
        # Now load contracts stats file
        contracts_stats_data = pd.read_csv(path.join('tmp', contracts_stats_file), sep=';', decimal=',',
                                           header=None, names=contracts_stats_columns, dtype=contracts_stats_dtype, parse_dates=[0],
                                           usecols=[2, 3, 4, 5, 6, 13, 15])
        
        # Join dataframes on contract_code
        df = pd.merge(contracts_data, contracts_stats_data, how='inner', on='contract_code', sort=False)
        
        # Adapt session date and expiration date to the same format used in EUREX website
        df['session_date'] = pd.to_datetime(df['session_date']).dt.strftime('%d/%m/%Y')
        df['expiration_date'] = pd.to_datetime(df['expiration_date']).dt.strftime('%d/%m/%Y')
        
        # Filter the dataframe to keep only options (rows which contain a defined strike)
        df.strike.replace('', np.nan, inplace=True)
        df.dropna(subset=['strike'], inplace=True)
        # The first char of contract code is the right initial for option contracts
        # Also, only European type options are listed for miniIBEX, but we have to filter out European type from stock options
        df['contract_code'] = df['contract_code'].apply(lambda x: np.nan if 'EU ' in x else x)
        df.dropna(subset=['contract_code'], inplace=True)
        df['right'] = df['contract_code'].apply(lambda x: x[0])
        # Delete unused columns
        del df['contract_code']
        del df['contract_type']
        
        # Check if only a specific ticker is wanted, or all the default ones are
        if ticker and ticker in contract_subgroups.values():
            subgroup_df = df[(df.contract_subgroup == ticker)]
            
            # Delete unused columns
            del subgroup_df['contract_subgroup']
        
            # Save as json
            _, file = path.split(input_file_path)
            json_filename = file.replace('.zip', '.json')
            subgroup_df.to_json(path.join('data', ticker, json_filename), orient='records')
        else:
            # Get options data for all of the subgroups under study
            for key, value in contract_subgroups.items():
                subgroup_df = df[(df.contract_subgroup == key)]
                
                # Delete unused columns
                del subgroup_df['contract_subgroup']
            
                # Save as json
                _, file = path.split(input_file_path)
                json_filename = file.replace('.zip', '.json')
                subgroup_df.to_json(path.join('data', value, json_filename), orient='records')
        
        # Delete tmp folder
        shutil.rmtree('tmp')


def check_option(input_file_path, ticker, strike, expiration_date, right):
    '''
    Method to check if null values seen in the report already have null value in the raw data, or introduced later
    '''
    # Check if given input file exists
    if path.exists(input_file_path) and path.isfile(input_file_path):
        # Delete tmp folder (if exists)
        if path.exists('tmp') and path.isdir('tmp'):
            shutil.rmtree('tmp')
        
        # First unzip (inside there is another zip file which also has to be unziped)
        outer_zip = zipfile.ZipFile(input_file_path, 'r')
        outer_zip.extractall('tmp')
        outer_zip.close()
        inner_zip = zipfile.ZipFile(path.join('tmp', inner_zip_filename), 'r')
        inner_zip.extractall('tmp')
        inner_zip.close()
        
        # Load contracts file
        contracts_data = pd.read_csv(path.join('tmp', contracts_file), sep=';', decimal=',',
                                     header=None, names=contracts_columns, dtype=contracts_dtype, parse_dates=[0, 5],
                                     usecols=[0, 2, 3, 4, 5, 6])
        
        # Now load contracts stats file
        contracts_stats_data = pd.read_csv(path.join('tmp', contracts_stats_file), sep=';', decimal=',',
                                           header=None, names=contracts_stats_columns, dtype=contracts_stats_dtype, parse_dates=[0],
                                           usecols=[2, 3, 4, 5, 6, 13, 15])
        
        # Join dataframes on contract_code
        df = pd.merge(contracts_data, contracts_stats_data, how='inner', on='contract_code', sort=False)
        
        # Adapt session date and expiration date to the same format used in EUREX website
        df['session_date'] = pd.to_datetime(df['session_date']).dt.strftime('%d/%m/%Y')
        df['expiration_date'] = pd.to_datetime(df['expiration_date']).dt.strftime('%d/%m/%Y')
        
        # Filter the dataframe to keep only options (rows which contain a defined strike)
        df.strike.replace('', np.nan, inplace=True)
        df.dropna(subset=['strike'], inplace=True)
        # The first char of contract code is the right initial for option contracts
        # Also, only European type options are listed for miniIBEX, but we have to filter out European type from stock options
        df['contract_code'] = df['contract_code'].apply(lambda x: np.nan if 'EU ' in x else x)
        df.dropna(subset=['contract_code'], inplace=True)
        df['right'] = df['contract_code'].apply(lambda x: x[0])
        # Delete unused columns
        del df['contract_code']
        del df['contract_type']
        
        # Print desired option data
        df.loc[(df['ticker'] == ticker) & (df['right'] == right) & (df['strike'] == strike) & (df['expiration_date'] == expiration_date)] #TODO
        print('CUCU')
        
        # Delete tmp folder
        shutil.rmtree('tmp')
        
        

if __name__ == '__main__':
    # Configure the command line options
    parser = ArgumentParser()
    parser.add_argument('-i', '--input_file', type=str, required=True,
                        help='Determines the single daily zip file or folder to convert')
    parser.add_argument('-t', '--ticker', type=str, default=None,
                        help='Determines a specific ticker to be extracted')            
    args = parser.parse_args()
    
    if path.exists(args.input_file):
        if path.isfile(args.input_file):
            meff_to_json(args.input_file, args.ticker)
        elif path.isdir(args.input_file):
            # Convert all available daily files data
            [meff_to_json(path.join(args.input_file, f), args.ticker) for f in listdir(args.input_file) if path.isfile(path.join(args.input_file, f)) and f.lower().endswith('.zip')]
    