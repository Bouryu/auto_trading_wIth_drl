import pandas as pd
from datetime import datetime
import backtrader as bt
import Strategy
from Model import DatabaseModel
import matplotlib.pyplot as plt
import seaborn as sns

#config
START_YEAR = 2016
END_YEAR = 2019
SYMBOL_TEST_AMOUNT = 30
START_CASH = 100000
COMMISSION_RATE = 0.0005

# strategy list for backtest
STRATEGY_LIST = [
    Strategy.BuyAndHold,
    Strategy.SmaCross,
    Strategy.SmaCrossTrailingStop,
    Strategy.macd,
    Strategy.Turtle
]


def load_symbol_list_by_volume(year, topn):
    # get top n symbol that have highest average volume in the year
    df = pd.read_csv('stock_volume_group_by_year.csv')
    return df.sort_values(str(year), ascending=False)['symbol'].to_list()[:topn]


SYMBOL_LIST = load_symbol_list_by_volume(START_YEAR-1, SYMBOL_TEST_AMOUNT)

X_LABEL = SYMBOL_LIST
Y_LABEL = []
for item in STRATEGY_LIST:
    Y_LABEL.append(item.label)

profit_storage = {}
sharpe_storage = {}
sqn_storage = {}


start = datetime(START_YEAR, 1, 1)
end = datetime(END_YEAR, 12, 31)
d1 = start.strftime('%Y-%m-%d')
d2 = end.strftime('%Y-%m-%d')
db = DatabaseModel.StockDB()
for symbol in SYMBOL_LIST:
    #prepare dataset for testing
    dataset = db.get_stock_historical_in_panda_dataframe(symbol, start, end)
    dataset.index = pd.to_datetime(dataset['Date'])
    dataset['openinterest'] = 0
    dataset = dataset[['Open', 'High', 'Low', 'Close', 'Volume', 'openinterest']]
    data = bt.feeds.PandasData(dataname=dataset, fromdate=start, todate=end)

    for strat in STRATEGY_LIST:
        #setup
        cerebro = bt.Cerebro()
        cerebro.adddata(data)
        cerebro.addstrategy(strat)
        cerebro.broker.setcash(START_CASH)
        cerebro.broker.setcommission(commission=COMMISSION_RATE)

        #add analyzer and run the backtest
        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='SharpeRatio')
        cerebro.addanalyzer(bt.analyzers.SQN, _name='SQN')
        results = cerebro.run()

        #obtain result
        strat = results[0]
        sharpe_ratio = strat.analyzers.SharpeRatio.get_analysis()
        sqn = strat.analyzers.SQN.get_analysis()
        net_profit = (cerebro.broker.getvalue() - START_CASH) / START_CASH

        #store the result
        if strat.label not in profit_storage:
            profit_storage[strat.label] = []
        if strat.label not in sharpe_storage:
            sharpe_storage[strat.label] = []
        if strat.label not in sqn_storage:
            sqn_storage[strat.label] = []
        profit_storage[strat.label].append(net_profit)
        sharpe_storage[strat.label].append(sharpe_ratio['sharperatio'])
        sqn_storage[strat.label].append(sqn['sqn'])

print('average profit:')
for key,val in profit_storage.items():
    print({key})

df_profit = pd.DataFrame(data=profit_storage, index=X_LABEL).transpose()
print(df_profit)
# df_sharpe = pd.DataFrame(data=sharpe_storage, index=X_LABEL).transpose()
# print(df_sharpe)
# df_sqn = pd.DataFrame(data=sqn_storage, index=X_LABEL).transpose()
# print(df_sqn)

ax = plt.subplot(111)
ax = sns.heatmap(df_profit, annot=True, cmap='Greys')
# ay = plt.subplot(212)
# ay = sns.heatmap(df_sharpe, annot=True, cmap='Greys')
# az = plt.subplot(313)
# az = sns.heatmap(df_sqn, annot=True, cmap='Greys')
plt.show()




