import logging
import datetime
import threading
import time
import pandas as pd

from finrl.config import config
from finrl.preprocessing.preprocessors import FeatureEngineer
from finrl.preprocessing.data import data_split
from finrl.env.env_stocktrading import StockTradingEnv
from finrl.model.models import DRLAgent
import joblib
import talib._ta_lib as ta
import alpaca_trade_api as tradeapi
from Model.AlpacaAPI import Config

# init WebSocket
conn = tradeapi.stream2.StreamConn(
    Config.api_key,
    Config.api_secret,
    base_url=Config.base_url,
    data_url=Config.data_url,
    data_stream='alpacadatav1',
)
filename = 'RFR_22-4-ER-64bit.pkl'
stored_model = joblib.load(filename)

class AutoDRLTrade:
    def __init__(self):
        self.alpaca = tradeapi.REST(Config.api_key, Config.api_secret, Config.base_url, api_version='v2')
        self.account = self.alpaca.get_account()
        self.stock = 'AAPL'
        self.todayCash =
        self.past60_15MinData = pd.DataFrame()
        self.processedData = pd.DataFrame()
        self.tech_indicator_list = None
        self.timeToClose = None
        self.signal = None
        self.IncrementTimeUnit = 11


    def run(self):
        orders = self.alpaca.list_orders(status="open")
        for order in orders:
            self.alpaca.cancel_order(order.id)

        # Wait for market to open.
        print("Waiting for market to open...")
        tAMO = threading.Thread(target=self.awaitMarketOpen)
        tAMO.start()
        tAMO.join()
        print("Market opened.")

        while True:
            clock = self.alpaca.get_clock()
            closingTime = clock.next_close.replace(tzinfo=datetime.timezone.utc).timestamp()
            currTime = clock.timestamp.replace(tzinfo=datetime.timezone.utc).timestamp()
            self.timeToClose = closingTime - currTime

            if (self.timeToClose < (60 * 15)):
                # Close all positions when 15 minutes til market close.
                print("Market closing soon.  Closing positions.")

                positions = self.alpaca.list_positions()
                if positions:
                    for position in positions:
                        if position.side == 'long':
                            orderSide = 'sell'
                        qty = abs(int(float(position.qty)))
                        tSubmitOrder = threading.Thread(
                            target=self.alpaca.submit_order(
                                qty=qty,
                                symbol=position.symbol,
                                side=orderSide,
                                type='market',
                                time_in_force='gtc'
                            )
                        )
                        tSubmitOrder.start()
                        tSubmitOrder.join()

                print("Sleeping until market close (15 minutes).")
                time.sleep(60 * 15)

            else:
                self.getMinData()
                self.getPredictSignal()
                self.tradeBegin()
                time.sleep(60*15)


    def awaitMarketOpen(self):
        isOpen = self.alpaca.get_clock().is_open
        while (not isOpen):
            clock = self.alpaca.get_clock()
            openingTime = clock.next_open.replace(tzinfo=datetime.timezone.utc).timestamp()
            currTime = clock.timestamp.replace(tzinfo=datetime.timezone.utc).timestamp()
            timeToOpen = int((openingTime - currTime) / 60)
            print(str(timeToOpen) + " minutes til market open.")
            time.sleep(60)
            isOpen = self.alpaca.get_clock().is_open

    def getMonthData(self):
        self.past30dayData = self.alpaca.get_barset(self.stock, 'day', limit=30).df[self.stock]

    def getMinData(self):
        self.past60_15MinData = self.alpaca.get_barset(self.stock, '15Min', limit=self.IncrementTimeUnit).df[self.stock].reset_index()
        self.past60_15MinData = self.past60_15MinData.rename(columns={"time": "date"})
        self.past60_15MinData['tic'] = self.stock
        self.IncrementTimeUnit = self.IncrementTimeUnit + 1

    def dataProcess(self):
        self.tech_indicator_list = ["macd","boll_ub","boll_lb","rsi_30","cci_30", "dx_30","close_30_sma",'kdjk','kdjd','kdjj', 'open_2_sma', 'boll','wr_30','wr_10','dma','rsi_14']

        fe = FeatureEngineer(use_technical_indicator=True, tech_indicator_list=self.tech_indicator_list, use_turbulence=False,
                             user_defined_feature=False)

        self.processedData = fe.preprocess_data(self.past60_15MinData)
        feature_list = list(self.processedData.columns)
        feature_list.remove('date')
        feature_list.remove('tic')
        feature_list.remove('close')
        print(feature_list)

        data_normaliser = self.processedData.StandardScaler()
        self.processedData[feature_list] = data_normaliser.fit_transform(self.processedData[feature_list])



    def getPredictSignal(self):
        self.dataProcess()
        stock_dimension = len(self.processedData.tic.unique())
        state_space = 1 + 2 * stock_dimension + len(self.tech_indicator_list) * stock_dimension
        env_kwargs = {
            "hmax": 100,
            "initial_amount": 100000,
            "buy_cost_pct": 0.0,
            "sell_cost_pct": 0.0008,
            "state_space": state_space,
            "stock_dim": stock_dimension,
            "tech_indicator_list": self.tech_indicator_list,
            "action_space": stock_dimension,
            "reward_scaling": 1e-4
        }

        e_trade_gym = StockTradingEnv(df=self.processedData, **env_kwargs)
        env_trade, _ = e_trade_gym.get_sb_env()

        agent = DRLAgent(env=env_trade)
        PPO_PARAMS = {
            "n_steps": 2048,
            "ent_coef": 0.005,
            "learning_rate": 0.0001,
            "batch_size": 128,
        }
        model_ppo = agent.get_model(model_name="ppo", model_kwargs=PPO_PARAMS)
        # Input the filename of trained model
        load_model = model_ppo.load('Model/FinRL/trained_models/2009-2019_MSFT_2021_4_23_ppo.model')
        df_account_value, df_actions = DRLAgent.DRL_prediction(model=load_model, environment=e_trade_gym)
        self.signal = int(df_actions.tail(1).actions)


    def printPos(self):
        positions = self.alpaca.list_positions()
        print(positions[0])

    def tradeBegin(self):
        print(f'The signal is {self.signal}')
        positions = self.alpaca.list_positions()
        print(positions)
        action = None
        if self.signal >= 20:
            action = 'buy'
        elif self.signal <= -20:
            action = 'sell'
        if not positions:
            print('Currently Not in Position')
            print(f'Predict Action: {action}')
            if action == 'buy':
                currPrice = self.alpaca.get_last_quote(symbol=self.stock).askprice
                qty = int(float(self.account.cash) / currPrice)
                self.alpaca.submit_order(
                    symbol=self.stock,
                    qty=qty,
                    side=action,
                    type='market',
                    time_in_force='gtc'
                )
                print(f'Bought {qty} Stock')
        else:
            print('Already in market')
            if action == 'sell':
                print('Stock Sold')
                self.alpaca.submit_order(
                    symbol=self.stock,
                    qty=positions[0].qty,
                    side=action,
                    time_in_force='gtc'
                )