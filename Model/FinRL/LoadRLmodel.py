import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import sqlite3
import datetime
from sklearn import preprocessing
from finrl.config import config
from finrl.preprocessing.preprocessors import FeatureEngineer
from finrl.preprocessing.data import data_split
from finrl.env.env_stocktrading import StockTradingEnv
from finrl.model.models import DRLAgent
from finrl.trade.backtest import backtest_stats, get_baseline, backtest_plot
# Diable the warnings
import warnings

warnings.filterwarnings('ignore')
# set the period
start = '2013-01-01'
end = '2019-12-31'
# d1 = start.strftime('%Y-%m-%d')
# d2 = end.strftime('%Y-%m-%d')

# collect to historical
stock = 'MSFT'
db = sqlite3.connect("db3.db")
dataSet = pd.read_sql(
    con=db,
    sql=f'SELECT date, Open, High, Low, Close, Volume  FROM "{stock}" WHERE Date BETWEEN  "{start}" and "{end}"')
dataSet['tic'] = stock
dataSet.columns = ['date','open','high','low','close','volume','tic']

# dataSet = YahooDownloader(start_date='2014-01-01',
#                           end_date='2020-12-31',
#                           ticker_list=['AAPL']).fetch_data()

# Using Stockstat to build TA
# Currently need to include config.TECHNICAL_INDICATORS_LIST to run
# TODO: need to overcome this
tech_indicator_list = config.TECHNICAL_INDICATORS_LIST
tech_indicator_list = tech_indicator_list + ['volume_delta','kdjk','kdjd','wr_30','wr_10','cci_10','rsi_10','dma','trix']

fe = FeatureEngineer(use_technical_indicator=True, tech_indicator_list=tech_indicator_list, use_turbulence=True,
                     user_defined_feature=False)

processeDataSet = fe.preprocess_data(dataSet)

train = data_split(processeDataSet, start='2013-01-01', end='2018-12-31')
trade = data_split(processeDataSet, start='2019-01-01', end='2019-12-31')

# For Normalization
# feature_list = list(train.columns)
# feature_list.remove('date')
# feature_list.remove('tic')
# feature_list.remove('close')
# print(feature_list)

# data_normaliser = preprocessing.StandardScaler()
# train[feature_list] = data_normaliser.fit_transform(train[feature_list])
# trade[feature_list] = data_normaliser.transform(trade[feature_list])

stock_dimension = len(train.tic.unique())
state_space = 1 + 2 * stock_dimension + len(config.TECHNICAL_INDICATORS_LIST) * stock_dimension
# Currently need to include config.TECHNICAL_INDICATORS_LIST to run
# TODO: need to overcome this
env_kwargs = {
    "hmax": 100,
    "initial_amount": 100000,
    "buy_cost_pct": 0.0,
    "sell_cost_pct": 0.0008,
    "state_space": state_space,
    "stock_dim": stock_dimension,
    "tech_indicator_list": config.TECHNICAL_INDICATORS_LIST,
    "action_space": stock_dimension,
    "reward_scaling": 1e-4
}

e_train_gym = StockTradingEnv(df=train, **env_kwargs)
env_train, _ = e_train_gym.get_sb_env()

agent = DRLAgent(env=env_train)
#currently workable on PPO,SAC,A2C
A2C_PARAMS = {"n_steps": 5, "ent_coef": 0.005, "learning_rate": 0.0002}
# PPO_PARAMS = {
#     "n_steps": 2048,
#     "ent_coef": 0.005,
#     "learning_rate": 0.0001,
#     "batch_size": 128,
# }
# model_ppo = agent.get_model("ppo",model_kwargs = PPO_PARAMS)
# SAC_PARAMS = {
#     "batch_size": 128,
#     "buffer_size": 100000,
#     "learning_rate": 0.00003,
#     "learning_starts": 100,
#     "ent_coef": "auto_0.1",
# }
# model_sac = agent.get_model("sac",model_kwargs = SAC_PARAMS)
model_a2c = agent.get_model(model_name="a2c", model_kwargs=A2C_PARAMS)
#Input the filename of trained model
load_model = model_a2c.load('input the model filename')
e_trade_gym = StockTradingEnv(df=trade, **env_kwargs)
df_account_value, df_actions = DRLAgent.DRL_prediction(model=load_model, environment=e_trade_gym)
#You can get the action degree from -100 to 100 as trade signal
print(df_actions)
print("==============Get Backtest Results===========")
now = datetime.datetime.now().strftime('%Y%m%d-%Hh%M')

perf_stats_all = backtest_stats(account_value=df_account_value)
perf_stats_all = pd.DataFrame(perf_stats_all)
perf_stats_all.to_csv("./" + config.RESULTS_DIR + "/perf_stats_all_" + now + '.csv')
perf_stats_all.Annual_return
print(f"==============Compare to {stock} itself buy-and-hold===========")
# %matplotlib inline
backtest_plot(account_value=df_account_value,
             baseline_ticker = stock,
             baseline_start = '2019-01-01',
             baseline_end = '2019-12-31')