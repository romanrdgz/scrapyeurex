#! /usr/bin/env python
# -*- coding: utf-8 -*
import pandas as pd
import numpy as np
import scipy.stats as stats
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns;
sns.set(style="white", color_codes=True)
pd.options.mode.chained_assignment = None


def plot_open_interest(df: pd.DataFrame, t: datetime):
    '''
    Plots open interest for all the available strikes for a given expiration date
    df: Pandas DataFrame with MEFF information
    t: Expiration date of the option under study
    '''
    # Filter out for given expiration date and keep only contracts where open interest is not NaN
    df = df[pd.notnull(df['open_interest'])]
    df = df[df.expiration_date == t]
    
    # Filter out strikes too OTM
    max_oi = int(df.open_interest.max())
    df.loc[df.open_interest < 0.1 * max_oi, 'open_interest'] = 0;
    
    # Get min and max strikes (where there is actually some open interest)
    min_strike = int(df[df.open_interest > 0].strike.min())
    max_strike = int(df[df.open_interest > 0].strike.max())
    strikes = np.arange(min_strike, max_strike + 100, 100)
    strikes_ticks = df[df.open_interest > 0].strike
    width = 25
    
    # Separate calls from puts
    call = df[df.right == 'C']
    put  = df[df.right == 'P']
    
    # Iterate each to get ordered list of open interest per strike
    call_oi = [0] * len(strikes)
    put_oi  = [0] * len(strikes)
    for i, s in enumerate(strikes):
        oi = call[call.strike == s]
        call_oi[i] = 0 if oi.empty else int(oi.open_interest)
        oi = put[put.strike == s]
        put_oi[i] = 0 if oi.empty else int(oi.open_interest)

    fig, ax = plt.subplots()
    ax.barh(strikes, call_oi, width, color='blue', align='center', label='Calls')
    ax.barh(strikes+width, put_oi, width, color='red', align='center', label='Puts')
    ax.set(yticks=strikes_ticks, ylim=[min_strike*0.9, max_strike*1.1])
    ax.set_xlabel('Open interest')
    ax.set_ylabel('Strikes')
    ax.set_title('Open interest for ESTX50 expiring on {} \nNote: strikes with open interest < 10% MAX are filtered out'.format(t))
    ax.legend()

    plt.show()
    
    
def normal_dist_over_call_open_interest(df: pd.DataFrame):
    '''
    TODO, work in progress
    '''
    # Filter out strikes too OTM
    #df = dataframe[(dataframe.strike > 8500) & (dataframe.strike < 10500)]
    
    # Get min and max strikes
    min_strike = int(df.strike.min())
    max_strike = int(df.strike.max())
    strikes = np.arange(min_strike, max_strike + 100, 100)
    width = 25
    
    
    strikes_mean = np.mean(strikes)
    strikes_std = np.std(strikes)
    strikes_n = (strikes - strikes_mean) / strikes_std
    pdf = stats.norm.pdf(strikes)

    # plot data
    f, ax1 = plt.subplots()

    ax1.hist(strikes, 20, normed=1)
    ax1.set(yticks=strikes+width, ylim=[min_strike, max_strike])
    ax1.set_xlim([strikes.min(), strikes.max()])
    ax1.set_xlabel(r'TV $[\sigma]$')
    ax1.set_ylabel(r'Relative Frequency')

    ax2 = ax1.twiny()
    ax2.plot(strikes_n, pdf, lw=3, c='r')
    ax2.grid(False)
    ax2.set_xlim(ax1.get_xlim())
    ax2.set_ylim(ax1.get_ylim())
    ax2.set_xlabel(r'TV' )

    ticklocs = ax2.xaxis.get_ticklocs()
    ticklocs = [round(t*strikes_std + strikes_mean, 2) for t in ticklocs]
    ax2.xaxis.set_ticklabels(map(str, ticklocs))

    plt.show()
    
    
def plot_open_interest_evolution(df: pd.DataFrame, k: float, t: datetime):
    '''
    Plots the evolution of open interest for both calls and puts of a given strike and expiry date
    df: Pandas DataFrame with MEFF information
    k: Strike of the option under study
    t: Expiration date of the option under study
    '''
    # Filter out data
    df = df[(df.expiration_date == t) & (df.strike == k)]
    
    # Get data to plot
    session_dates = df.session_date[df.right == 'C']
    call_oi = df.open_interest[df.right == 'C']
    put_oi = df.open_interest[df.right == 'P']
    
    f, ax = plt.subplots()
    ax.plot(session_dates, call_oi, 'b', label='Calls')
    ax.plot(session_dates, put_oi, 'r', label='Puts')
    ax.set_xlabel('Session date')
    ax.set_ylabel('Open interest')
    ax.set_title('Evolution of open interest for mini-IBEX strike {} expiring on {}'.format(k, t))
    ax.grid(True)
    ax.legend()
    plt.show()