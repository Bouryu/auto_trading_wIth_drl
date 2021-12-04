import backtrader as bt

class StopTrailer(bt.Indicator):
    _nextforce = True  # force system into step by step calcs

    lines = ('stop_long', 'stop_short',)
    plotinfo = dict(subplot=False, plotlinelabels=True)

    params = dict(
        atrperiod=14,
        emaperiod=10,
        stopfactor=3.0,
    )

    def __init__(self):
        self.strat = self._owner  # alias for clarity

        # Volatility which determines stop distance
        atr = bt.indicators.ATR(self.data, period=self.p.atrperiod)
        emaatr = bt.indicators.EMA(atr, period=self.p.emaperiod)
        self.stop_dist = emaatr * self.p.stopfactor

        # Running stop price calc, applied in next according to market pos
        self.s_l = self.data - self.stop_dist
        self.s_s = self.data + self.stop_dist

    def next(self):
        # When entering the market, the stop has to be set
        if self.strat.entering > 0:  # entering long
            self.l.stop_long[0] = self.s_l[0]
        elif self.strat.entering < 0:  # entering short
            self.l.stop_short[0] = self.s_s[0]

        else:  # In the market, adjust stop only in the direction of the trade
            if self.strat.position.size > 0:
                self.l.stop_long[0] = max(self.s_l[0], self.l.stop_long[-1])
            elif self.strat.position.size < 0:
                self.l.stop_short[0] = min(self.s_s[0], self.l.stop_short[-1])

#unused
class StopTrailerMulti(bt.Indicator):
    _nextforce = True  # force system into step by step calcs

    lines = ('stop_long', 'stop_short',)
    plotinfo = dict(subplot=False, plotlinelabels=True)

    params = dict(
        atrperiod=14,
        emaperiod=10,
        stopfactor=3.0,
    )

    def __init__(self):
        self.strat = self._owner  # alias for clarity

        self.inds = {}
        for i,d in enumerate(self.datas):
            self.inds[d] = {}
            # Volatility which determines stop distance
            self.inds[d]['atr'] = bt.indicators.ATR(d, period=self.p.atrperiod)
            self.inds[d]['emaatr'] = bt.indicators.EMA(self.inds[d]['atr'], period=self.p.emaperiod)
            self.inds[d]['stop_dist'] = self.inds[d]['emaatr'] * self.p.stopfactor

            # Running stop price calc, applied in next according to market pos
            self.inds[d]['s_l'] = d - self.inds[d]['stop_dist']
            self.inds[d]['s_s'] = d + self.inds[d]['stop_dist']

    def next(self):
        # When entering the market, the stop has to be set
        for i, d in enumerate(self.datas):
            if self.strat.entering > 0:  # entering long
                self.l.stop_long[0] = self.s_l[0]
            elif self.strat.entering < 0:  # entering short
                self.l.stop_short[0] = self.s_s[0]

            else:  # In the market, adjust stop only in the direction of the trade
                if self.strat.position.size > 0:
                    self.l.stop_long[0] = max(self.s_l[0], self.l.stop_long[-1])
                elif self.strat.position.size < 0:
                    self.l.stop_short[0] = min(self.s_s[0], self.l.stop_short[-1])
