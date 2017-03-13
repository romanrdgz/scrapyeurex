#! /usr/bin/env python
# -*- coding: utf-8 -*
from argparse import ArgumentParser
import os
from os import path
import json
import sys
import pandas as pd
from risk_graph import plot_risk_graph


def load_strategy(filename):
    data = None
    try:
        with open(filename, 'r') as infile:
            data = json.load(infile)
    except ValueError as e:
        sys.exit('ERROR: given input file is not a valid json file')
    return data

    
if __name__ == '__main__':
    # Configure the command line options
    parser = ArgumentParser()
    parser.add_argument('-i', '--input_file', type=str, required=True,
                        help='[Required] Determines the input file with options data')
    parser.add_argument('-S', '--underlying_price', type=float, required=True,
                        help='[Required] Current underlying price')
    parser.add_argument('-r', '--risk_free_rate', type=float, default=0.01,
                        help='Risk free rate. Default: 0.01')
    parser.add_argument('-o', '--output', action='store_true', default=False,
                        help='If enabled saves the plot as a PNG file. Otherwise (default), it just shows the plot')
    config = parser.parse_args()
    
    # Check that input file does exist
    if not (path.exists(config.input_file) and path.isfile(config.input_file)):
        sys.exit('ERROR: given input file does not exist or is not a file')
    
    # Load strategy
    data = load_strategy(config.input_file)
    
    # Update last price for each options
    # First check if there is data available in data folder for given ticker
    data_folder = 'data'
    available_tickers = [f for f in os.listdir(data_folder) if path.isdir(path.join(data_folder, f))]
    if data['meta']['ticker'].upper() not in available_tickers:
        sys.exit('ERROR: there is no available option data on ticker ' + str(data.meta.ticker))
    
    # Get the latest daily file regarding that ticker
    ticker_data_folder = path.join(data_folder, data['meta']['ticker'].upper())
    daily_files = sorted([f for f in os.listdir(ticker_data_folder) if path.isfile(path.join(ticker_data_folder, f)) and f.lower().endswith('.json')])
    latest_daily_filepath = path.join(ticker_data_folder, daily_files[-1])
    
    # Load the latest daily file and add last price data to the options composing input strategy
    df = pd.read_json(latest_daily_filepath)
    for opt in data['options']:
        # Filter dataframe to find this option
        filter = df[(df.strike == opt['strike']) & (df.expiration_date == opt['expiration_date']) & (df.right == opt['right'])]
        if filter.empty:
            sys.exit('ERROR: unable to find ' + str(opt.right) + ' option with strike ' + str(opt.strike) + ' expiring on ' + str(opt.expiration_date))
        opt['last_price'] = filter.iloc[0].last_price
    
    # Plot risk graph
    plot_risk_graph(data, config.underlying_price, config.risk_free_rate, save_png=config.output)
    