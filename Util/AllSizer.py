import backtrader as bt
import math

class AllSizer(bt.Sizer):
    def _getsizing(self, comminfo, cash, data, isbuy):
        if isbuy:
            self.sizing = 0
            try:
                self.sizing = math.floor(cash/data.high)
            except:
                pass
            return self.sizing
        else:
            return self.broker.getposition(data)

