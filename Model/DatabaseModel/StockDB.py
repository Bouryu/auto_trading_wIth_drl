import sqlite3
import datetime
import pandas as pd

class StockDB:
    instance = None
    # database model for storing all symbol data and historical market data
    # with singleton pattern
    def __new__(cls, *args, **kwargs):
        if cls.instance is None:
            cls.instance = super().__new__(StockDB)
            return cls.instance
        return cls.instance

    def __init__(self, db_name='db3.db'):
        self.name = db_name
        # connect takes url, dbname, user-id, password
        self.conn = self.connect()
        self.cursor = self.conn.cursor()

    def connect(self):
        try:
            return sqlite3.connect(self.name)
        except sqlite3.Error as e:
            pass

    def __del__(self):
        self.cursor.close()
        self.conn.close()

    def create_symbol_table(self, symbol):
        conn = self.conn
        c = self.cursor
        c.execute('''CREATE TABLE IF NOT EXISTS ''' + symbol + ''' (
                                        "Date"	TEXT,
                                        "Open"	REAL,
                                        "High"	REAL,
                                        "Low"	REAL,
                                        "Close"	REAL,
                                        "Volume"	REAL,
                                        PRIMARY KEY("Date")
                                     )''')
        print('table ' + symbol + ' created')
        conn.commit()

    def insert_historical_data(self, symbol, dataframe):
        # param dataframe: type panda.dataframe from get_historical_data()
        conn = self.conn
        c = self.cursor
        for date, row in dataframe.iterrows():
            c.execute('''INSERT OR IGNORE INTO ''' + symbol + ''' (Date, Open, High, Low, Close, Volume) VALUES (?,?,?,?,?,?)'''
                      , (date.strftime('%Y-%m-%d'), row['Open'], row['High'], row['Low'], row['Close'], row['Volume']))
        conn.commit()

    def get_historical_data(self, symbol):
        conn = self.conn
        c = self.cursor
        c.execute('''SELECT Date, Open, High, Low, Close, Volume FROM ''' + symbol + ''' ORDER BY Date''')
        result = []
        for row in c.fetchall():
            temp = {}
            temp['Date'] = row[0]
            temp['Open'] = row[1]
            temp['High'] = row[2]
            temp['Low'] = row[3]
            temp['Close'] = row[4]
            temp['Volume'] = row[5]
            result.append(temp)

        return result

    def get_latest_date(self, symbol):
        conn = self.conn
        c = self.cursor
        c.execute('''SELECT DATE(MAX(Date),'+1 day') FROM ''' + symbol)
        return c.fetchone()[0]

    def get_symbol_list(self):
        conn = self.conn
        c = self.cursor
        c.execute(
            '''SELECT 
                name
            FROM 
                sqlite_master 
            WHERE 
                type ='table' AND 
                name NOT LIKE 'sqlite_%';'''
                     )
        result = []
        for row in c.fetchall():
            result.append(row[0])

        return result

    def get_stock_avg_volume_group_by_year(self):
        conn = self.conn
        c = self.cursor
        f = open('stock_volume_group_by_year.csv', 'w')
        header = 'symbol'
        current_year = datetime.datetime.now().year
        for y in range(2000,current_year+1):
            header += ','+ str(y)
        f.write(header + '\n')

        symbol_list = self.get_symbol_list()
        for symbol in symbol_list:
            line = symbol
            c.execute('''
            SELECT 
                strftime('%Y', Date) as `year`,
                AVG(Volume)
            FROM
                '''+ symbol + '''
            WHERE
                strftime('%Y', Date) >= '2000'
            GROUP BY
                `year`
            ''')
            result = {}
            for row in c.fetchall():
                result[row[0]] = row[1]

            for y in range(2000, current_year + 1):
                if str(y) in result:
                    line += ',' + str(result[str(y)])
                else:
                    line += ',0'
            f.write(line + '\n')
        f.close()

    def get_stock_historical_in_panda_dataframe(self, symbol, start, end):
        #dateformat: YYYY-mm-DD
        return pd.read_sql(
            con=self.conn,
            sql=f'SELECT Date, Open, High, Low, Close, Volume  FROM "{symbol}" WHERE Date BETWEEN  "{start}" and "{end}" '
        )
