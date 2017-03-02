#! /usr/bin/env python
# -*- coding: utf-8 -*
import vollib.black_scholes as bs
import vollib.black_scholes.implied_volatility as iv
import vollib.black_scholes.greeks.analytical as gk
from datetime import date, datetime
from argparse import ArgumentParser
import json
import os
import sys


if __name__ == '__main__':
    # Configure the command line options
    parser = ArgumentParser()
    parser.add_argument('-i', '--input_json', type=str, required=True,
                        help='[Required] Path to input json file with Eurexchange option data')
    parser.add_argument('-s', '--underlying_price', type=float, required=True,
                        help='[Required] Current price of option\'s underlying')
    parser.add_argument('-t', '--session_date', type=str, default=date.today().strftime('%d%m%Y'),
                        help='Session date. Required format: ddmmyyyy. Default: today.')
    parser.add_argument('-r', '--risk_free_rate', type=float, required=True,
                        help='[Required] Risk free rate. Example: 0.01')
    config = parser.parse_args()
    
    # Open and load json file
    data = {}
    if os.path.exists(config.input_json) and os.path.isfile(config.input_json):
        with open(config.input_json, 'r') as f:
            data = json.load(f)
    else:
        sys.exit('ERROR: given input file does not exist')
    
    # Iterate json entries and calculate greeks using Black-Scholes
    for entry in data:
        last_price = entry['last_price']
        K = entry['strike']
        S = config.underlying_price  # underlying_price
        session_date = datetime.strptime(config.session_date, "%d%m%Y").date()
        opt_date = datetime.strptime(entry['expiration_date'], "%d/%m/%Y").date()
        t = (opt_date - session_date).days / 365.  # time to expiration (in years)
        r = config.risk_free_rate
        flag = entry['right'].lower()
        
        sigma = iv.implied_volatility(last_price, S, K, t, r, flag)
        print(sigma, last_price, S, K, t, r, flag)
        sigma = 0 if sigma < 1e-10 else sigma
        entry['iv'] = sigma
        entry['delta'] = gk.delta(flag, S, K, t, r, sigma)
        entry['gamma'] = gk.gamma(flag, S, K, t, r, sigma)
        entry['theta'] = gk.theta(flag, S, K, t, r, sigma) * 365
        entry['vega'] = gk.vega(flag, S, K, t, r, sigma)
    
    # Remove existing json file and save the new one with the greeks
    #os.remove(config.input_json) TODO
    os.remove('test2.json') #TODO
    with open('test2.json', 'w') as f:
        json.dump(data, f, indent=4)