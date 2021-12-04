import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
import sqlite3
import talib._ta_lib as ta
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
import joblib
from sklearn.metrics import roc_auc_score, confusion_matrix
import os

#set the period
start = datetime(2015, 1, 1)
end = datetime(2019, 12, 31)
d1 = start.strftime('%Y-%m-%d')
d2 = end.strftime('%Y-%m-%d')

#collect to historical data
db = sqlite3.connect('db3.db')
msft = pd.read_sql(
    con=db,
    sql=f'SELECT Open, High, Low, Close, Volume  FROM TSLA WHERE Date BETWEEN  "{d1}" and "{d2}"')
spy = pd.read_sql(
    con=db,
    sql=f'SELECT Open, High, Low, Close, Volume  FROM SPY WHERE Date BETWEEN  "{d1}" and "{d2}"')

#msft.index = pd.to_datetime(msft['Date'])
msft.columns = ['open','high','low','close','volume']
spy.columns = ['open','high','low','close','volume']
# indicator factor
# msft['SMA5'] = ta.SMA(msft['close'], timeperiod=5)
# msft['SMA30'] = ta.SMA(msft['close'], timeperiod=30)
# msft['MOM'] = ta.MOM(msft['close'])
msft['STOCK-K'], msft['STOCK-D'] = ta.STOCH(msft['high'],msft['low'],msft['close'])
msft['RSI'] = ta.RSI(msft['close'])
macd, macdsignal, macdhist = ta.MACD(msft['close'])
msft['MACD'] = macd
msft['SPY'] = spy.close
msft['LW'] = ta.WILLR(msft['high'],msft['low'],msft['close'])
msft['CCI'] = ta.CCI(msft['high'],msft['low'],msft['close'])
msft['ADOSC'] = ta.ADOSC(msft['high'],msft['low'],msft['close'],msft['volume'])
# msft['ptgChg'] = msft.close.pct_change(periods=1)
# msft['preClose'] = msft.close.shift(1)


#feature engineering & data cleaning
#msft['day_trend'] = np.where(msft.close.shift(-5) > msft.close ,1, -1)
# msft['signal'] = msft.ptgChg * 100
# msft['day_trend'] = np.where(msft.ptgChg > 0, 1, -1)
# msft['day_trend'] = np.where(msft.ptgChg > 0, 1, (np.where(msft.ptgChg < 0, -1, 0)))
# msft['day_trend'] = np.where(msft.close.shift(-1) > msft.close, 1, 0) #bad
msft['LC'] = msft.close.pct_change(periods=1)
msft['LS'] = msft.SPY.pct_change(periods=1)
msft['signal'] = (msft.LC - msft.LS) * 10
# msft['day_trend'] = np.where(msft.close > msft.close.shift(1), 1, 0) # 1: up/no change , 0: down
# msft['signal'] = np.where(msft.close.shift(-1) > msft.close,
#                              (np.where(msft.close.shift(-2) > msft.close,
#                                        (np.where(msft.close.shift(-3) > msft.close,
#                                                  (np.where(msft.close.shift(-4) > msft.close,1.0,0.8)),
#                                                  (np.where(msft.close.shift(-4) > msft.close,0.8,0.6)))),
#                                        (np.where(msft.close.shift(-3) > msft.close,
#                                                  (np.where(msft.close.shift(-4) > msft.close,0.6,0.4)),
#                                                  (np.where(msft.close.shift(-4) > msft.close,0.4,0.2)))))),
#                              (np.where(msft.close.shift(-2) > msft.close,
#                                        (np.where(msft.close.shift(-3) > msft.close,
#                                                  (np.where(msft.close.shift(-4) > msft.close,0.6,0.4)),
#                                                  (np.where(msft.close.shift(-4) > msft.close,0.4,0.2)))),
#                                        (np.where(msft.close.shift(-3) > msft.close,
#                                                  (np.where(msft.close.shift(-4) > msft.close,0.4,0.2)),
#                                                  (np.where(msft.close.shift(-4) > msft.close,0.2,0)))))))
# msft['signal'] = np.where(msft.day_trend == 1, np.where(msft.day_trend.shift(1) == 1, 0, 1), (
#                    np.where(msft.day_trend == 0, -1, 0)))
# 1 = buy , 0 = hold/no action, -1 = sell
msft.isnull().sum()
data = msft.dropna()

# 7:3
split_point = int(len(data)*0.75)
# train = data.iloc[:split_point, :].copy()
train = data
test = data.iloc[split_point:-1, :].copy()

train_X = train.drop(['SPY','LC','LS','signal'], axis = 1)
train_Y = train.signal

# X_test = test.drop(['SPY','LC','LS','signal'], axis = 1)
# Y_test = test.signal

model = RandomForestRegressor(max_features=6,n_estimators=100,warm_start=True,min_samples_leaf=10,random_state=50,n_jobs = -1)
model.fit(train_X, train_Y)

# prediction = model.predict(X_test)
# print(f"model score = {model.score(X_test, Y_test)}")
# print(prediction)
# print(test)
# plt.plot(prediction, label="predict")
# plt.plot(Y_test.reset_index(drop=True),label="Real")
# plt.legend(loc='upper left')
# plt.xlabel('Index')
# plt.ylabel('Price')
# plt.show()
# print(confusion_matrix(Y_test,prediction))
#AUC area
#print(f"auc = {roc_auc_score(Y_test, prediction)}")

# x = [1,5,10,50,100,200,500]
# y = [1,2,3,4,5,6,7,8,9,10,11]
# z = [1,3,5,7,10,25,50,100]
#
# for node_size in x :
#     model = RandomForestRegressor(max_features=6,n_estimators=node_size,random_state=5,
#                                    min_samples_leaf=10,n_jobs = -1)
#     model.fit(train_X, train_Y)
#     prediction = model.predict(X_test)
#     print(f"{node_size} & {model.score(X_test, Y_test)}")
#
# for node_size in y :
#     model = RandomForestRegressor(max_features=node_size,n_estimators=100,random_state=5,
#                                    min_samples_leaf=10,n_jobs = -1)
#     model.fit(train_X, train_Y)
#     prediction = model.predict(X_test)
#     print(f"{node_size} & {model.score(X_test, Y_test)}")
#
# for node_size in z :
#     model = RandomForestRegressor(max_features=6,n_estimators=100,random_state=5,
#                                    min_samples_leaf=node_size,n_jobs = -1)
#     model.fit(train_X, train_Y)
#     prediction = model.predict(X_test)
#     print(f"{node_size} & {model.score(X_test, Y_test)}")

# def load_symbol_list_by_volume(year, topn):
#     # get top n symbol that have highest average volume in the year
#     df = pd.read_csv('stock_volume_group_by_year.csv')
#     return df.sort_values(str(year), ascending=False)['symbol'].to_list()[:topn]
#
#
# train_list = load_symbol_list_by_volume(2019,1)
# #train_list = ['GOOGL','TSLA','AMD','INTC','NFLX']
# for stk in train_list:
#     model.n_estimators += 10
#     stock = pd.read_sql(
#         con=db,
#         sql=f'SELECT Open, High, Low, Close, Volume  FROM {stk} WHERE Date BETWEEN  "{d1}" and "{d2}"')
#
#     #msft.index = pd.to_datetime(msft['Date'])
#     stock.columns = ['open','high','low','close','volume']
#     # indicator factor
#     # stock['SMA10'] = ta.SMA(stock['close'], timeperiod=10)
#     # stock['SMA5'] = ta.SMA(stock['close'], timeperiod=5)
#     stock['MOM'] = ta.MOM(stock['close'])
#     stock['STOCK-K'], stock['STOCK-D'] = ta.STOCH(stock['high'],stock['low'],stock['close'])
#     stock['RSI'] = ta.RSI(stock['close'])
#     macd, macdsignal, macdhist = ta.MACD(stock['close'])
#     # stock['MACD'] = macd
#     stock['LW'] = ta.WILLR(stock['high'],stock['low'],stock['close'])
#     stock['CCI'] = ta.CCI(stock['high'],stock['low'],stock['close'])
#     stock['ADOSC'] = ta.ADOSC(stock['high'],stock['low'],stock['close'],stock['volume'])
#
#     #feature engineering & data cleaning
#     #stock['day_trend'] = np.where(stock.close.shift(-5) > stock.close, 1, -1)
#     stock['ptgChg'] = stock.close.pct_change()
#     # stock['day_trend'] = np.where(stock.ptgChg > 0.005, 1, (np.where(stock.ptgChg < -0.01, -1, 0)))
#     stock.isnull().sum()
#     train = stock.dropna()
#
#     train_X = train.drop(['STOCK-K','day_trend','ptgChg'], axis = 1)
#     train_y = train.day_trend
#
#     model.fit(train_X, train_y)
#
#     print(f"{stk} done")
# print("Finish")

for i in range(len(train_X.columns)):
    print('%.4f, %s'%(model.feature_importances_[i], train_X.columns[i]))

# plt.show()
filename = 'RFR_22-4-ER-64bit.pkl'
joblib.dump(model, filename)
