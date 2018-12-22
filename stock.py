import requests
from io import StringIO
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
import pymongo
from functools import reduce
import time
from pd_sql import connect_sql, mapping_df_types

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
    def clean_dash(x):
        if x == '--':
            return 0
        else:
            return float(x.replace(',',''))
    for i in ['成交股數', '成交筆數', '成交金額', '本益比']:
        try:
            ret[i] = ret[i].apply(str_num)
        except:
            print('some transform fails')
    for i in ['開盤價', '最高價', '最低價', '收盤價']:
        try:
            ret[i] = ret[i].apply(clean_dash)
        except:
            print('some transform fails in', i)
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



class Security(object):
    def __init__(self, data=None, close=None, open_=None, high=None, low=None, volume=None):
        self.data=data
        self.close=close
        self.open_=open_
        self.high=high
        self.low=low
        self.volume=volume
        
    def set_ohlcv(self):
        indicators = ['收盤價', '開盤價', '最高價', '最低價', '成交股數']
        if self.data!=None:
            [self.close, self.open_, self.high, self.low, self.volume] = [pd.DataFrame({k:d[i] for k,d in self.data.items()}).transpose() for i in indicators]
            for attr in [self.close, self.open_, self.high, self.low, self.volume]:
                attr.index = pd.to_datetime(attr.index)
#             return [close, open_, high, low, volume]

    def merge(self, stockId):
        df = reduce(lambda left, right:
           pd.merge(pd.DataFrame(left), pd.DataFrame(right), left_index=True, right_index=True), 
           [i[stockId] for i in [self.close, self.open_, self.high, self.low, self.volume]])
        df.reset_index(inplace=True)
        df.columns=['timestamp', 'close', 'open', 'high', 'low', 'volume']
        df = df.sort_values(by='timestamp').reset_index(drop=True)
        return df

# mongo    
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
# mongo  

def data_transform_write(data_per_date):
    Base, engine, conn, metadata = connect_sql(database='stock')
    a = Security()
    a.data = data_per_date
    a.set_ohlcv()
    ids = list(a.close.columns)
    data_per_stock = dict(zip(list(ids), list(map(a.merge, ids))))
    for i in list(data_per_stock.keys()):
        print('Current stock is', i)
        dtypedict = mapping_df_types(data_per_stock[i])
        data_per_stock[i].to_sql(name=i, con=conn, if_exists='append', index=False, dtype=dtypedict)

def n_days_str(num):
    dt = datetime.now() - timedelta(days=num)
    var_time = datetime.strptime(dt.strftime('%Y%m%d'), '%Y%m%d').strftime('%Y-%m-%d %H:%M:%S')
    return var_time

def new_max(sqlObject, Id, date):
    try:
        base_command = '''select (max(close) - (select close from `{}` where timestamp = 
        (select max(timestamp) from `{}`))) 
        / max(close) from `{}` where  timestamp >= "{}" '''
        sqlObject.call = base_command.format(Id,Id,Id, date)
        return round(sqlObject.get_res()[0][0], 3)
    except TypeError:
        return 0        

if __name__ == '__main__':
    n_days = int(input('enter scraping date range: '))
    mul_data = multiple(n_days)
    ori_ohlcv = [close, open_, high, low, volume] = ohlcv(mul_data)
    time_ohlcv = [s_close, s_open_, s_high, s_low, s_volume] = list(map(save_ohlcv, ori_ohlcv))
    write(time_ohlcv)
    c, o, h, l, v = [from_mongo('stock', i) for i in ['close', 'open', 'high', 'low', 'volume']]
    