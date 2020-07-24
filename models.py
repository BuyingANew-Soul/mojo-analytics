import numpy as np
import pandas as pd
from pykalman import KalmanFilter
from numpy import log, polyfit, sqrt, std, subtract
import statsmodels.tsa.stattools as ts
import statsmodels.api as sm
from datetime import datetime


def names_of_fig():
    now = datetime.now()
    date = "-".join([str(now.day), str(now.month), str(now.year)])
    time = "-".join([str(now.hour), str(now.minute), str(now.second)])
    name = time + " " + date + ".png"
    return name


# define functions
def load_data():
    # set the working directory
    import os
    # os.getcwd() # this is to check the current working directory
    # os.chdir("D://EPAT//09 FP//")
    all_contracts = pd.read_csv('data sets/PriceData_bk.csv', index_col='tradeDate', parse_dates=True)
    p_sorted = pd.read_csv('data sets/training_p_sorted_tmp.csv', index_col='id', parse_dates=False)

    return all_contracts, p_sorted


def hurst(ts):
    """Returns the Hurst Exponent of the time series vector ts"""
    # Create the range of lag values
    lags = range(2, 100)

    # Calculate the array of the variances of the lagged differences
    tau = [sqrt(std(subtract(ts[lag:], ts[:-lag]))) for lag in lags]

    # Use a linear fit to estimate the Hurst Exponent
    poly = polyfit(log(lags), log(tau), 1)

    # Return the Hurst exponent from the polyfit output
    return poly[0] * 2.0


###############################################################################
##### ADF TEST
###############################################################################

# Calculate the spread of each pair (Spread = Y – hedge ratio * X )

def adf_test(x, y):
    df = pd.DataFrame({'y': y, 'x': x})
    est = sm.OLS(df.y, df.x)
    est = est.fit()
    df['hr'] = -est.params[0]
    df['spread'] = df.y + (df.x * df.hr)

    cadf = ts.adfuller(df.spread)
    return cadf[1]


###############################################################################
##### Using Kalman Filter Regression Function to calculate *hedge ratio*
##### Calculate z-score of ‘s’, using *rolling mean* and *standard deviation* for
##### the time period of ‘half-life’ intervals. Save this as z-score
##### Using half-life function to calculate the half-life
###############################################################################


def half_life(spread):
    spread_lag = spread.shift(1)
    spread_lag.iloc[0] = spread_lag.iloc[1]

    spread_ret = spread - spread_lag
    spread_ret.iloc[0] = spread_ret.iloc[1]

    spread_lag2 = sm.add_constant(spread_lag)

    model = sm.OLS(spread_ret, spread_lag2)
    res = model.fit()
    halflife = int(round(-np.log(2) / res.params[1], 0))
    # halflife = float(round(-np.log(2) / res.params[1],0))

    if halflife <= 0:
        halflife = 1
    return halflife


def KalmanFilterAverage(x):
    # Construct a Kalman filter
    from pykalman import KalmanFilter
    kf = KalmanFilter(transition_matrices=[1],
                      observation_matrices=[1],
                      initial_state_mean=0,
                      initial_state_covariance=1,
                      observation_covariance=1,
                      transition_covariance=.01)

    # Use the observed values of the price to get a rolling mean
    state_means, _ = kf.filter(x.values)
    state_means = pd.Series(state_means.flatten(), index=x.index)
    return state_means


#  Kalman filter regression
def KalmanFilterRegression(x, y):
    delta = 1e-3
    trans_cov = delta / (1 - delta) * np.eye(2)  # How much random walk wiggles
    obs_mat = np.expand_dims(np.vstack([[x], [np.ones(len(x))]]).T, axis=1)

    kf = KalmanFilter(n_dim_obs=1, n_dim_state=2,  # y is 1-dimensional, (alpha, beta) is 2-dimensional
                      initial_state_mean=[0, 0],
                      initial_state_covariance=np.ones((2, 2)),
                      transition_matrices=np.eye(2),
                      observation_matrices=obs_mat,
                      observation_covariance=2,
                      transition_covariance=trans_cov)

    # Use the observations y to get running estimates and errors for the state parameters
    state_means, state_covs = kf.filter(y.values)
    return state_means


###############################################################################################################################


###############################################################################
##### BACKTEST - *NOT YET - We need clean working data otherwise we endup with
##### floating point conversions 😢*
###############################################################################


def backtest(s1, s2, x, y):
    #############################################################
    # run regression to find hedge ratio
    # and then create spread series
    df1 = pd.DataFrame({'y': y, 'x': x})
    state_means = KalmanFilterRegression(KalmanFilterAverage(x), KalmanFilterAverage(y))

    df1['hr'] = - state_means[:, 0]
    df1['spread'] = df1.y + (df1.x * df1.hr)

    ##############################################################
    halflife = half_life(df1['spread'])

    ##############################################################

    meanSpread = df1.spread.rolling(window=halflife).mean()
    stdSpread = df1.spread.rolling(window=halflife).std()

    df1['zScore'] = (df1.spread - meanSpread) / stdSpread

    ##############################################################

    entryZscore = 2
    exitZscore = 0

    # set up num units long
    df1['long entry'] = ((df1.zScore < - entryZscore) & (df1.zScore.shift(1) > - entryZscore))
    df1['long exit'] = ((df1.zScore > - exitZscore) & (df1.zScore.shift(1) < - exitZscore))
    df1['num units long'] = np.nan
    df1.loc[df1['long entry'], 'num units long'] = 1
    df1.loc[df1['long exit'], 'num units long'] = 0
    df1['num units long'][0] = 0
    df1['num units long'] = df1['num units long'].fillna(method='pad')

    # set up num units short
    df1['short entry'] = ((df1.zScore > entryZscore) & (df1.zScore.shift(1) < entryZscore))
    df1['short exit'] = ((df1.zScore < exitZscore) & (df1.zScore.shift(1) > exitZscore))
    df1.loc[df1['short entry'], 'num units short'] = -1
    df1.loc[df1['short exit'], 'num units short'] = 0
    df1['num units short'][0] = 0
    df1['num units short'] = df1['num units short'].fillna(method='pad')

    df1['numUnits'] = df1['num units long'] + df1['num units short']
    df1['spread pct ch'] = (df1['spread'] - df1['spread'].shift(1)) / ((df1['x'] * abs(df1['hr'])) + df1['y'])
    df1['port rets'] = df1['spread pct ch'] * df1['numUnits'].shift(1)

    df1['cum rets'] = df1['port rets'].cumsum()
    df1['cum rets'] = df1['cum rets'] + 1

    try:
        sharpe = ((df1['port rets'].mean() / df1['port rets'].std()) * sqrt(252))
    except ZeroDivisionError:
        sharpe = 0.0

    #############################################################
    return df1['cum rets'], sharpe


def potential_pairs(all_contracts, p_sorted):
    list_sect = []
    ret = pd.DataFrame()
    for i in np.arange(p_sorted.shape[0]):

        #print("The total # of testing is: ", p_sorted.shape[0], " Current: ", i)
        s1 = p_sorted.iloc[i][1]
        s2 = p_sorted.iloc[i][0]

        name = s1 + "-" + s2

        x = all_contracts[s1]
        y = all_contracts[s2]

        tmp, sharpe = backtest(s1, s2, x, y)
        if sharpe > 0.5 and tmp.values[-1] > 1.105:
            ret[name] = tmp.values
            list_sect.append((s1, s2))
    return ret, list_sect


# SAMPLE BACKＴＥＳＩＮＧ
def sample_backtest(list_sect):

    testing_data = pd.read_csv('data sets/PriceData_Test03.csv', index_col='tradeDate', parse_dates=True)

    test_ret = pd.DataFrame()
    for i in np.arange(len(list_sect)):
        # print("The total # of testing is: ", p_sorted.shape[0], " Current: ", i)
        s1 = list_sect[i][1]
        s2 = list_sect[i][0]

        name = s1 + "-" + s2

        x = testing_data[s1]
        y = testing_data[s2]

        test_ret[name], sharpe = backtest(s1, s2, x, y)
        return test_ret, testing_data