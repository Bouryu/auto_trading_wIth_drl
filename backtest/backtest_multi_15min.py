import pandas as pd
from datetime import datetime
import backtrader as bt
import Strategy
import Util
from Model import DatabaseModel

#config
START_CASH = 100000
COMMISSION_RATE = 0.0001

# strategy list for backtest
STRATEGY = Strategy.SmaCrossTrailingStopMulti
SYMBOL = ['AAPL', 'ORCL', 'TSLA', 'MSFT']

start = datetime(2020, 12, 1)
end = datetime(2020, 12, 31)
d1 = start.strftime('%Y-%m-%d')
d2 = end.strftime('%Y-%m-%d')
db = DatabaseModel.StockDB15Min()

cerebro = bt.Cerebro()
cerebro.addsizer(bt.sizers.PercentSizer, percents=30)
# cerebro.addsizer(bt.sizers.FixedSize, stake=20)
#collect to historical data
for s in SYMBOL:
    dataset = db.get_stock_historical_in_panda_dataframe(s, start, end)
    dataset.index = pd.to_datetime(dataset['Date'])
    dataset['openinterest'] = 0
    dataset = dataset[['Open', 'High', 'Low', 'Close', 'Volume', 'openinterest']]
    data = bt.feeds.PandasData(dataname=dataset, fromdate=start, todate=end)
    cerebro.adddata(data)



cerebro.addstrategy(STRATEGY)
cerebro.broker.setcash(START_CASH)
cerebro.broker.setcommission(commission=COMMISSION_RATE)

#add analyzer and run the backtest
cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='SharpeRatio')
cerebro.addanalyzer(bt.analyzers.SQN, _name='SQN')
results = cerebro.run()

portValue = cerebro.broker.getvalue()
netProfit = portValue - START_CASH
strat = results[0]
print('Final Portfolio Value: %.2f' % portValue)
print('SR:', strat.analyzers.SharpeRatio.get_analysis())
print('SQN:', strat.analyzers.SQN.get_analysis())
print(f'Net Profit: {round(netProfit,2)}')
print(f'Profit Rate: {round(netProfit/START_CASH,3)}')

cerebro.plot()