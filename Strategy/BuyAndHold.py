import backtrader as bt
import Util

class BuyAndHold(bt.Strategy):
    label = 'Buy&Hold'
    def __init__(self):
        self.sma60 = bt.ind.SMA(period = 60)
        self.sma20 = bt.ind.SMA(period = 20)
        self.setsizer(Util.AllSizer())

    def next(self):
        if not self.position:
            if self.data.close < self.sma60[0] and self.sma20[0] > self.sma20[-1]:
                self.buy()
