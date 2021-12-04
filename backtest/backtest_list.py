import pandas as pd
from datetime import datetime
import backtrader as bt
import Strategy
from Model import DatabaseModel
import matplotlib.pyplot as plt
import seaborn as sns

#config
START_YEAR = 2010
END_YEAR = 2019
SYMBOL_TEST_AMOUNT = 1000
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

for strat in STRATEGY_LIST:
    f = open('result_tsv/' + strat.label + '.tsv', 'w')
    f.close()


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

        f = open('result_tsv/' + strat.label + '.tsv', 'a')
        f.write(str(symbol) + '\t' + str(net_profit) + '\t' + str(sharpe_ratio['sharperatio']) + '\t' + str(sqn['sqn']) + '\n')
        f.close()

# Add analysis stuff
ANALYSIS_RANGE = [
    'B1:B' + str(SYMBOL_TEST_AMOUNT),
    'C1:C' + str(SYMBOL_TEST_AMOUNT),
    'D1:D' + str(SYMBOL_TEST_AMOUNT)
]

ANALYSIS_FUNCTION = [
    '_AVG\t=AVERAGE({0})\t=AVERAGE({1})\t=AVERAGE({2})'.format(ANALYSIS_RANGE[0],ANALYSIS_RANGE[1],ANALYSIS_RANGE[2]),
    '_SD\t=STDEV.S({0})\t=STDEV.S({1})\t=STDEV.S({2})'.format(ANALYSIS_RANGE[0],ANALYSIS_RANGE[1],ANALYSIS_RANGE[2]),
    '_VAR\t=VAR.S({0})\t=VAR.S({1})\t=VAR.S({2})'.format(ANALYSIS_RANGE[0],ANALYSIS_RANGE[1],ANALYSIS_RANGE[2]),
    '_MIN\t=MIN({0})\t=MIN({1})\t=MIN({2})'.format(ANALYSIS_RANGE[0],ANALYSIS_RANGE[1],ANALYSIS_RANGE[2]),
    '_MAX\t=MAX({0})\t=MAX({1})\t=MAX({2})'.format(ANALYSIS_RANGE[0],ANALYSIS_RANGE[1],ANALYSIS_RANGE[2]),
    '_LOWERQ\t=PERCENTILE.INC({0},0.25)\t=PERCENTILE.INC({1},0.25)\t=PERCENTILE.INC({2},0.25)'.format(ANALYSIS_RANGE[0],ANALYSIS_RANGE[1],ANALYSIS_RANGE[2]),
    '_MEDIAN\t=PERCENTILE.INC({0},0.5)\t=PERCENTILE.INC({1},0.5)\t=PERCENTILE.INC({2},0.5)'.format(ANALYSIS_RANGE[0],ANALYSIS_RANGE[1],ANALYSIS_RANGE[2]),
    '_UPPERQ\t=PERCENTILE.INC({0},0.75)\t=PERCENTILE.INC({1},0.75)\t=PERCENTILE.INC({2},0.75)'.format(ANALYSIS_RANGE[0],ANALYSIS_RANGE[1],ANALYSIS_RANGE[2]),
    '_10PTILE\t=PERCENTILE.INC({0},0.1)\t=PERCENTILE.INC({1},0.1)\t=PERCENTILE.INC({2},0.1)'.format(ANALYSIS_RANGE[0],ANALYSIS_RANGE[1],ANALYSIS_RANGE[2]),
    '_20PTILE\t=PERCENTILE.INC({0},0.2)\t=PERCENTILE.INC({1},0.2)\t=PERCENTILE.INC({2},0.2)'.format(ANALYSIS_RANGE[0],ANALYSIS_RANGE[1],ANALYSIS_RANGE[2]),
    '_30PTILE\t=PERCENTILE.INC({0},0.3)\t=PERCENTILE.INC({1},0.3)\t=PERCENTILE.INC({2},0.3)'.format(ANALYSIS_RANGE[0],ANALYSIS_RANGE[1],ANALYSIS_RANGE[2]),
    '_40PTILE\t=PERCENTILE.INC({0},0.4)\t=PERCENTILE.INC({1},0.4)\t=PERCENTILE.INC({2},0.4)'.format(ANALYSIS_RANGE[0],ANALYSIS_RANGE[1],ANALYSIS_RANGE[2]),
    '_50PTILE\t=PERCENTILE.INC({0},0.5)\t=PERCENTILE.INC({1},0.5)\t=PERCENTILE.INC({2},0.5)'.format(ANALYSIS_RANGE[0],ANALYSIS_RANGE[1],ANALYSIS_RANGE[2]),
    '_60PTILE\t=PERCENTILE.INC({0},0.6)\t=PERCENTILE.INC({1},0.6)\t=PERCENTILE.INC({2},0.6)'.format(ANALYSIS_RANGE[0],ANALYSIS_RANGE[1],ANALYSIS_RANGE[2]),
    '_70PTILE\t=PERCENTILE.INC({0},0.7)\t=PERCENTILE.INC({1},0.7)\t=PERCENTILE.INC({2},0.7)'.format(ANALYSIS_RANGE[0],ANALYSIS_RANGE[1],ANALYSIS_RANGE[2]),
    '_80PTILE\t=PERCENTILE.INC({0},0.8)\t=PERCENTILE.INC({1},0.8)\t=PERCENTILE.INC({2},0.8)'.format(ANALYSIS_RANGE[0],ANALYSIS_RANGE[1],ANALYSIS_RANGE[2]),
    '_90PTILE\t=PERCENTILE.INC({0},0.9)\t=PERCENTILE.INC({1},0.9)\t=PERCENTILE.INC({2},0.9)'.format(ANALYSIS_RANGE[0],ANALYSIS_RANGE[1],ANALYSIS_RANGE[2]),

]

for strat in STRATEGY_LIST:
    f = open('result_tsv/' + strat.label + '.tsv', 'a')
    f.write('\n')
    for fun in ANALYSIS_FUNCTION:
        f.write(fun + '\n')
    f.write('\n')
    f.close()

