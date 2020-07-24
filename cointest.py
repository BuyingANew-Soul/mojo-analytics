import pandas as pd
from matplotlib import pyplot as plt
import requests
import statsmodels.tsa.stattools as ts
from statsmodels.tsa.vector_ar.vecm import coint_johansen


def get_bitfinex_asset(asset, ts_ms_start, ts_ms_end):
    url = 'https://api.bitfinex.com/v2/candles/trade:1D:t' + asset + '/hist'
    params = { 'start': ts_ms_start, 'end': ts_ms_end, 'sort': 1}
    r = requests.get(url, params = params)
    data = r.json()
    return pd.DataFrame(data)[2]


def coin_test():
    start_date = 1580515200000  # 1 January 2018, 00:00:00
    end_date = 1585612800000  # 31 May 2018, 23:59:59
    assets = ['EOSUSD', 'BTCUSD', 'ETHUSD', 'LTCUSD', 'TRXUSD', 'NEOUSD', 'ETCUSD', 'XLMUSD']

    crypto_prices = pd.DataFrame()

    print("\n\nStaring cointest function............\n")
    for a in assets:
        print('Downloading ' + a)
        crypto_prices[a] = get_bitfinex_asset(asset=a, ts_ms_start=start_date, ts_ms_end=end_date)

    crypto_prices.head()

    # Normalize prices by first value
    norm_prices = crypto_prices.divide(crypto_prices.iloc[0])
    print(f'\n\n\nPrinting norm prices....\n\n{norm_prices}\n\n')
    plt.figure(figsize=(15, 10))
    plt.plot(norm_prices)
    plt.xlabel('days')
    plt.title('Performance of cryptocurrencies')
    plt.legend(assets)
    plt.show()

    df_dic = {
        'asset pairs': [],
        'test result': []
    }
    for a1 in crypto_prices.columns:
        for a2 in crypto_prices.columns:
            if a1 != a2:
                test_result = ts.coint(crypto_prices[a1], crypto_prices[a2])
                # print(a1 + ' and ' + a2 + ': p-value = ' + str(test_result[1]))
                df_dic['asset pairs'].append(a1 + ' and ' + a2)
                df_dic['test result'].append(test_result[1])




