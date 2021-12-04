import urllib3
import csv

class SymbolCollection:
    # configurate url required here
    NASDAQ_LISTED_URL = 'http://ftp.nasdaqtrader.com/dynamic/SymDir/nasdaqtraded.txt'

    def __init__(self):
        self.http = http = urllib3.PoolManager()

    def nasdaq(self):
        result = []
        # return list of nasdaq-listed stock
        response = self.http.request('GET', self.NASDAQ_LISTED_URL)
        csv_file = open('nasdaq_listed.csv', 'wb')
        csv_file.write(response.data)
        csv_file.close()
        with open('nasdaq_listed.csv', 'r') as csvfile:
            reader = csv.reader(csvfile, delimiter='|')
            for row in reader:
                result.append(row[1])

        return result



