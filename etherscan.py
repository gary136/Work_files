import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup

head = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}

class eth_data_scrapper(object):
    def __init__(self, address):
        self.headers = head
        self.address = address
        self.url_base = 'https://etherscan.io/txs?a={}&p={}'
        
    def single_table(self):
        page = 1
        single_list = []
        signal = 'There are no matching entries'
        while page < 100:
            url = self.url_base.format(self.address, page)
            res = requests.get(url, self.headers)

            df = pd.read_html(res.text)[0]
            #judge
            status = re.findall(signal, res.text)
            if status != []:
                print('page {}'.format(page), signal)
                break
            else:
                single_list.append(df)
#                 print('page {} end'.format(page))
                page+=1
        df_single = pd.concat(single_list).sort_values(by='Block', ascending=False)
        return df_single
    
    @staticmethod
    def clean_table(df):
        df['Value'] = df['Value'].apply(lambda x:float(x.split(' ')[0].replace(',', '')))
        df = df[df['Value'] > 0.1]
        return df

def processing(df):
    import time
    from functools import reduce
    df.drop('TxHash', axis=1, inplace=True)
    df.columns = ['Block', 'Age', 'From', 'In / Out', 'To', 'Amount (Eth)', '[TxFee]']
    
    def judge(cols):
        condition = cols[0]
        value = cols[1]

        if condition == 'IN':
            return value
        else:
            return -value
    
    def all_pipe(raw):
        transform = {
            'sec':1, 
            'secs':1, 
            'min':60, 
            'mins':60, 
            'hr':60*60, 
            'hrs':60*60,
            'day':60*60*24, 
            'days':60*60*24
        }

        def str_2_num(x):
            if x not in transform:
                try:
                    return int(x)
                except ValueError as v:
                    print(v)
                    return 0
            else:
                return transform[x]
    #     def num_list(x):
    #         num_list = list(map(str_2_num, x))
    #         return num_list
        def split_list(x):
            if len(x) > 2:
                return x[:2], x[2:]
            else:
                return x
        def m(x, y):
            return x*y
        def a(x, y):
            return x+y
        def reduced_list(i):
            if type(i) == tuple:
                multiple = map(lambda x:reduce(m, x), i)
                aggr = reduce(a, multiple)
                return aggr
            
            else:
                return reduce(m, i)
    
        seperated = raw.split(' ')
        num = list(map(str_2_num, seperated))
        num_split = split_list(num)
        final = reduced_list(num_split)

        return int(time.time()) - final
    
    df['Amount (Eth)'] = df[['In / Out', 'Amount (Eth)']].apply(judge, axis=1)
    df['time'] = df['Age'].apply(lambda x:x.split(' ago')[0])
    df['time'] = df['time'].apply(all_pipe)
    df['Time (UTC)'] = df['time'].apply(lambda x:time.strftime("%Y-%m-%dT%H:%M:%SZ", time.localtime(x)))
    df['timestamp'] = df['time'].apply(lambda x:int(time.strftime("%Y%m%d", time.localtime(x))))
    df.drop(['Age', '[TxFee]', 'time'], axis=1, inplace=True)
    df = df[['Block', 'Time (UTC)', 'timestamp', 'From', 'In / Out', 'To', 'Amount (Eth)']]
    
    return df

def join_price(df):
    from cryptocmd import CmcScraper
    scraper = CmcScraper('ETH')
    header, data = scraper.get_data()
    eth_data = pd.DataFrame(data, columns=header)
    
    def reverse(x):
        t = x.split('-')
        r = t[2]+t[1]+t[0]
        return int(r)

    eth_data['timestamp'] = eth_data['Date'].apply(reverse)
    eth_data_price = eth_data[['Close**', 'timestamp']]
    df_complete = pd.merge(df, eth_data_price, how='inner', on='timestamp')
    
    df_complete.columns = ['Block', 'Time (UTC)', 'timestamp', 'From', 'In / Out', 'To',
       'Amount (Eth)', 'Eth_usd_price']
    
    return df_complete

if __name__ == "__main__":
    all_list = []
    e = eth_address_scrapper()
    rich_address = e.get_list()
    for i in rich_address:
        print(i, rich_address.index(i))
        try:
            t = eth_data_scrapper(i)
            raw = t.single_table()
            df = t.clean_table(raw)
            all_list.append(df)
        except IndexError:
            print('IndexError')
    df_t = pd.concat(all_list).sort_values(by='Block', ascending=False)
    df_cle = processing(df_t)
    df_complete = join_price(df_cle)