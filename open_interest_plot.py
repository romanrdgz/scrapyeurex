#! /usr/bin/env python
# -*- coding: utf-8 -*
import pandas as pd
import numpy as np
import scipy.stats as stats
from datetime import datetime
import os
from os import path
import matplotlib.pyplot as plt
import seaborn as sns;
sns.set(style="white", color_codes=True)
pd.options.mode.chained_assignment = None


def plot_open_interest(df: pd.DataFrame, t: str, ticker: str, save_img: bool):
    '''
    Plots open interest for all the available strikes for a given expiration date
    df: Pandas DataFrame with options information
    t: Expiration date of the option under study
    ticker: Ticker of the underlying
    save_img: True to store plot as an image file, false to shor it in a window
    '''
    svg_filename = None
    # Filter out for given expiration date and keep only contracts where open interest is not NaN
    df = df[pd.notnull(df['open_interest'])]
    df = df[df.expiration_date == t]
    
    # Filter out strikes too OTM
    max_oi = int(df.open_interest.max())
    df.loc[df.open_interest < 0.1 * max_oi, 'open_interest'] = 0;
    
    # Check if there is open interest at all for current expiration date
    if not df[df.open_interest > 0].empty:
        # Get min and max strikes (where there is actually some open interest)
        min_strike = int(df[df.open_interest > 0].strike.min())
        max_strike = int(df[df.open_interest > 0].strike.max())
        strikes_ticks = df[df.open_interest > 0].strike
        strikes = np.array(strikes_ticks.tolist())
        
        # Get minor distance between 2 strikes
        min_distance_between_strikes = df.strike.diff().min()
        width = min_distance_between_strikes / 4
        
        # Separate calls from puts
        call = df[df.right == 'C']
        put  = df[df.right == 'P']
        
        # Iterate each to get ordered list of open interest per strike
        call_oi = [0] * len(strikes)
        put_oi  = [0] * len(strikes)
        for i, s in enumerate(strikes):
            oi = call[call.strike == s]
            if not oi.empty:
                call_oi[i] = int(oi.open_interest)
            oi = put[put.strike == s]
            if not oi.empty:
                put_oi[i] = int(oi.open_interest)
        
        # Set y range as an additional upper and lower 10% of the spread between max and min spreads.
        # Consider that there might be only one strike, or very few close strikes. In that case use additional 10% of max strike
        strike_spread = (max_strike - min_strike) if (max_strike - min_strike > 0.1 * min_strike) else max_strike
        yrange = [min_strike - strike_spread * 0.1, max_strike + strike_spread * 0.1]
        
        # Calculate the vertical size of the plot in order to contain all bars without overlapping nor being too thin.
        # To do this, consider that barh function has height parameter (default 0.8% of (plot size / num_bars))
        # Default figure size is (8, 6) inches
        num_bars = max(len(call_oi), len(put_oi))
        size_vs_nbars = strike_spread / num_bars
        print(ticker, t, size_vs_nbars)
        
        # Plot    
        fig, ax = plt.subplots(figsize=(8, 16))
        ax.barh(strikes-width/2, call_oi, height=0.99, color='blue', align='center', label='Calls')
        ax.barh(strikes+width/2, put_oi, height=0.99, color='red', align='center', label='Puts')
        
        ax.set(yticks=strikes_ticks, ylim=yrange)
        ax.set_xlabel('Open interest')
        ax.set_ylabel('Strikes')
        ax.set_title('Open interest for {} expiring on {} \nNote: strikes with open interest < 10% MAX are filtered out'.format(ticker, t))
        ax.legend()

        if save_img:
            svg_filename = '{}_oi_{}.svg'.format(ticker, datetime.strptime(t, '%d/%m/%Y').strftime('%Y%m%d'))
            reports_subfolders = sorted([f for f in os.listdir('reports') if path.isdir(path.join('reports', f))])
            latest_folder = reports_subfolders[-1]
            img_folder = path.join('reports', latest_folder, 'img')
            if not path.exists(img_folder):
                os.makedirs(img_folder)
            img_path = path.join(img_folder, svg_filename)
            plt.savefig(img_path, format='svg', dpi=300)
        else:
            plt.show()  # Show the plot
        plt.close('all')
    return svg_filename
    
    
def plot_open_interest_evolution(df: pd.DataFrame, k: float, t: str, ticker: str, save_img: bool):
    '''
    Plots the evolution of open interest for both calls and puts of a given strike and expiry date
    df: Pandas DataFrame with MEFF information
    k: Strike of the option under study
    t: Expiration date of the option under study
    '''
    # Filter out data
    df = df[(df.expiration_date == t) & (df.strike == k)]
    
    # Get data to plot (get session dates for each group independently to avoid problems when data is missing for one group)
    session_dates_call = pd.to_datetime(df.session_date[df.right == 'C'], format="%d/%m/%Y")
    session_dates_put = pd.to_datetime(df.session_date[df.right == 'P'], format="%d/%m/%Y")
    call_oi = df.open_interest[df.right == 'C']
    put_oi = df.open_interest[df.right == 'P']
    
    f, ax = plt.subplots()
    ax.plot(session_dates_call, call_oi, 'b', label='Calls')
    ax.plot(session_dates_put,  put_oi,  'r', label='Puts')
    ax.set_xlabel('Session date')
    ax.set_ylabel('Open interest')
    ax.set_title('Evolution of open interest for {} strike {} expiring on {}'.format(ticker, k, t))
    ax.grid(True)
    ax.legend()
    
    svg_filename = None
    if save_img:
        svg_filename = '{}_oiev_{}_{}.svg'.format(ticker, k, datetime.strptime(t, '%d/%m/%Y').strftime('%Y%m%d'))
        reports_subfolders = sorted([f for f in os.listdir('reports') if path.isdir(path.join('reports', f))])
        latest_folder = reports_subfolders[-1]
        img_folder = path.join('reports', latest_folder, 'img')
        if not path.exists(img_folder):
            os.makedirs(img_folder)
        img_path = path.join(img_folder, svg_filename)
        plt.savefig(img_path, format='svg', dpi=300)
    else:
        plt.show()
    plt.close('all')
    return svg_filename