import logging
import datetime
import threading
import time
import pandas as pd

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

class AutoMLTrade:
    def __init__(self):
        self.alpaca = tradeapi.REST(Config.api_key, Config.api_secret, Config.base_url, api_version='v2')
        self.account = self.alpaca.get_account()
        self.stock = 'AAPL'
        self.past30dayData = pd.DataFrame()
        self.past30_15MinData = pd.DataFrame()
        self.processedData = pd.DataFrame()
        self.timeToClose = None
        self.signal = None


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
                for position in positions:
                    if(position.side == 'long'):
                        orderSide = 'sell'

                    qty = abs(int(float(position.qty)))
                    respSO = []
                    tSubmitOrder = threading.Thread(target=self.submitOrder(qty, position.symbol, orderSide, respSO))
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
        self.past30_15MinData = self.alpaca.get_barset(self.stock, '15Min', limit=40).df[self.stock]

    def dataProcess(self):
        self.processedData = self.past30_15MinData
        self.processedData['STOCK-K'], self.processedData['STOCK-D'] = ta.STOCH(self.processedData['high'], self.processedData['low'], self.processedData['close'])
        self.processedData['RSI'] = ta.RSI(self.processedData['close'])
        macd, macdsignal, macdhist = ta.MACD(self.processedData['close'])
        self.processedData['MACD'] = macd
        self.processedData['LW'] = ta.WILLR(self.processedData['high'], self.processedData['low'], self.processedData['close'])
        self.processedData['CCI'] = ta.CCI(self.processedData['high'], self.processedData['low'], self.processedData['close'])
        self.processedData['ADOSC'] = ta.ADOSC(self.processedData['high'], self.processedData['low'], self.processedData['close'], self.processedData['volume'])

    def getPredictSignal(self):
        self.dataProcess()
        self.signal = stored_model.predict(self.processedData.tail(1))

    def printPos(self):
        positions = self.alpaca.list_positions()
        print(positions[0])

    def tradeBegin(self):
        print(self.signal)
        positions = self.alpaca.list_positions()
        print(positions)
        action = None
        if self.signal >= 0.02:
            action = 'buy'
        elif self.signal < -0.02:
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