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


def plot_open_interest(df: pd.DataFrame, t: str, ticker: str, output_folder: str, rewrite_img: bool, save_img: bool):
    '''
    Plots open interest for all the available strikes for a given expiration date
    df: Pandas DataFrame with options information
    t: Expiration date of the option under study
    ticker: Ticker of the underlying asset
    output_folder: Ouput folder
    rewrite_img: Rewrites image if exists, skips computation otherwise
    save_img: True to store plot as an image file, false to show it in a window
    '''
    img_path = ''
    svg_filename = ''
    if save_img:
        svg_filename = '{}_oi_{}.svg'.format(ticker, datetime.strptime(t, '%d/%m/%Y').strftime('%Y%m%d'))
        img_folder = path.join('reports', output_folder, 'img')
        img_path = path.join(img_folder, svg_filename)
        # Check if image already exists, and skip computation (unless rewrite option is activated)
        if not rewrite_img and img_path and path.isfile(img_path):
            return svg_filename
    
    # Filter out for given expiration date and keep only contracts where open interest is not NaN
    df = df[pd.notnull(df['open_interest'])]
    df = df[df.expiration_date == t]
    if df.empty:
        return None
    
    # Filter out strikes too OTM
    max_oi = int(df.open_interest.max())
    df.loc[df.open_interest < 0.1 * max_oi, 'open_interest'] = 0;
    
    # Check if there is open interest at all for current expiration date
    if not df[df.open_interest > 0].empty:
        # Get min and max strikes (where there is actually some open interest)
        min_strike = int(df[df.open_interest > 0].strike.min())
        max_strike = int(df[df.open_interest > 0].strike.max())
        strikes = sorted(np.array(df[df.open_interest > 0].strike.unique().tolist()))
        
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
        
        # Calculate the vertical size of the plot in order to contain all bars without overlapping nor being too thin
        num_bars = max(len(call_oi), len(put_oi))
        dpi = 300
        fig_w = 8
        fig_h = max(4.2, num_bars * 100 / dpi)  # Set a minimum figure height of 4.2 inches (otherwise xlabel and/or plot title is cropped)
        
        # Plot
        fig, ax = plt.subplots(figsize=(fig_w, fig_h))
        df2 = pd.DataFrame({'strike': [s for s in strikes], 'call': call_oi, 'put': put_oi})
        df2 = df2.set_index('strike')
        df2[['call', 'put']].plot(kind='barh', color=['blue', 'red'], ax=ax)

        ax.set_xlabel('Open interest')
        ax.set_ylabel('Strikes')
        ax.set_title('Open interest for {} expiring on {} \nNote: strikes with open interest < 10% MAX are filtered out'.format(ticker, t))
        ax.legend()

        if save_img:
            plt.savefig(img_path, format='svg', dpi=dpi)
        else:
            plt.show()  # Show the plot
        plt.close('all')
    return svg_filename
    
    
def plot_open_interest_evolution(df: pd.DataFrame, k: float, t: str, ticker: str, output_folder: str, rewrite_img: bool, save_img: bool):
    '''
    Plots the evolution of open interest for both calls and puts of a given strike and expiry date
    df: Pandas DataFrame with MEFF information
    k: Strike of the option under study
    t: Expiration date of the option under study
    ticker: Ticker of the underlying asset
    output_folder: Ouput folder
    rewrite_img: Rewrites image if exists, skips computation otherwise
    save_img: True to store plot as an image file, false to show it in a window
    '''
    img_path = ''
    svg_filename = ''
    if save_img:
        svg_filename = '{}_oiev_{}_{}.svg'.format(ticker, k, datetime.strptime(t, '%Y/%m/%d').strftime('%Y%m%d'))
        img_folder = path.join('reports', output_folder, 'img')
        img_path = path.join(img_folder, svg_filename)
        # Check if image already exists, and skip computation (unless rewrite option is activated)
        if not rewrite_img and img_path and path.isfile(img_path):
            return svg_filename
    
    # Traspose date format
    tt = datetime.strptime(t, '%Y/%m/%d').strftime('%d/%m/%Y')
    
    # Filter out data
    df = df[(df.expiration_date == tt) & (df.strike == k)]
    
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
    
    if save_img:
        plt.savefig(img_path, format='svg', dpi=300)
    else:
        plt.show()
    plt.close('all')
    return svg_filename