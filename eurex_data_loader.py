#! /usr/bin/env python
# -*- coding: utf-8 -*
import pandas as pd
import sys
import os
from os.path import exists, isdir, isfile, join, split
from argparse import ArgumentParser
import open_interest_plot as oip


if __name__ == '__main__':
    # Configure the command line options
    parser = ArgumentParser()
    parser.add_argument('-i', '--input_file', type=str,
                        help='Determines the path to a single daily json file')
    parser.add_argument('-f', '--input_folder', type=str,
                        help='Determines the path to folder containing several daily json files')
    parser.add_argument('-t', '--expiration_date', type=str, required=True,
                        help='Determines the expiration date under study. Example: 17/03/2017')
    parser.add_argument('-k', '--strike', type=float,
                        help='Determines the strike of the option under study. Example: 6000')
    args = parser.parse_args()
    
    data = pd.DataFrame()
    daily_files = []
    ticker = ''
    if args.input_file:
        if exists(args.input_file) and isfile(args.input_file):
            daily_files.append(args.input_file)
            ticker = args.input_file.split(os.sep)[-2]
        else:
            sys.exit('ERROR: given input file does not exist')
    elif args.input_folder:
        if exists(args.input_folder) and isdir(args.input_folder):
            # Load all available daily files data
            daily_files = [join(args.input_folder, f) for f in os.listdir(args.input_folder) if isfile(join(args.input_folder, f)) and f.lower().endswith('.json')]
            ticker = 'TEST'
            
    for file in daily_files:      
        # Load contracts file
        df = pd.read_json(file)
        
        # Append dataframe into a single dataframe with the info from all files
        data = data.append(df)
    
    if args.input_file and args.expiration_date:
        oip.plot_open_interest(data, args.expiration_date, ticker, False)
    
    if args.strike and args.expiration_date and not args.input_file:
        # If a certain option has been given with both strike and expiration, plot cummulative open interest
        filename = oip.plot_open_interest_evolution(data, args.strike, args.expiration_date, ticker, True)
        print(filename)