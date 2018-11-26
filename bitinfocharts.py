import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
from pd_ela import *
import talib

head = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}

def write(mesg, path='/Users/gary/bitscrappinglog', mode='a'):
    with open(path, mode) as f:
        f.write(mesg+'\n')
        
class address_scrapper(object):
    def __init__(self):
        self.headers = head
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
    
class data_scrapper(object):
    def __init__(self, url):
        self.headers = head
        self.url = url
        
    def get_table(self):
        res = requests.get(self.url, self.headers)
        df = pd.read_html(res.text)[2]
        df = df[df['Balance, USD'].isnull() != True]
        return df
    
    @staticmethod
    def clean_table(df):
        df.columns = ['Block', 'Time (UTC)', 'Amount (BTC)', 'Balance (BTC)', 'Balance (USD)']
        df['Block'] = df['Block'].apply(lambda x:int(x[:6]))
        df['year'] = df['Time (UTC)'].apply(lambda x:x.split('-')[0])
        df['month'] = df['Time (UTC)'].apply(lambda x:x.split('-')[1])
        df['date'] = df['Time (UTC)'].apply(lambda x:x[8:10])
        df['time_numeric'] = df['Time (UTC)'].apply(lambda x:time.mktime(time.strptime(x, "%Y-%m-%d %H:%M:%S UTC")))
        
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
        df['year'] = df['year'].apply(lambda x:int(x))
        df['month'] = df['month'].apply(lambda x:int(x))
        df['date'] = df['date'].apply(lambda x:int(x))
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
        df = df[df['year'] > 2010]
        df = df[['Block', 'Time (UTC)', 'year', 'month', 'date', 'timestamp', 'Amount (BTC)', 'Balance (BTC)', 'Balance (USD)', 'USD price', 'time_numeric']]
        return df
    
def tech(df, rsi_range1=6, rsi_range2=9, rsi_range3=15, kd_range=9):
    df_day = df.groupby(['timestamp'])
    volume_day = np.array(df_day.sum()['Amount (BTC)'])
    price_day = np.array(df_day.mean()['USD price'])
    raw_date = list(df_day.groups.keys())
    
    def iso_format(x):
        t = str(x)
        return t[:4]+'-'+t[4:6]+'-'+t[6:]+'T00:00:00Z'
    
    es_date = list(map(iso_format, list(df_day.groups.keys())))
    
    rsi1 = talib.RSI(volume_day, timeperiod=rsi_range1)
    rsi2 = talib.RSI(volume_day, timeperiod=rsi_range2)
    rsi3 = talib.RSI(volume_day, timeperiod=rsi_range3)
    
    k, d = talib.STOCH(high=volume_day, 
                low=volume_day, 
                close=volume_day,
                fastk_period=kd_range,
                slowk_period=3,
                slowd_period=3
    )
    
    df_technical = pd.DataFrame(data = {'Time (UTC)':es_date, 'timestamp':raw_date, 'Amount (BTC)':volume_day, 
                                        'USD price':price_day, 
                                        'RSI_{}'.format(rsi_range1):rsi1, 
                                        'RSI_{}'.format(rsi_range2):rsi2, 
                                        'RSI_{}'.format(rsi_range3):rsi3, 
                                        'K_{}'.format(kd_range):k, 'D_{}'.format(kd_range):d
                                 })
    return df_technical

def full_table():
    all_list = []
    a = address_scrapper()
    rich_address = a.get_list()
    base = 'https://bitinfocharts.com/bitcoin/address/{}-full'
    for i in rich_address:
        if rich_address.index(i) == 30:
            write('rank {} address {}'.format(rich_address.index(i), i))
        try:
            t = data_scrapper(base.format(i))
            df = t.clean_table(t.get_table())
            df.drop('time_numeric', axis=1, inplace=True)
            df['address'] = i
            df['rank'] = rich_address.index(i) + 1
            all_list.append(df)
        except IndexError:
            write('IndexError')
    df_sum = pd.concat(all_list).sort_values(by='Block', ascending=False)
    df_sum = df_sum[df_sum['year'] > 2014]
    return df_sum

def filtered_table():
    write('connects with elasticsearch @ {}'.format(time.asctime(time.localtime())))
    last = get_last()
    write('over @ {}'.format(time.asctime(time.localtime())))
    all_list = []
    a = address_scrapper()
    rich_address = a.get_list()
    base = 'https://bitinfocharts.com/bitcoin/address/{}-full'
    for i in rich_address:
        if rich_address.index(i) == 30:
            write('rank {} address {}'.format(rich_address.index(i), i))
        try:
            t = data_scrapper(base.format(i))
            df = t.clean_table(t.get_table())
            df = df[df['time_numeric'] > last]
            df.drop('time_numeric', axis=1, inplace=True)
            df['address'] = i
            df['rank'] = rich_address.index(i) + 1
            all_list.append(df)
        except IndexError:
            write('IndexError')
    df_sum = pd.concat(all_list).sort_values(by='Block', ascending=False)
    df_sum = df_sum[df_sum['year'] > 2014]
    return df_sum

if __name__ == "__main__":
    write('\nprogram starts @ {}'.format(time.asctime(time.localtime())))
    df_filtered = filtered_table()
    if len(df_filtered) > 0:
        write('detect {} new docs @ {}'.format(len(df_filtered), time.asctime(time.localtime())))
        esbulk('btc_top100_index', 't', df_filtered)
    else:
        write('none updated data')
    write('program ceased temporarily @ {}'.format(time.asctime(time.localtime())))