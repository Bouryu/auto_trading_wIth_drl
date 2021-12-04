import pandas as pd
from datetime import datetime
import backtrader as bt
import Strategy
import sqlite3

#set the period
start = datetime(2020, 1, 1)
end = datetime(2020, 12, 31)
d1=start.strftime('%Y-%m-%d')
d2=end.strftime('%Y-%m-%d')
stock_tag = "MSFT"
#collect to historical data
db = sqlite3.connect('db3.db')
msft = pd.read_sql(con=db, sql=f'SELECT Date, Open, High, Low, Close, Volume  FROM "{stock_tag}" WHERE Date BETWEEN  "{d1}" and "{d2}" ')

msft.index = pd.to_datetime(msft['Date'])
msft['openinterest'] = 0
msft = msft[['Open', 'High', 'Low', 'Close','Volume', 'openinterest']]

#feed the data to dataframe
data = bt.feeds.PandasData(dataname=msft,fromdate=start,todate=end)

#initial the cilent
cerebro = bt.Cerebro()
cerebro.adddata(data)
cerebro.addstrategy(Strategy.OldBuyAndHold)
startCash = 100000
cerebro.broker.setcash(startCash)
cerebro.broker.setcommission(commission=0.0005)
print(f'Initial cash: { startCash }')

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

cerebro.plot()