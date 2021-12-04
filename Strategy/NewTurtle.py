import backtrader as bt
import Util

class Turtle(bt.Strategy):
    label = 'turtle'
    def __init__(self):
        sma = bt.indicators.SMA(period=5)
        self.dataclose = self.datas[0].close
        self.datahigh = self.datas[0].high
        self.datalow = self.datas[0].low

        self.setsizer(Util.AllSizer())

        high = bt.indicators.Highest(self.datahigh(-1), period=20,subplot=False)
        low = bt.indicators.Lowest(self.datalow(-1), period=10,subplot=False)

        self.CrossoverHi = bt.ind.CrossOver(self.dataclose(0), high)
        self.CrossoverLo = bt.ind.CrossOver(self.dataclose(0), low)

        highLong = bt.indicators.Highest(self.datahigh(-1), period=55, subplot=False)
        lowLong = bt.indicators.Lowest(self.datalow(-1), period=20, subplot=False)

        self.CrossoverHiLong = bt.ind.CrossOver(self.dataclose(0), highLong)
        self.CrossoverLoLong = bt.ind.CrossOver(self.dataclose(0), lowLong)

    def next(self):
        if not self.position:
            if self.CrossoverHi > 0 or self.CrossoverHiLong > 0:
                self.order = self.buy()
        elif self.CrossoverHi > 0 or self.CrossoverHiLong > 0:
            self.order = self.buy()
        elif self.CrossoverLo < 0 or self.CrossoverLoLong < 0:
            self.order = self.close()

