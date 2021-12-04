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
start = '2014-01-01'
end = '2020-12-31'
# d1 = start.strftime('%Y-%m-%d')
# d2 = end.strftime('%Y-%m-%d')

# collect to historical
stock = 'AAPL'
db = sqlite3.connect("db3.db")
dataSet = pd.read_sql(
    con=db,
    sql=f'SELECT date, Open, High, Low, Close, Volume  FROM "{stock}" WHERE Date BETWEEN  "{start}" and "{end}"')
dataSet['tic'] = 'TSLA'
dataSet.columns = ['date','open','high','low','close','volume','tic']

# dataSet = YahooDownloader(start_date='2014-01-01',
#                           end_date='2020-12-31',
#                           ticker_list=['AAPL']).fetch_data()

print(dataSet.head())
tech_indicator_list = config.TECHNICAL_INDICATORS_LIST
tech_indicator_list = tech_indicator_list + ['kdjk','kdjd','kdjj', 'open_2_sma', 'boll', 'close_10.0_le_5_c', 'wr_10',
                                             'dma','rsi_6','trix']

fe = FeatureEngineer(use_technical_indicator=True, tech_indicator_list=tech_indicator_list, use_turbulence=True,
                     user_defined_feature=False)

processeDataSet = fe.preprocess_data(dataSet)

print(processeDataSet.head())

train = data_split(processeDataSet, start='2014-01-01', end='2019-12-31')
trade = data_split(processeDataSet, start='2020-01-01', end='2020-12-31')

feature_list = list(train.columns)
feature_list.remove('date')
feature_list.remove('tic')
feature_list.remove('close')
print(feature_list)

data_normaliser = preprocessing.StandardScaler()
train[feature_list] = data_normaliser.fit_transform(train[feature_list])
trade[feature_list] = data_normaliser.transform(trade[feature_list])

stock_dimension = len(train.tic.unique())
state_space = 1 + 2 * stock_dimension + len(config.TECHNICAL_INDICATORS_LIST) * stock_dimension
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

# A2C_PARAMS = {"n_steps": 5, "ent_coef": 0.005, "learning_rate": 0.0002}
# model_a2c = agent.get_model(model_name="a2c", model_kwargs=A2C_PARAMS)
# trained_a2c = agent.train_model(model=model_a2c,
#                                 tb_log_name='a2c',
#                                 total_timesteps=50000)
# DDPG_PARAMS = {"batch_size": 64, "buffer_size": 500000, "learning_rate": 0.0001}
# model_ddpg = agent.get_model("ddpg",model_kwargs = DDPG_PARAMS)
# trained_ddpg = agent.train_model(model=model_ddpg,
#                              tb_log_name='ddpg',
#                              total_timesteps=30000)

PPO_PARAMS = {
    "n_steps": 2048,
    "ent_coef": 0.005,
    "learning_rate": 0.0001,
    "batch_size": 128,
}
model_ppo = agent.get_model("ppo",model_kwargs = PPO_PARAMS)
trained_ppo = agent.train_model(model=model_ppo,
                             tb_log_name='ppo',
                             total_timesteps=80000)

# TD3_PARAMS = {"batch_size": 128,
#               "buffer_size": 1000000,
#               "learning_rate": 0.0003}
# model_td3 = agent.get_model("td3",model_kwargs = TD3_PARAMS)
# trained_td3 = agent.train_model(model=model_td3,
#                              tb_log_name='td3',
#                              total_timesteps=30000)
#
# SAC_PARAMS = {
#     "batch_size": 128,
#     "buffer_size": 100000,
#     "learning_rate": 0.00003,
#     "learning_starts": 100,
#     "ent_coef": "auto_0.1",
# }
# model_sac = agent.get_model("sac",model_kwargs = SAC_PARAMS)
# trained_sac = agent.train_model(model=model_sac,
#                                 tb_log_name='sac',
#                                 total_timesteps=30000)

# trade = data_split(processeDataSet,start='2020-01-01',end='2020-12-31')
e_trade_gym = StockTradingEnv(df=trade, **env_kwargs)
# env_trade, obs_trade = e_trade_gym.get_sb_env()

df_account_value, df_actions = DRLAgent.DRL_prediction(model=trained_ppo, environment=e_trade_gym)

print("==============Get Backtest Results===========")
now = datetime.datetime.now().strftime('%Y%m%d-%Hh%M')

perf_stats_all = backtest_stats(account_value=df_account_value)
perf_stats_all = pd.DataFrame(perf_stats_all)
perf_stats_all.to_csv("./" + config.RESULTS_DIR + "/perf_stats_all_" + now + '.csv')
