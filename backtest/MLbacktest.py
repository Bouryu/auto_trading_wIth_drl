import pandas as pd
import Util
import numpy as np
from datetime import datetime
import sqlite3
import talib._ta_lib as ta
import os
from backtrader.feeds import PandasData
os.environ['PATH'] += os.pathsep + 'C:/Program Files (x86)/Graphviz2.38/bin'


#set the period
start = datetime(2018, 11, 10)
end = datetime(2019, 12, 31)
d1 = start.strftime('%Y-%m-%d')
d2 = end.strftime('%Y-%m-%d')

#collect to historical data
db = sqlite3.connect('db3.db')
msft = pd.read_sql(
    con=db,
    sql=f'SELECT Date, Open, High, Low, Close, Volume  FROM MSFT WHERE Date BETWEEN  "{d1}" and "{d2}"')

msft.index = pd.to_datetime(msft['Date'])
date = pd.to_datetime(msft['Date'])
msft = msft.drop('Date',axis = 1)
msft.columns = ['open','high','low','close','volume']
# random factor
# msft['SMA5'] = ta.SMA(msft['close'], timeperiod=5)
# msft['SMA30'] = ta.SMA(msft['close'], timeperiod=30)
# msft['MOM'] = ta.MOM(msft['close'])
msft['STOCK-K'], msft['STOCK-D'] = ta.STOCH(msft['high'],msft['low'],msft['close'])
msft['RSI'] = ta.RSI(msft['close'])
macd, macdsignal, macdhist = ta.MACD(msft['close'])
msft['MACD'] = macd
msft['LW'] = ta.WILLR(msft['high'],msft['low'],msft['close'])
msft['CCI'] = ta.CCI(msft['high'],msft['low'],msft['close'])
msft['ADOSC'] = ta.ADOSC(msft['high'],msft['low'],msft['close'],msft['volume'])

import joblib
filename = 'RFR_27-2-ER.pkl'
stored_model = joblib.load(filename)

msft.isnull().sum()
data = msft.dropna()
pd.set_option('display.max_columns', None)
backtest_data = data[['open','high','low','close','volume']]

backtest_data['signal'] = stored_model.predict(data)
print(backtest_data)
import backtrader as bt


class MLStrategy(bt.Strategy):
    params = (('maperiod', 20),)

    def __init__(self):
        self.data_predicted = self.datas[0].signal

        self.data_open = self.datas[0].open
        self.data_close = self.datas[0].close

        self.order = None
        self.price = None
        self.comm = None

    def log(self, txt):
        '''Logging function'''
        dt = self.datas[0].datetime.date(0).isoformat()
        print(f'{dt}, {txt}')

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # order already submitted/accepted - no action required
            return
        # report executed order
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    f'BUY EXECUTED --- Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f},Commission: {order.executed.comm:.2f}'
                    )
                self.price = order.executed.price
                self.comm = order.executed.comm
            else:
                self.log(
                    f'SELL EXECUTED --- Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f},Commission: {order.executed.comm:.2f}'
                    )
        # report failed order
        elif order.status in [order.Canceled, order.Margin,
                              order.Rejected]:
            self.log(f'Order Failed {order.status}')
        # set no pending order
        self.order = None

        def notify_trade(self, trade):
            if not trade.isclosed:
                return
            self.log(f'OPERATION RESULT --- Gross: {trade.pnl:.2f}, Net: {trade.pnlcomm:.2f}')

        # We have set cheat_on_open = True.This means that we calculated the signals on day t's close price,
        # but calculated the number of shares we wanted to buy based on day t+1's open price.

    def next_open(self):
        if not self.position:
            if self.data_predicted > 0:
                # calculate the max number of shares ('all-in')
                size = int(self.broker.getcash() / self.datas[0].open)
                # buy order
                self.log(f'BUY CREATED --- Size: {size}, Cash: {self.broker.getcash():.2f}, Open: {self.data_open[0]}, Close: {self.data_close[0]}')
                self.buy(size=int(size*0.9))
    def next(self):
        if self.position:
            if self.data_predicted < 0:
                # sell order
                self.log(f'SELL CREATED --- Size: {self.position.size}')
                self.close()
                # self.sell(size=self.position.size)

# feed the data to dataframe
#feed_data = bt.feeds.PandasData(dataname=backtest_data, fromdate=start, todate=end)

OHLCV = ['open', 'high', 'low', 'close', 'volume']
# class to define the columns we will provide
class SignalData(PandasData):
    """
    Define pandas DataFrame structure
    """
    cols = OHLCV + ['signal']
# create lines
    lines = tuple(cols)
# define parameters
    params = {c: -1 for c in cols}
    params.update({'datetime': None})
    params = tuple(params.items())


feed_data = SignalData(dataname=backtest_data)
# initial the cerebro
cerebro = bt.Cerebro(cheat_on_open=True)
cerebro.adddata(feed_data)
cerebro.addstrategy(MLStrategy)
startCash = 100000
cerebro.broker.setcash(startCash)
cerebro.broker.setcommission(commission=0.0008)

print(f'initial cash: {startCash}')


cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name = 'SharpeRatio')
cerebro.addanalyzer(bt.analyzers.SQN, _name='SQN')

results = cerebro.run()
portValue = cerebro.broker.getvalue()
netProfit = portValue - startCash
strat = results[0]
print('Final Portfolio Value: %.2f' % portValue)
print('SR:', strat.analyzers.SharpeRatio.get_analysis())
print('SQN:', strat.analyzers.SQN.get_analysis())
print(f'Net Profit: {round(netProfit,2)}')
print(f'Profit Rate: {round(netProfit/startCash,3)}')

cerebro.plot(style='candlestick')