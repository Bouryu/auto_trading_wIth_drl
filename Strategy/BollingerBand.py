import backtrader as bt
import Util

class BollingerBand(bt.Strategy):
    params = (
        ("period", 20),
        ("devfactor", 2),
        ("size", 20)
    )
    def __init__(self):
        # Bollinger Band indicator
        self.boll = bt.indicators.BollingerBands()

        self.order = None


    def next(self):
        if self.order:
            return

        if not self.position:

            if self.data.close > self.boll.lines.top:
                self.sell(exectype=bt.Order.Stop, price=self.boll.lines.top[0], size=self.p.size)

            if self.data.close < self.boll.lines.bot:
                self.buy(exectype=bt.Order.Stop, price=self.boll.lines.bot[0], size=self.p.size)


        else:

            if self.position.size > 0:
                self.sell(exectype=bt.Order.Limit, price=self.boll.lines.mid[0], size=self.p.size)

            else:
                self.buy(exectype=bt.Order.Limit, price=self.boll.lines.mid[0], size=self.p.size)


class BollingerBandTrailingStopMulti(bt.Strategy):
    SHORT, NONE, LONG = -1, 0, 1
    label = 'BollingerBandTrailingStopMulti'
    params = (
        ("period", 20),
        ("devfactor", 2)
    )
    def __init__(self):
        # Bollinger Band indicator
        self.boll = bt.indicators.BollingerBands()
        self.setsizer(Util.PercentSizer(0.4))

        self.order = None

        self.stoptrailer = st = Util.StopTrailer(stopfactor=4.0)
        self.exit_long = bt.ind.CrossDown(self.data,
                                          st.stop_long, plotname='Exit Long')
        self.exit_short = bt.ind.CrossUp(self.data,
                                         st.stop_short, plotname='Exit Short')


    def next(self):
        for i,d in enumerate(self.datas):
            dt, dn = self.datetime.date(), d._name
            pos = self.getposition(d).size

        if self.order:
            return

        if not self.position:

            # if self.data.close > self.boll.lines.top:
            #     self.sell(exectype=bt.Order.Stop, price=self.boll.lines.top[0], size=self.p.size)

            if self.data.close < self.boll.lines.bot:
                self.buy(exectype=bt.Order.Stop, price=self.boll.lines.bot[0], size=self.p.size)


        else:

            if self.position.size > 0:
                self.sell(exectype=bt.Order.Limit, price=self.boll.lines.mid[0], size=self.p.size)

            else:
                self.buy(exectype=bt.Order.Limit, price=self.boll.lines.mid[0], size=self.p.size)
