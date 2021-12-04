import pandas as pd
from datetime import datetime
import talib._ta_lib as ta
import datetime as dt
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import sqlite3
import joblib
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import confusion_matrix, roc_curve, auc
import pickle

#set the period
start = datetime(2010, 1, 1)
end = datetime(2016, 12, 31)
d1 = start.strftime('%Y/%m/%d')
d2 = end.strftime('%Y/%m/%d')

#collect to historical data
db = sqlite3.connect('db3.db')
msft = pd.read_sql(
    con=db,
    sql=f'SELECT Open, High, Low, Close, Volume  FROM "AMD" WHERE Date BETWEEN  "{d1}" and "{d2}"')

#msft.index = pd.to_datetime(msft['Date'])

msft.columns = ['open','high','low','close','volume']
# indicator factor
msft['SMA10'] = ta.SMA(msft['close'], timeperiod=10)
msft['SMA30'] = ta.SMA(msft['close'], timeperiod=30)
msft['MOM'] = ta.MOM(msft['close'])
msft['STOCK-K'], msft['STOCK-D'] = ta.STOCH(msft['high'],msft['low'],msft['close'])
msft['RSI'] = ta.RSI(msft['close'])
macd, macdsignal, macdhist = ta.MACD(msft['close'])
msft['MACD'] = macd
msft['LW'] = ta.WILLR(msft['high'],msft['low'],msft['close'])
msft['CCI'] = ta.CCI(msft['high'],msft['low'],msft['close'])
msft['ADOSC'] = ta.ADOSC(msft['high'],msft['low'],msft['close'],msft['volume'])

msft['ptgChg'] = msft.close.pct_change()
msft['day_trend'] = np.where(msft.ptgChg > 0.005, 1,(np.where(msft.ptgChg < -0.01, -1, 0)))

msft.isnull().sum()
data = msft.dropna()

train_X = data.drop(['day_trend','ptgChg'], axis = 1)
train_Y = data.day_trend

#Split the data to 7:3 for train and test
split_point = int(len(data)*0.7)

train = data.iloc[:split_point, :].copy()
test = data.iloc[split_point:-1, :].copy()


train_X = train.drop('week_trend', axis = 1)
train_y = train.week_trend

test_X = test.drop('week_trend', axis = 1)
test_y = test.week_trend

model = DecisionTreeClassifier(max_depth = 14)
model.fit(train_X, train_Y)

prediction = model.predict(test_X)
print(prediction)

print(confusion_matrix(test_y, prediction))

print(model.score(test_X, test_y))

#ROC curve
false_positive_rate, true_positive_rate, thresholds = roc_curve(test_y, prediction)
#AUC area
print(auc(false_positive_rate, true_positive_rate))

# store the model
filename = 'Decision_Tree_model.pkl'
joblib.dump(model, filename)

# read the model
filename = 'Decision_Tree_model_001.sav'
model = pickle.load(open(filename, 'rb'))
