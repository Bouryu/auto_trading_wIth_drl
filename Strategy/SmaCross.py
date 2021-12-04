import backtrader as bt
import math
import Util



class SmaCross(bt.Strategy):
    label = 'SmaCross'

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        sma1 = bt.ind.SMA(period=10)
        sma2 = bt.ind.SMA(period=30)
        self.crossover = bt.ind.CrossOver(sma1, sma2)
        self.setsizer(Util.AllSizer())
        self.dataclose = self.datas[0].close

    def next(self):
        if not self.position:
            if self.crossover > 0:
                self.buy(price=self.dataclose[0])
        elif self.crossover < 0:
            self.close(price=self.dataclose[0])

class SmaCrossTrailingStop(bt.Strategy):
    SHORT, NONE, LONG = -1, 0, 1
    label = 'SmaCrossTrailingStop'

    def __init__(self):
        sma1 = bt.ind.SMA(period=10)
        sma2 = bt.ind.SMA(period=30)
        self.crossover = bt.ind.CrossOver(sma1, sma2)
        self.setsizer(Util.AllSizer())
        self.dataclose = self.datas[0].close

        self.stoptrailer = st = Util.StopTrailer(stopfactor=4.0)
        self.exit_long = bt.ind.CrossDown(self.data,
                                          st.stop_long, plotname='Exit Long')
        self.exit_short = bt.ind.CrossUp(self.data,
                                         st.stop_short, plotname='Exit Short')

    def start(self):
        self.entering = 0
        self.start_val = self.broker.get_value()

    def next(self):
        if self.position.size > 0:  # In the market - Long
            if self.exit_long:
                closing = self.close()

        if not self.position:
            # Not in the market or closing pos and reenter in samebar
            if self.crossover > 0:
                self.buy()

class SmaCrossTrailingStopMulti(bt.Strategy):
    SHORT, NONE, LONG = -1, 0, 1
    label = 'SmaCrossTrailingStopMulti'

    def __init__(self):
        self.inds = {}
        for i, d in enumerate(self.datas):
            self.inds[d] = {}
            self.inds[d]['sma1'] = bt.indicators.SimpleMovingAverage(d.close, period=10)
            self.inds[d]['sma2'] = bt.indicators.SimpleMovingAverage(d.close, period=30)
            self.inds[d]['crossover'] = bt.indicators.CrossOver(self.inds[d]['sma1'], self.inds[d]['sma2'])
            self.inds[d]['order'] = None
            #self.inds[d]['stop_trailer'] = Util.StopTrailer(stopfactor=4.0)
            #self.inds[d]['exit'] = bt.indicators.CrossDown(d.close, self.inds[d]['stop_trailer'].stop_long)

        #self.dataclose = self.datas[0].close

        #self.stoptrailer = st = Util.StopTrailer(stopfactor=4.0)
        #self.exit_long = bt.ind.CrossDown(self.data, st.stop_long, plotname='Exit Long')

    def start(self):
        self.entering = 0
        self.start_val = self.broker.get_value()

    def next(self):
        for i, d in enumerate(self.datas):
            dt, dn = self.datetime.date(), d._name
            pos = self.getposition(d)
            if not pos: # not in market
                if self.inds[d]['crossover'] > 0:
                    o = self.buy(data=d)
                    self.inds[d]['order'] = None

            elif self.inds[d]['order'] is None:
                # if self.inds[d]['crossover'] < 0:
                #     self.inds[d]['order'] = self.close(data=d)
                # else:
                self.inds[d]['order'] = self.close(data=d, exectype=bt.Order.StopTrail,
                          trailpercent=0.02)

