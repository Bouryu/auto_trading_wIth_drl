import yfinance
from datetime import date
from Model.DatabaseModel import StockDB

class YahooFinance:

    def __init__(self, symbol):
        self.symbol = symbol.upper()
        self.ticker = yfinance.Ticker(self.symbol)

        self.quarter_financial = self.get_quarter_financial_data()
        self.financial = self.get_financial_data()
        self.quarter_balance_sheet = self.get_quarter_balance_sheet()
        self.balance_sheet = self.get_balance_sheet()
        self.quarter_cashflow = self.get_quarter_cashflow()
        self.cashflow = self.get_cashflow()
        self.quarter_earning = self.get_quarter_earning()
        self.earning = self.get_earning()
        self.sustainability = self.get_sustainability()

    def get_historical_data_max(self):
        return self.ticker.history(period="max")

    def get_historical_data_update(self):
        db = StockDB()
        start = db.get_latest_date(self.symbol)
        end = date.today().strftime('%Y-%m-%d')
        return self.ticker.history(start=start, end=end)



    def get_quarter_financial_data(self):
        return self.ticker.quarterly_financials

    def get_financial_data(self):
        return self.ticker.financials

    def get_quarter_balance_sheet(self):
        return self.ticker.quarterly_balance_sheet

    def get_balance_sheet(self):
        return self.ticker.balance_sheet

    def get_quarter_cashflow(self):
        return self.ticker.quarterly_cashflow

    def get_cashflow(self):
        return self.ticker.cashflow

    def get_quarter_earning(self):
        return self.ticker.quarterly_earnings

    def get_earning(self):
        return self.ticker.earnings

    def get_sustainability(self):
        return self.ticker.sustainability

