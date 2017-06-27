#! /usr/bin/env python
# -*- coding: utf-8 -*
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
from os import path
import py_vollib.black_scholes.implied_volatility as iv
from py_lets_be_rational.exceptions import BelowIntrinsicException


def calculate_iv(df: pd.DataFrame, S: float, r: float, ticker: str):
    '''
    Calculates implied volatility using Black Scholes formula.
    df: Options dataframe
    S: Underlying asset price
    r: Risk-free interest rate
    '''
    df['years_to_exp'] = df['expiration_date'].apply(lambda x: (datetime.strptime(x, '%d/%m/%Y').date() - datetime.now().date()).days / 365.)
    return df.apply(lambda row: _calculate_iv(row['last_price'], S, row['strike'], row['years_to_exp'], r, row['right'], ticker), axis=1)
    
    
def _calculate_iv(price: float, S: float, K: float, t: float, r: float, flag: str, ticker: str):
    iv_value = float('NaN')
    if price > 0.0 and t > 0.0:  # Otherwise makes no sense
        try:
            iv_value = iv.implied_volatility(price, S, K, t, r, flag.lower())
        except BelowIntrinsicException as e:
            # Option price is below the intrinsic value (distance between current underlying price and strike). If true (including fees), this is a free
            # risk opportunity, but it is more likely an error in data (probably underlying asset price is not updated)
            iv_value = float('NaN')
        except Exception as e:
            exception_type = type(e).__name__
            print('ERROR {} while calculating IV(price, S, K, t, r, right)->({}, {}, {}, {}, {}, {}) for ticker {} : {}'.format(exception_type, price, S, K, t, r, flag, ticker, e))
    return iv_value
    
    
def plot_strikes_skew(df: pd.DataFrame, t_list: list, ticker: str, output_folder: str, rewrite_img: bool, save_img: bool):
    '''
    Plots the strikes volatility skew
    df: Options dataframe
    t_list: List of xpiration dates to fix for this skew
    ticker: Ticker of the underlying asset
    output_folder: Ouput folder
    rewrite_img: Rewrites image if exists, skips computation otherwise
    save_img: True to store plot as an image file, false to show it in a window
    '''
    img_path = ''
    svg_filename = ''
    if save_img:
        svg_filename = '{}_strike_skew.svg'.format(ticker)
        img_folder = path.join('reports', output_folder, 'img')
        img_path = path.join(img_folder, svg_filename)
        # Check if image already exists, and skip computation (unless rewrite option is activated)
        if not rewrite_img and img_path and path.isfile(img_path):
            return svg_filename
    
    for t in t_list:
        strikes_put = df.strike[(df.right == 'P') & (df.expiration_date == t)]
        iv_put = df.iv[(df.right == 'P') & (df.expiration_date == t)]
        plt.plot(strikes_put, iv_put)
        plt.legend(t)
    plt.xlabel('Strike prices')
    plt.ylabel('IV')

    if save_img:
        dpi = 300
        plt.savefig(img_path, format='svg', dpi=dpi)
    else:
        plt.show()  # Show the plot
    plt.close('all')
    return svg_filename


def plot_expiration_skew(df: pd.DataFrame, K_list: list, ticker: str, output_folder: str, rewrite_img: bool, save_img: bool):
    '''
    Plots the expiration dates volatility skew
    df: Options dataframe
    K_list: List of strikes to fix for this skew
    ticker: Ticker of the underlying asset
    output_folder: Ouput folder
    rewrite_img: Rewrites image if exists, skips computation otherwise
    save_img: True to store plot as an image file, false to show it in a window
    '''
    img_path = ''
    svg_filename = ''
    if save_img:
        svg_filename = '{}_exp_skew.svg'.format(ticker)
        img_folder = path.join('reports', output_folder, 'img')
        img_path = path.join(img_folder, svg_filename)
        # Check if image already exists, and skip computation (unless rewrite option is activated)
        if not rewrite_img and img_path and path.isfile(img_path):
            return svg_filename
    
    for K in K_list:
        expiration_dates_put = pd.to_datetime(df.expiration_date[(df.right == 'P') & (df.strike.astype('float') == K)], format="%d/%m/%Y")
        iv_put = df.iv[(df.right == 'P') & (df.strike.astype('float') == K)]
        plt.plot(expiration_dates_put, iv_put)
        plt.legend(str(K))
    plt.xlabel('Expiration Date')
    plt.ylabel('IV')

    if save_img:
        dpi = 300
        plt.savefig(img_path, format='svg', dpi=dpi)
    else:
        plt.show()  # Show the plot
    plt.close('all')
    return svg_filename