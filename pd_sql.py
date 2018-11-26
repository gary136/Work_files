import sqlalchemy
import pandas as pd
from sqlalchemy import *
from pandas.core.frame import DataFrame
import time
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.types import NVARCHAR, Float, Integer
from datetime import datetime, timedelta, timezone
import matplotlib.pyplot as plt
    
def connect_sql(database='btc_t'):
    Base = declarative_base()
    engine = create_engine("mysql+pymysql://root:jack0705@localhost:3306/{}".format(database),echo=True)
    conn = engine.connect()
    metadata = MetaData(engine)
    return Base, engine, conn, metadata

def mapping_df_types(df):
    dtypedict = {}
    for i, j in zip(df.columns, df.dtypes):
        if "object" in str(j):
            dtypedict.update({i: NVARCHAR(length=255)})
#         if "float" in str(j):
#             dtypedict.update({i: Float(precision=14, asdecimal=True)})
#         if "int" in str(j):
#             dtypedict.update({i: Integer()})
    return dtypedict

class Sql_result():
    def __init__(self, conn, call=None):
        self.call = call
        self.conn = conn
    def get_res(self):
        s = text(self.call)
        res = self.conn.execute(s)
        return list(res)
    def res_count_time(self):
        time_1 = time.time()
        res_list = list(self.get_res())
        time_2 = time.time()
        time_passed = time_2-time_1
        try:            
            return res_list, 'time: {}'.format(time_passed)
        except sqlalchemy.exc.ResourceClosedError as e:
            print(e.args[0])
    
#     stored procedures
    def balance_per_address(self, var_time):
        self.call = '''select a.address, a.rank, a.`Balance (BTC)`, a.`Time (UTC)` latest_time 
               from (select address, max(`Time (UTC)`) latest_time from btc 
               where `Time (UTC)` < {} group by address) x 
               join btc a on a.address = x.address and a.`Time (UTC)` = x. latest_time 
               order by a.`Balance (BTC)` desc;'''.format(var_time)
#         res = ins.get_res()
#         df = pd.DataFrame(res, columns = ['address', 'rank', 'Balance (BTC)', 'Time (UTC)'])
#         return df
    def latest_time(self):
        self.call = '''select max(`Time (UTC)`) from btc;'''
        res = self.get_res()
        return res[0][0]
    def describe_table(self, table_name):
        self.call = '''desc {};'''.format(table_name)
        res = self.get_res()
        df = pd.DataFrame(res, columns = ['Field', 'Type', 'Null', 'Key', 'Default', 'Extra'])
        return df
    

def twin(data_y1, data_y2, *args, color_1 = 'k', color_2 = 'r'):
    import matplotlib.pyplot as plt
    fig, ax1 = plt.subplots(figsize=(12,4))
    ax2 = ax1.twinx()  # this is the important function
    if len(args) > 0:
        ax1.plot(data_y1, label=args[0], color = 'k')
        ax1.set_ylabel(args[0])
        ax1.set_xlabel(args[1])
        ax2.plot(data_y2, label=args[2], color = 'r')
        ax2.set_ylabel(args[2])
        fig.legend()
    else:
        ax1.plot(data_y1, color = 'k')
        ax2.plot(data_y2, color = 'r')
        fig.legend()

def latest_balance(ins, var_time):
    ins.call = '''select a.address, a.rank, a.`Balance (BTC)`, a.`Time (UTC)` latest_time 
           from (select address, max(`Time (UTC)`) latest_time from btc 
           where `Time (UTC)` < {} group by address) x 
           join btc a on a.address = x.address and a.`Time (UTC)` = x. latest_time 
           order by a.`Balance (BTC)` desc;'''.format(var_time)
    res = ins.get_res()
    df = pd.DataFrame(res, columns = ['address', 'rank', 'Balance (BTC)', 'Time (UTC)'])
    return df

def time_series(start):
    t = datetime.strptime(start, '%Y-%m-%dT%H:%M:%SZ')
    c = []
    while t < datetime.now():
        n_t = datetime.strftime(t, '%Y-%m-%dT%H:%M:%SZ')
        c.append(n_t)
        t+=timedelta(days=1)
    return c
def accumulated(ins, ser):
    f_c = list(map(lambda x:datetime.strptime(x, '%Y-%m-%dT%H:%M:%SZ'), ser))
    num = list(map(lambda x:latest_balance(ins, "{}{}{}".format("'", x, "'"))['Balance (BTC)'].sum(), ser))
    df = pd.DataFrame(num, columns=['BTC Amount'])
    t = df['BTC Amount']
    t.index = f_c
    t.index.name = 'Date'
    return t
def acc_plot(data):
    fig, ax1 = plt.subplots(figsize=(15,8))
    ax1.plot(data)
    ax1.set_xlabel('Date')
    ax1.set_ylabel('BTC Amount')
