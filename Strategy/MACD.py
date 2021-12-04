import backtrader as bt
import Util

class macd(bt.Strategy):
    label = 'MACD'
    params = (
        ('code', 0),
        ('profits', [])
    )

    def log(self, txt, dt=None, doprint=True):
        if doprint:
            dt = dt or self.datas[0].datetime.date(0)
            print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        self.dataclose = self.datas[0].close
        me1 = bt.indicators.EMA(self.data, period=12)
        me2 = bt.indicators.EMA(self.data, period=26)
        self.setsizer(Util.AllSizer())
        self.macd = me1 - me2
        self.signal = bt.indicators.EMA(self.macd, period=9)

    def notify_order(self, order):
        # 交易状态处理
        # Python实用宝典
        if order.status in [order.Submitted, order.Accepted]:
            return
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    "BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f"
                    % (order.executed.price, order.executed.value, order.executed.comm)
                )

                # 记录买入价格
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
                self.bar_executed_close = self.dataclose[0]
            else:
                self.log(
                    "SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f"
                    % (order.executed.price, order.executed.value, order.executed.comm)
                )
                # 收益率计算
                profit_rate = float(order.executed.price - self.buyprice) / float(self.buyprice)
                # 存入策略变量
                self.params.profits.append(profit_rate)
            self.bar_executed = len(self)

    def next(self):
        if not self.position:
            condition1 = self.macd[-1] = self.signal[-1]
            condition2 = self.macd[0] = self.signal[0]

            if condition1 < 0 and condition2 > 0:
                self.order = self.buy()

        else:
            condition = (self.dataclose[0] - self.bar_executed_close) / self.dataclose[0]
            if condition > 0.1 or condition < -0.1:
                self.order = self.close()
