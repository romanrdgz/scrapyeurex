#! /usr/bin/env python
# -*- coding: utf-8 -*
import os
from os import path
import shutil
import pandas as pd
import jinja2
from datetime import datetime
import open_interest_plot as oip


def get_big_movements(ldf: pd.DataFrame, pdf: pd.DataFrame, n=10):
    # Get N options with higher volume in the last day of trading available
    ldf_high_volume = ldf[ldf.volume > 0].nlargest(n, 'volume')
    ldf['oiev_chart_filename'] = ldf['expiration_date'].apply(lambda x: datetime.strptime(x, '%d/%m/%Y').strftime('%Y%m%d'))
        
    # Merge with previous day data and compare to detect important changes in open interest
    mdf = ldf.merge(pdf, on=['strike', 'right', 'expiration_date'], how='inner', suffixes=('_latest', '_previous'))
    mdf['open_interest_diff'] = mdf.apply(lambda x: x['open_interest_latest'] - x['open_interest_previous'], axis=1)
    mdf['open_interest_diff_pc'] = mdf.apply(lambda x: '{:.2f}%'.format(100 * (x['open_interest_latest'] - x['open_interest_previous']) / x['open_interest_previous']) if x['open_interest_previous'] > 0 else 'N/A', axis=1)
    mdf['oiev_chart_filename'] = mdf['expiration_date'].apply(lambda x: datetime.strptime(x, '%d/%m/%Y').strftime('%Y%m%d'))
        
    # Get options with greater change in open interest (N positive and N negative)
    mdf_lowest_changers = mdf.nsmallest(n, 'open_interest_diff')
    mdf_highest_changers = mdf.nlargest(n, 'open_interest_diff')
        
    # Return as dict
    return {'highest_volume': ldf_high_volume, 'lowest_changers': mdf_lowest_changers, 'highest_changers': mdf_highest_changers}

    
def create_report_folder(session_date: str):
    output_folder = 'report_{}'.format(session_date.replace('/', ''))
    output_folder_path = path.join('reports', output_folder)
    if not path.exists(output_folder_path):
        os.makedirs(output_folder_path)
    return output_folder_path
    
        
def generate_oi_report(movements, output_folder, oi_plots_files):
    templateLoader = jinja2.FileSystemLoader('templates')
    templateEnv = jinja2.Environment(
	    autoescape=False,
		loader=templateLoader,
		trim_blocks=False)
    template = templateEnv.get_template('report_template_tabbed.html')

    session_date = list(movements.values())[0]['highest_volume'].iloc[0].session_date
    tickers_list = movements.keys()
    
    volume_data = {}
    oi_data = {}
    portfolio_data = {}
    for ticker in tickers_list:
        volume_data[ticker] = {}
        volume_data[ticker]['hv_option_list'] =  [opt for _, opt in movements[ticker]['highest_volume'].iterrows()]
        volume_data[ticker]['poi_option_list'] = [opt for _, opt in movements[ticker]['highest_changers'].iterrows()]
        volume_data[ticker]['noi_option_list'] = [opt for _, opt in movements[ticker]['lowest_changers'].iterrows()]
        
        oi_data[ticker] = oi_plots_files[ticker]
        
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
    with open(path.join(output_folder, output_file), 'w') as f:
        f.write(output_html)

        
if __name__ == '__main__':
    # Get all available tickers
    data_folder = 'data'
    output_folder = None
    available_tickers = [f for f in os.listdir(data_folder) if path.isdir(path.join(data_folder, f))]

    # Iterate tickers to find important changes in open interest and volume
    movements = {}
    oi_plots_files = {}
    for ticker in available_tickers:
        # Get 2 last daily files to be compared
        ticker_data_folder = path.join(data_folder, ticker)
        daily_files = sorted([f for f in os.listdir(ticker_data_folder) if path.isfile(path.join(ticker_data_folder, f)) and f.lower().endswith('.json')])
        latest_daily_filepath = path.join(ticker_data_folder, daily_files[-1])
        previous_day_filepath = path.join(ticker_data_folder, daily_files[-2])
        
        # Load latest session data and previous day data
        ldf = pd.read_json(latest_daily_filepath)
        pdf = pd.read_json(previous_day_filepath)
        
        # Look for big movements for each ticker
        movements[ticker] = get_big_movements(ldf, pdf)
        
        # Generate an open interest evolution plot for those options
        daily_files = [path.join(ticker_data_folder, f) for f in os.listdir(ticker_data_folder) if path.isfile(path.join(ticker_data_folder, f)) and f.lower().endswith('.json')]
        all_historical_data = pd.DataFrame()
        for file in daily_files:  # Append dataframe into a single dataframe with the info from all files
            df = pd.read_json(file)
            all_historical_data = all_historical_data.append(df)
        for df in movements[ticker].values():
            for index, row in df.iterrows():
                try:
                    filename = oip.plot_open_interest_evolution(all_historical_data, row.strike, row.expiration_date, ticker, True)
                    df.set_value(index, 'oiev_chart_filename', filename)
                except Exception as e:
                    print('ERROR: Failed to create open interest evolution plot for {} {} expiring on {}'.format(ticker, row.strike, row.expiration_date))
                    print(e)
        
        # Create report folder (if it does not exist)
        session_date = list(movements.values())[0]['highest_volume'].iloc[0].session_date
        output_folder = create_report_folder(session_date)
        
        # Get all available expiration dates from previous session
        expiration_dates = pdf.expiration_date.unique()
        
        # Generate open interest plots for all the available expiration dates
        oi_plots_files[ticker] = []
        for t in expiration_dates:
            try:
                image_filename = oip.plot_open_interest(ldf, t, ticker, True)
                if image_filename:
                    oi_plots_files[ticker].append((t, path.join('img', image_filename)))
            except Exception as e:
                print('ERROR: Failed to create open interest plot for {} expiring on {}'.format(ticker, t))
                print(e)
    
    generate_oi_report(movements, output_folder, oi_plots_files)