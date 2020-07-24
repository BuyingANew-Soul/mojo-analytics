from models import load_data, names_of_fig, potential_pairs, sample_backtest
import ffn
import matplotlib.pyplot as plt
import os


def load_and_report():

    # fetching the current time as name
    name = names_of_fig()

    #  load Pricing test data
    all_contracts, p_sorted = load_data()

    # List contracts
    print(f"Showing all_contracts..........\n{all_contracts.tail(10)}\n")
    print(f"Showing p_sorted......\n{p_sorted.tail(10)}\n")



    # output from potential_pair
    ret, list_sect = potential_pairs(all_contracts, p_sorted)

    print(f"showing list_sect.......\n{list_sect}\n")
    print(f"showing ret........\n{ret.tail(10)}\n")

    # show the results of in sample testing
    ret.iloc[0] = 1
    ret.index = all_contracts.index
    plt.figure(figsize=(15, 7))
    plt.xlabel('Trade Date')
    plt.grid(True)
    plt.plot(ret)
    plt.legend(list(ret.columns))
    plt.show()
    plt.savefig(os.path.join("charts/sample test", "sample test " + name))

    # calculate the performance
    perf = ret.calc_stats()
    perf.display()
    perf.to_csv(sep=',', path="train_perfer.csv")

    # plot the maxinum drawndown of each pair
    ffn_ret = ffn.to_drawdown_series(ret)

    plt.figure(figsize=(15, 7))
    plt.grid(True)
    plt.plot(ffn_ret)
    plt.legend(list(ffn_ret.columns))
    plt.show()
    plt.savefig(os.path.join("charts/ffn drawdown", "ffn max drawdown " + name))

    # In sample back testing of portfolio

    port = ret.mean(axis=1)
    plt.figure(figsize=(15, 7))
    plt.grid(True)
    plt.plot(port)
    plt.show()
    #plt.legend(list(port.columns))
    plt.savefig(os.path.join("charts/testing of portfolio", "portfolio test " + name))

    perf = port.calc_stats()

    print(f"\n\nPrinting perf stats.......\n{perf.stats}\n")

    # In sample back testing of portfolio maxinum drawndown
    ffn_port = ffn.to_drawdown_series(port)
    plt.figure(figsize=(15, 7))
    plt.grid(True)
    plt.plot(ffn_port)
    #plt.legend(list(ffn_port.columns))
    plt.savefig(os.path.join("charts/back testing of portfolio maxinum drawndown", "maxinum drawndown " + name))

    ####################
    ##sample back testing######
    #####################
    test_ret, testing_data = sample_backtest(list_sect)

    print(f"\n\n\nShowing sample back testing- testing data tail.......\n\n{testing_data.tail(3)}\n")

    test_ret.iloc[0] = 1
    print(f"\n\nShowing sample backtesting test_ret tail.......\n\n{test_ret.tail(3)}")
    print(f"\n\nshowing test_ret shape......\n\n{test_ret.shape})")
    print(f"\n\n\nshowing test_ret index........\n\n{test_ret.index}")

    # plotting test_ret sample back testing
    plt.plot(test_ret)
    plt.legend(list(test_ret.columns))
    plt.savefig(os.path.join("charts/sample Backtesting/test_ret", "test_ret " + name))

    # Out sample back testing of portfolio

    port = test_ret.mean(axis=1)
    plt.figure(figsize=(15, 7))
    plt.grid(True)
    plt.plot(port)

    # plt.legend(list(port.columns))
    plt.savefig(os.path.join("charts/sample Backtesting/portfolio", "backtesting portfolio " + name))

    perf = port.calc_stats()
    print(perf.stats)

    ffn_backtest_sample = ffn.to_drawdown_series(port)
    plt.figure(figsize=(15, 7))
    plt.grid(True)
    plt.plot(ffn_backtest_sample)

    # plt.legend(list(ffn_backtest_sample.columns))
    plt.savefig(os.path.join("charts/sample Backtesting/ffn_drawdown_port", "drwadown_port " + name))

    return None


