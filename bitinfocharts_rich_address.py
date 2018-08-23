import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup

class rich_scrapper(object):
    def __init__(self, url):
        self.headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
        self.url = url
        
    def get_table(self):
        res = requests.get(self.url, self.headers)
        df = pd.read_html(res.text)[2]
        return df
    
    @staticmethod
    def clean_table(df):
        df.columns = ['Block', 'Time (UTC)', 'Amount (BTC)', 'Balance (BTC)', 'Balance (USD)']
        df['year'] = df['Time (UTC)'].apply(lambda x:x.split('-')[0])
        df['month'] = df['Time (UTC)'].apply(lambda x:x.split('-')[1])
        df['date'] = df['Time (UTC)'].apply(lambda x:x[8:10])
        def iso(x):
            t = x.split(' ')
            return t[0]+'T'+t[1]+'Z'
        df['Time (UTC)'] = df['Time (UTC)'].apply(iso)
        def add(cols):
            year = cols[0]
            month = cols[1]
            date = cols[2]
            return int(str(year)+str(month)+str(date))
        df['timestamp'] = df[['year', 'month', 'date']].apply(add,axis=1)
        def btc(x):
            x = str(x)[:-4]
            x = x.replace(',','')
            if x.startswith('+'):
                return float(x[1:])
            else:
                return float(x)
        df['Amount (BTC)'] = df['Amount (BTC)'].apply(btc)
        df['Balance (BTC)'] = df['Balance (BTC)'].apply(btc)
        df['USD price'] = df['Balance (USD)'].apply(lambda x:x.split('@')[1])
        df['Balance (USD)'] = df['Balance (USD)'].apply(lambda x:x.split('@')[0])
        def usd(x):
            x = x.replace('$', '')
            x = x.replace(' ', '')
            x = x.replace(',', '')
            return float(x)
        df['USD price'] = df['USD price'].apply(usd)
        df['Balance (USD)'] = df['Balance (USD)'].apply(usd)
        df = df[['Block', 'Time (UTC)', 'year', 'month', 'date', 'timestamp', 'Amount (BTC)', 'Balance (BTC)', 'Balance (USD)', 'USD price']]
        return df
        
class address_scrapper(object):
    def __init__(self):
        self.headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
        self.url = 'https://bitinfocharts.com/top-100-richest-bitcoin-addresses.htmll'
    
    def get_list(self):
        res = requests.get(self.url, self.headers)
        table_list = pd.read_html(res.text)
        f = table_list[2].drop(['Unnamed: 0'],axis=1)
        s = table_list[3].drop(0,axis=1)
        s.columns = f.columns
        f100 = f.append(s)
        raw_rich_address = list(f100['Address'])
        def clean_address(x):
            if 'of' in x:
                return x.split(' ')[0]
            elif 'wallet:' in x:
                return x.split('wallet:')[0]
            else:
                return x
        rich_address = list(map(clean_address, raw_rich_address))
        return rich_address