import py_vollib.black_scholes as bs
import py_vollib.black_scholes.implied_volatility as bsiv
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
'''
import seaborn as sns
sns.set(style='darkgrid')
sns.set(color_codes=True)
'''


def plot_risk_graph(options_data, S, r, save_png=False):
    '''
    Creates a risk graph for the combination of options provided
    in the input list of options for the different times to
    expiration provided

    inputs:
    options_data -> options data composing the strategy. It is important
        to provide this list ordered by near-term expiries first
    S -> current underlying price
    r -> interest rate on a 3-month U.S. Treasury bill or similar
    save_png -> determines if the plot is saved as a PNG file (default False)
    returns:
        list of tuples (x, (datetime, y))
    '''
    # Get the list of options from options_data
    options_list = options_data['options']
    
    # First get the graph bounds, 10% apart from the min and max strikes
    min_strike = None
    max_strike = None
    for opt in options_list:
        if (min_strike is None) or (opt['strike'] < min_strike):
            min_strike = opt['strike']
        if (max_strike is None) or (opt['strike'] > max_strike):
            max_strike = opt['strike']
    # Make sure current underlying price is into the range
    if min_strike > S:
        min_strike = S
    if max_strike < S:
        max_strike = S
            
    # Determine front expiration date
    front_expiration = None
    back_expiration = None
    for opt in options_list:
        aux_date = datetime.strptime(opt['expiration_date'], '%d/%m/%Y')
        if (front_expiration is None) or (aux_date < front_expiration):
            front_expiration = aux_date
        if (back_expiration is None) or (aux_date > back_expiration):
            back_expiration = aux_date

    # Prices vector
    strike_spread = max_strike - min_strike
    x_vector = np.linspace(min_strike - strike_spread * 0.1, max_strike + strike_spread * 0.1, 500)

    # Now plot the risk graph for the different time values provided
    return_values = []
    y = []
    for t in [datetime.today(), front_expiration, back_expiration]:
        y_vector = np.zeros(len(x_vector))
        y_vector.fill(options_data['meta']['amount'] *  options_data['meta']['multiplier'] * options_data['meta']['premium'] - options_data['meta']['commisions'])
        y.append(y_vector)
        # Create the discrete values of P/L to plot against xrange
        for opt in options_list:
            # Get time to expiration in years
            days_to_expire = (datetime.strptime(opt['expiration_date'], '%d/%m/%Y') - t).days
            t_exp = days_to_expire / 365.
            if t_exp >= 0:
                # Calculate IV from latest option price
                iv = bsiv.implied_volatility(opt['last_price'], S, opt['strike'], t_exp, r, opt['right'].lower())
                
                # Calculate option price using black-scholes given that IV
                y[-1] += np.array(
                    [
                        options_data['meta']['amount'] * options_data['meta']['multiplier'] * opt['amount'] * 
                        bs.black_scholes(opt['right'].lower(), x, opt['strike'], t_exp, r, iv)
                        for x in x_vector
                    ])

        # Get the number of days to expiration from today for plot's legend
        plt.plot(x_vector, y[-1], label='t: ' + str(days_to_expire))
        return_values.append((t, y[-1]))

    # Plot a vertical line where the underlying is currently trading at
    plt.axvline(S, color='r')
    
    # Plot zero horizontal line
    plt.axhline(0, color='k', linestyle='dashed')
    
    plt.legend()
    plt.xlabel('Price')
    plt.ylabel('P/L')
    # Save the plot as a PNG if required, or show plot in a window
    if save_png:
        plt.savefig(datetime.today().strftime(options_data.meta.ticker + '_%d%b%y.png'))
    else:
        # Show the plot
        plt.show()

    # Return the values calculated TODO for what? to calculate breakevens?
    return (x_vector, return_values)
