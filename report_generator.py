#! /usr/bin/env python
# -*- coding: utf-8 -*
import os
from os import path
import shutil
import pandas as pd
import jinja2
from datetime import datetime
import open_interest_plot as oip
import traceback


def get_big_movements(ldf: pd.DataFrame, pdf: pd.DataFrame, n=10):
    # Filter out too small open interest (less than 0.1% of total open interest)
    ldf = ldf.drop_duplicates()
    ldf_total_oi = ldf.open_interest.sum()
    ldf = ldf.loc[ldf['open_interest'] > 0.001 * ldf_total_oi]
    pdf = pdf.drop_duplicates()
    pdf_total_oi = pdf.open_interest.sum()
    pdf = pdf.loc[pdf['open_interest'] > 0.001 * pdf_total_oi]
    
    # Get N options with higher volume in the last day of trading available
    ldf_high_volume = ldf[ldf.volume > 0].nlargest(n, 'volume')
    ldf['oiev_chart_filename'] = ldf['expiration_date'].apply(lambda x: datetime.strptime(x, '%d/%m/%Y').strftime('%Y%m%d'))
    
    # Get 3 options with higher open interest for each right and expiry available
    column_names = list(ldf.columns.values)
    ldf_high_call_oi = pd.DataFrame(columns=column_names)
    ldf_high_put_oi = pd.DataFrame(columns=column_names)
    for expiry in sorted(ldf.expiration_date.unique().tolist()):
        ldf_high_call_oi = ldf_high_call_oi.append(ldf.loc[(ldf.expiration_date == expiry) & (ldf.right == 'C')].nlargest(3, 'open_interest'))
        ldf_high_put_oi = ldf_high_put_oi.append(ldf.loc[(ldf.expiration_date == expiry) & (ldf.right == 'P')].nlargest(3, 'open_interest'))
    ldf_high_call_oi.sort_values(by=['expiration_date', 'open_interest'], ascending=[0, 0])
    ldf_high_put_oi.sort_values(by=['expiration_date', 'open_interest'], ascending=[0, 0])
        
    # Merge with previous day data and compare to detect important changes in open interest
    mdf = ldf.merge(pdf, on=['strike', 'right', 'expiration_date'], how='inner', suffixes=('_latest', '_previous'))
    mdf['open_interest_diff'] = mdf.apply(lambda x: x['open_interest_latest'] - x['open_interest_previous'], axis=1)
    mdf['open_interest_diff_pc'] = mdf.apply(lambda x: '{:.2f}%'.format(100 * (x['open_interest_latest'] - x['open_interest_previous']) / x['open_interest_previous']) if x['open_interest_previous'] > 0 else x['open_interest_latest'], axis=1)
    mdf['oiev_chart_filename'] = mdf['expiration_date'].apply(lambda x: datetime.strptime(x, '%d/%m/%Y').strftime('%Y%m%d'))
        
    # Get options with greater change in open interest (N positive)
    mdf_highest_changers = mdf.loc[mdf.open_interest_diff > 0].nlargest(n, 'open_interest_diff')
        
    # Return as dict
    return {'highest_volume': ldf_high_volume, 'highest_call_oi': ldf_high_call_oi, 'highest_put_oi': ldf_high_put_oi, 'highest_changers': mdf_highest_changers}

    
def create_report_folder(session_date: str):
    output_folder = 'report_{}'.format(session_date.replace('/', ''))
    output_folder_path = path.join('reports', output_folder)
    if not path.exists(output_folder_path):
        os.makedirs(output_folder_path)
    return output_folder
    
        
def generate_oi_report(movements, output_folder, oi_plots_files, current_prices):
    templateLoader = jinja2.FileSystemLoader('templates')
    templateEnv = jinja2.Environment(
	    autoescape=False,
		loader=templateLoader,
		trim_blocks=False)
    template = templateEnv.get_template('report_template_tabbed.html')

    session_date = list(movements.values())[0]['highest_volume'].iloc[0].session_date
    tickers_list = sorted(movements.keys())
    
    volume_data = {}
    oi_data = {}
    portfolio_data = {}
    for ticker in tickers_list:
        volume_data[ticker] = {}
        volume_data[ticker]['last_price'] = float(current_prices.loc[current_prices.ticker == ticker, 'last_price'])
        volume_data[ticker]['hv_option_list']  = [opt for _, opt in movements[ticker]['highest_volume'].iterrows()]
        volume_data[ticker]['poi_option_list'] = [opt for _, opt in movements[ticker]['highest_changers'].iterrows()]
        volume_data[ticker]['highest_call_oi'] = [opt for _, opt in movements[ticker]['highest_call_oi'].iterrows()]
        volume_data[ticker]['highest_put_oi']  = [opt for _, opt in movements[ticker]['highest_put_oi'].iterrows()]
        
        oi_data[ticker] = sorted(oi_plots_files[ticker])
        
        portfolio_data[ticker] = {}
        
    context = {
        'date': session_date,
        'tickers_list': tickers_list,
        'volume_data': volume_data,
        'oi_data': oi_data,
        'portfolio_data': portfolio_data
    }
    
    output_file = 'report_{}.html'.format(session_date.replace('/', ''))
    output_html = template.render(context)
    with open(path.join('reports', output_folder, output_file), 'w') as f:
        f.write(output_html)

    return path.join(output_folder, output_file)
    
    
def generate_link_to_latest(report_path):
    with open(path.join('reports', 'latest.html'), 'w') as f:
        f.write('<html><head><meta http-equiv="refresh" content="0; url={}"/></head><body></body></html>'.format(report_path))
        
        
def get_percentual_diff(K: float, S: float):
    diff = (float(K) - S) / S * 100
    return '{:.2f}%'.format(diff)
    
    
if __name__ == '__main__':
    # Get all available tickers
    data_folder = 'data'
    output_folder = None
    available_tickers = [f for f in os.listdir(data_folder) if path.isdir(path.join(data_folder, f))]
    
    # Get current underlying prices for all the contracts under analysis
    current_prices = pd.read_csv('current.csv', sep=';', names=['ticker', 'last_price'], dtype={'ticker': str, 'last_price': float})

    # Iterate tickers to find important changes in open interest and volume
    movements = {}
    oi_plots_files = {}
    for ticker in available_tickers:
        # Get current underlying price
        S = float(current_prices.loc[current_prices.ticker == ticker, 'last_price'])
        
        # Get 2 last daily files to be compared
        ticker_data_folder = path.join(data_folder, ticker)
        daily_files = sorted([f for f in os.listdir(ticker_data_folder) if path.isfile(path.join(ticker_data_folder, f)) and f.lower().endswith('.json')])
        latest_daily_filepath = path.join(ticker_data_folder, daily_files[-1])
        previous_day_filepath = path.join(ticker_data_folder, daily_files[-2])
        
        # Load latest session data and previous day data
        ldf = pd.read_json(latest_daily_filepath)
        pdf = pd.read_json(previous_day_filepath)
        
        # Add a column to both DataFrames with the % diff between each strike and current underlying price
        ldf['diff_from_underlying_price'] = ldf['strike'].apply(get_percentual_diff, args=(S,))
        pdf['diff_from_underlying_price'] = pdf['strike'].apply(get_percentual_diff, args=(S,))
        
        # Look for big movements for each ticker
        movements[ticker] = get_big_movements(ldf, pdf)
        
        # Generate an open interest evolution plot for those options
        daily_files = [path.join(ticker_data_folder, f) for f in os.listdir(ticker_data_folder) if path.isfile(path.join(ticker_data_folder, f)) and f.lower().endswith('.json')]
        all_historical_data = pd.DataFrame()
        for file in daily_files:  # Append dataframe into a single dataframe with the info from all files
            df = pd.read_json(file)
            all_historical_data = all_historical_data.append(df)
        for key, df in movements[ticker].items(): #values()
            for index, row in df.iterrows():
                try:
                    filename = oip.plot_open_interest_evolution(all_historical_data, row.strike, row.expiration_date, ticker, True)
                    df.set_value(index, 'oiev_chart_filename', filename)
                except Exception as e:
                    print(key, ticker, type(row), row)
                    print('ERROR: Failed to create open interest evolution plot for {} {} expiring on {}'.format(ticker, row.strike, row.expiration_date))
                    print(e)
        
        # Create report folder (if it does not exist)
        if not output_folder:
            try:
                session_date = list(movements.values())[0]['highest_volume'].iloc[0].session_date
                output_folder = create_report_folder(session_date)
            except Exception as e:
                output_folder = 'aux'
        
        # Get all available expiration dates from previous session
        expiration_dates = pdf.expiration_date.unique()
        
        # Generate open interest plots for all the available expiration dates
        oi_plots_files[ticker] = []
        for t in expiration_dates:
            if datetime.strptime(session_date, '%d/%m/%Y') <= datetime.strptime(t, '%d/%m/%Y'):
                try:
                    image_filename = oip.plot_open_interest(ldf, t, ticker, True)
                    if image_filename:
                        oi_plots_files[ticker].append((t, path.join('img', image_filename)))
                except Exception as e:
                    traceback.print_exc()
                    print('ERROR: Failed to create open interest plot for {} expiring on {}'.format(ticker, t))
                    print(e)
            
    report_path = generate_oi_report(movements, output_folder, oi_plots_files, current_prices)
    generate_link_to_latest(report_path)