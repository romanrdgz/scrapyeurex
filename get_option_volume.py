#! /usr/bin/env python
# -*- coding: utf-8 -*
import pandas as pd
import os


data_folder = 'data'
tickers = ['BBVA', 'DAX', 'DIA', 'ESTX50', 'FIE', 'ITX', 'QQQ', 'SAN', 'SPY', 'TEF', 'VIX']
ohlc_data_file = 'candlestick_data.csv'
ohlc_dtype = {'session_date': str, 'close': float, 'open': float, 'percentage_high': float, 'high': float, 'low':float, 'volume': float}
atm_percentage = 0.015

for ticker in tickers:
    ticker_data_folder = os.path.join(data_folder, ticker)
    daily_files = sorted([f for f in os.listdir(ticker_data_folder) if os.path.isfile(os.path.join(ticker_data_folder, f)) and f.lower().endswith('.json')])
    optvol = pd.DataFrame(columns=['session_date', 'itm_call_volume', 'atm_call_volume', 'otm_call_volume', 'itm_put_volume', 'atm_put_volume', 'otm_put_volume'])
    ohlc = None
    try:
        ohlc = pd.read_csv(os.path.join(data_folder, ticker, ohlc_data_file), encoding='ISO-8859-1', sep=';', decimal=',', dtype=ohlc_dtype)
    except ValueError as e:
        print('ERROR for {} while trying to read CSV data file: {}'.format(ticker, e))
    else:
        for dayf in daily_files:
            csvfile = ''
            try:
                csvfile = os.path.join(data_folder, ticker, dayf)
                df = pd.read_json(csvfile)
            except ValueError as e:
                print('ERROR while reading file {}: {}'.format(csvfile, e))
            
            today = ''
            close = 0
            try:
                # Get adjusted close price for this ticker this day
                today = df['session_date'].iloc[0]
                close_series = ohlc.loc[ohlc['session_date'] == today, 'close']
                if close_series.empty:
                    print('WARNING: no OHLC data for {} on {}'.format(ticker, today))
                else:
                    # Sum volume for all call ATM, OTM and ITM options
                    close = float(close_series)
                    itm_call_volume = int(df.loc[(df['right'] == 'C') & (df['strike'] < close * (1-atm_percentage)), 'volume'].sum())
                    atm_call_volume = int(df.loc[(df['right'] == 'C') & (df['strike'] >= close * (1-atm_percentage)) & (df['strike'] <= close * (1+atm_percentage)), 'volume'].sum())
                    otm_call_volume = int(df.loc[(df['right'] == 'C') & (df['strike'] > close * (1+atm_percentage)), 'volume'].sum())
                    otm_put_volume  = int(df.loc[(df['right'] == 'P') & (df['strike'] < close * (1-atm_percentage)), 'volume'].sum())
                    atm_put_volume  = int(df.loc[(df['right'] == 'P') & (df['strike'] >= close * (1-atm_percentage)) & (df['strike'] <= close * (1+atm_percentage)), 'volume'].sum())
                    itm_put_volume  = int(df.loc[(df['right'] == 'P') & (df['strike'] > close * (1+atm_percentage)), 'volume'].sum())
                    
                    optvol = optvol.append({
                        'session_date': today,
                        'itm_call_volume': itm_call_volume,
                        'atm_call_volume': atm_call_volume,
                        'otm_call_volume': otm_call_volume,
                        'itm_put_volume':  itm_put_volume,
                        'atm_put_volume':  atm_put_volume,
                        'otm_put_volume':  otm_put_volume
                    }, ignore_index=True)
            except TypeError as e:
                print('ERROR for {} while iterating {} for a close price of {}: {}'.format(ticker, today, close, e))
                
    # Join both dataframes
    df = ohlc.merge(optvol, on=['session_date'], how='inner')
    df = df.set_index('session_date')
    df.to_csv(os.path.join(ticker_data_folder, 'daily_option_volume.csv'), sep=',', decimal='.')