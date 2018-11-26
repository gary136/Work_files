import requests
from io import StringIO
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
import time
import pymongo

def crawl_price(date):
    head = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
    base = 'http://www.twse.com.tw/exchangeReport/MI_INDEX?response=csv&date={}&type=ALL'
    r = requests.get(base.format(str(date).split(' ')[0].replace('-','')), head)
    filtered = [i.replace(' ', '')
            for i in r.text.split('\n')
            if len(i.split('",')) == 17 and i[0] != '=']
    merge_data = "\n".join(filtered)
    ret = pd.read_csv(StringIO(merge_data))
    ret = ret.set_index('證券代號')
    ret.drop(['Unnamed: 16', '最後揭示買價', '最後揭示買量', '最後揭示賣價', '最後揭示賣量'], axis = 1, inplace = True)
    def str_num(x):
        if '.' in x:
            num_x = float(x.replace(',',''))
        else:
            num_x = int(x.replace(',',''))
        return num_x
    for i in ['成交股數', '成交筆數', '成交金額', '本益比']:
        try:
            ret[i] = ret[i].apply(str_num)
        except:
            print('some transform fails')
    return ret

def multiple(n_days):
    data = {}
    dt = datetime.now()
    fail_count = 0
    allow_continuous_fail_count = 15
    while len(data) < n_days:
        try:
            # 抓資料
            data[dt.strftime('%Y%m%d')] = crawl_price(dt.strftime('%Y%m%d'))
            fail_count = 0
        except:
            # 假日爬不到
            print('{} is holiday'.format(dt.strftime('%Y%m%d')))
            fail_count += 1
            if fail_count == allow_continuous_fail_count:
                raise
                break

        # 減一天
        dt -= timedelta(days=1)
        time.sleep(5)
    return data











def ohlcv(df):
    close = pd.DataFrame({k:d['收盤價'] for k,d in df.items()}).transpose()
    open_ = pd.DataFrame({k:d['開盤價'] for k,d in df.items()}).transpose()
    high = pd.DataFrame({k:d['最高價'] for k,d in df.items()}).transpose()
    low = pd.DataFrame({k:d['最低價'] for k,d in df.items()}).transpose()
    volume = pd.DataFrame({k:d['成交股數'] for k,d in df.items()}).transpose()
    for i in [close, open_, high, low, volume]:
        i.index = pd.to_datetime(i.index)
    return [close, open_, high, low, volume]

def save_ohlcv(df):
    s_df = df.reset_index()
    s_df_column = list(s_df.columns)
    s_df_column[0] = '_id'
    s_df.columns = s_df_column
    return s_df

def mongobulk(df, database, collection, Host='localhost:27017'):
    myclient = pymongo.MongoClient("mongodb://{}".format(Host))
    mydb = myclient[database]
    mycol = mydb[collection]
    def pandas_generator(df):
        for record in df.to_dict(orient="records"):
            yield record
    g = pandas_generator(df)
    while True:
        try:
            mycol.insert_one(next(g))
        except StopIteration:
            print('{} has StopIteration'.format(collection))
            break
            
def write(sav):
    mapper = zip(sav, ['close', 'open', 'high', 'low', 'volume'])
    for k,d in mapper:
        mongobulk(k, 'stock', d)
            
def from_mongo(database, collection, Host='localhost:27017'):
    myclient = pymongo.MongoClient("mongodb://{}".format(Host))
    mydb = myclient[database]
    mycol = mydb[collection]
    df = pd.DataFrame(list(mycol.find()))
    df = df.set_index('_id')
    return df

if __name__ == '__main__':
    n_days = int(input('enter scraping date range: '))
    mul_data = multiple(n_days)
    ori_ohlcv = [close, open_, high, low, volume] = ohlcv(mul_data)
    time_ohlcv = [s_close, s_open_, s_high, s_low, s_volume] = list(map(save_ohlcv, ori_ohlcv))
    write(time_ohlcv)
    c, o, h, l, v = [from_mongo('stock', i) for i in ['close', 'open', 'high', 'low', 'volume']]
    