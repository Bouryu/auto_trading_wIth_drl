import backtrader as bt
class RSI(bt.Strategy):
    label = 'RSI'
    def __init__(self):
        #Relative Strength Index & MA
        self.rsi = bt.indicators.RSI_SMA(self.data.close, period=14)

    def next(self):
        if not self.position:
            if self.rsi < 30:
                self.buy(size=20)
        else:
            if self.rsi > 70:
                self.sell(size=20)