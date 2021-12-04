from datetime import datetime
import backtrader as bt
import math
from dateutil.relativedelta import relativedelta

class RegularBuy(bt.Strategy):
    def __init__(self):
        self.next_buy_date = datetime(2010, 1, 1)
        self.sma60 = bt.ind.SMA(period = 60)
        self.sma20 = bt.ind.SMA(period = 20)
        self.total_cash = 0
        self.addCash = 1000

    def next(self):
        current_date = self.data.datetime.date()
        if current_date >= self.next_buy_date.date():
            if self.data.close < self.sma60[0] and self.sma20[0] > self.sma20[-1] :
                price = (self.data.high + self.data.low) / 2.0
                volume = math.floor(self.broker.cash / price)
                print(volume)
                self.buy(size=volume)
                self.broker.add_cash(cash=self.addCash)
                self.total_cash += self.addCash
                self.next_buy_date = datetime.combine(current_date, datetime.min.time()) + relativedelta(months=1)

    def stop(self):
        print(f'Total Cash: {self.total_cash}')