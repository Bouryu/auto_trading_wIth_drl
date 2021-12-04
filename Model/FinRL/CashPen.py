#!/usr/bin/env python
# coding: utf-8

# In[2]:


import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
# matplotlib.use('Agg')
import datetime

get_ipython().run_line_magic('matplotlib', 'inline')
from finrl.config import config
from finrl.marketdata.yahoodownloader import YahooDownloader
from finrl.preprocessing.preprocessors import FeatureEngineer
from finrl.preprocessing.data import data_split
from finrl.env.env_stocktrading_cashpenalty import StockTradingEnvCashpenalty
from finrl.model.models import DRLAgent
from finrl.trade.backtest import backtest_plot, backtest_stats

from pprint import pprint


# In[ ]:


config.DOW_30_TICKER


# In[20]:


df = YahooDownloader(start_date = '2014-01-01',
                     end_date = '2020-01-01',
                     ticker_list = ['AAPL', 'MSFT', 'JPM']).fetch_data()


# In[21]:


fe = FeatureEngineer(
                    use_technical_indicator=True,
                    tech_indicator_list = config.TECHNICAL_INDICATORS_LIST,
                    use_turbulence=False,
                    user_defined_feature = False)

processed = fe.preprocess_data(df)


# In[22]:


processed['log_volume'] = np.log(processed.volume*processed.close)
processed['change'] = (processed.close-processed.open)/processed.close
processed['daily_variance'] = (processed.high-processed.low)/processed.close
processed.head()


# In[7]:


processed.head()


# In[40]:



train = data_split(processed, '2009-01-01','2016-01-01')
trade = data_split(processed, '2019-01-01','2020-01-01')
print(len(train))
print(len(trade))


# In[41]:


information_cols = ['daily_variance', 'change', 'log_volume', 'close','day', 
                    'macd', 'rsi_30', 'cci_30', 'dx_30']

# e_train_gym = StockTradingEnvCashpenalty(df = train,initial_amount = 1e6,hmax = 5000, 
#                                 turbulence_threshold = None, 
#                                 currency='$',
#                                 buy_cost_pct=3e-3,
#                                 sell_cost_pct=3e-3,
#                                 cash_penalty_proportion=0.2,
#                                 cache_indicator_data=True,
#                                 daily_information_cols = information_cols, 
#                                 print_verbosity = 500, 
#                                 random_start = True)

e_trade_gym = StockTradingEnvCashpenalty(df = trade,initial_amount = 1e6,hmax = 5000, 
                                turbulence_threshold = None, 
                                currency='$',
                                buy_cost_pct=3e-3,
                                sell_cost_pct=3e-3,
                                cash_penalty_proportion=0.2,
                                cache_indicator_data=True,
                                daily_information_cols = information_cols, 
                                print_verbosity = 500, 
                                random_start = False)


# In[26]:


import multiprocessing

n_cores = multiprocessing.cpu_count() - 2

print(f"using {n_cores} cores")

#this is our training env. It allows multiprocessing
env_train, _ = e_train_gym.get_sb_env()
# env_train, _ = e_train_gym.get_sb_env()

#this is our observation environment. It allows full diagnostics
env_trade, _ = e_trade_gym.get_sb_env()


# In[27]:


agent = DRLAgent(env = env_train)

# from torch.nn import Softsign, ReLU
ppo_params ={'n_steps': 256, 
             'ent_coef': 0.0, 
             'learning_rate': 0.000005, 
             'batch_size': 1024, 
            'gamma': 0.99}

policy_kwargs = {
#     "activation_fn": ReLU,
    "net_arch": [1024 for _ in range(10)], 
#     "squash_output": True
}

model = agent.get_model("ppo",  
                        model_kwargs = ppo_params, 
                        policy_kwargs = policy_kwargs, verbose = 0)


# In[29]:


model.learn(total_timesteps = 50000, 
            eval_env = env_trade, 
            eval_freq = 1000,
            log_interval = 1, 
            tb_log_name = 'env_cashpenalty_highlr',
            n_eval_episodes = 1)


# In[30]:



model.save("different.model")


# In[34]:


e_trade_gym.hmax = 500


# In[42]:


df_account_value, df_actions = DRLAgent.DRL_prediction(model=model,environment = e_trade_gym)


# In[43]:



df_account_value.head(50)


# In[44]:


print("==============Get Backtest Results===========")
perf_stats_all = backtest_stats(account_value=df_account_value, value_col_name = 'total_assets')


# In[45]:


print("==============Compare to DJIA===========")
get_ipython().run_line_magic('matplotlib', 'inline')
# S&P 500: ^GSPC
# Dow Jones Index: ^DJI
# NASDAQ 100: ^NDX
backtest_plot(df_account_value, 
             baseline_ticker = '^DJI', 
             baseline_start = '2019-01-01',
             baseline_end = '2020-01-01', value_col_name = 'total_assets')


# In[ ]:




