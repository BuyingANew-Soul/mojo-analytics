import time
from data_and_reports import load_and_report
from cointest import coin_test

if __name__ == '__main__':

    while True:
        sec = 0
        while sec == 0:
            load_and_report()
            coin_test()
            break
        for i in range(20):
            sec += 1
            time.sleep(1)
            star = "*"*i
            print(star)
        if sec == 20:
            continue


