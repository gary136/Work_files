import pandas as pd
from espandas import Espandas
import json
from elasticsearch import Elasticsearch, TransportError
import time
import numpy as np
import talib
from math import sqrt

def write(mesg, path='/Users/gary/bitscrappinglog', mode='a'):
    with open(path, mode) as f:
        f.write(mesg+'\n')

es = Elasticsearch(['35.194.152.180'], timeout=30)

def connect_ela(Host):
    es = Elasticsearch([Host], timeout=30)
    return es


class Ela_result():
    def __init__(self, es, index="btc_top100_index", query=None):
        self.es = es
        self.index = index
        self.query = query
    def get_res(self):
        res = self.es.search(index=self.index, body=self.query)
        return res
    def res_pandas(self):
        res = self.get_res()
        doc = res['hits']['hits']
        data = list(map(lambda x:x['_source'], doc))
        df = pd.DataFrame(data)
        return df
    
#     stored procedure
    def latest_time(self):
        self.query = {
            "aggs" : {"max_time" : { "max" : { "field" : "Time (UTC)" } }
            },
            "size":0
        }
        res = self.get_res()
        num_res = int(res['aggregations']['max_time']['value']/1000)
        res_as_str = res['aggregations']['max_time']['value_as_string'].replace('.000', '')
        return num_res, res_as_str
    def time_filtered(self, var_time):
        self.query = {'size':10000, 
           'query':{
                    "bool": {
                        "filter": {
                            "range": {
                              'Time (UTC)': {
                                "gt": var_time
                                  }
                            }
                          }
                        }
                    }   
          }

def pd_elastic(df):
    df['indexId'] = (df.index).astype(str)
    Index = input('index name: ')
    Type = input('type name: ')
    esp = Espandas()
    esp.es_write(df, Index, Type)

def create(Index, Type):
    empty = {}
    res = es.index(index=Index, doc_type=Type, id=1, body=empty)
    print(res['result'])
    es.delete(index=Index,doc_type=Type,id=1)
    

def get_last():
    result = es.search(index="btc_top100_index", body={
        "aggs" : {"max_time" : { "max" : { "field" : "Time (UTC)" } }
        },
        "size":0
    })
    last = result['aggregations']['max_time']['value']/1000
    return last

def esbulk(Index, Type, df):
    if not isinstance(df, pd.DataFrame):
        raise ValueError('df must be a pandas DataFrame')        

    def rec_to_actions(df):
        for record in df.to_dict(orient="records"):
            yield ('{ "index" : { "_index" : "%s", "_type" : "%s" }}'% (Index, Type))
            yield (json.dumps(record, default=int))
    if not es.indices.exists(Index):
        raise RuntimeError('index does not exists') 
        
    try:
        r = es.bulk(rec_to_actions(df)) # return a dict
        if r["errors"] == True:
            write('error happens because of {}'.format(r['items'][0]['index']['error']))
        else:
            write('data transmitts into elasticsearch @ {}'.format(time.asctime(time.localtime())))
    except Exception as e:
        write('An unknown error occured connecting to ElasticSearch: %s' % e)
        
def es_all(Index="btc_top100_index", query = {'size':10000, 'query':{"match_all": {}}}):
    total = []
#     query = {'size':10000, 'query':{"match_all": {}}}
    def rest(res):
        scrollId = res['_scroll_id']
        new_res = es.scroll(scroll_id = scrollId, scroll = '1m')
        return new_res
    # first
    res1 = es.search(index=Index, body=query, scroll='1m')
    total.append(res1['hits']['hits'])
    # second
    res_ = rest(res1)
    total.append(res_['hits']['hits'])
    # third and then
    while res_['hits']['hits'] != []:
        res_ = rest(res_)
        if res_['hits']['hits'] != []:
            total.append(res_['hits']['hits'])
    
    doc = total[0]
    for i in range(1, len(total)):
        doc += total[i]
    data = list(map(lambda x:x['_source'], doc))
    return data

def json_pandas(data):
    import json
    str_d = json.dumps(data)
    df = pd.read_json(str_d, orient='records')
    return df

def technical(df, rsi_range=15, kd_range=9, v_range=30):
    df_day = df.groupby(['timestamp'])
    volume_day = np.array(df_day.sum()['Amount (BTC)'])
    h = l = c = price_day = np.array(df_day.mean()['USD price'])
    raw_date = list(df_day.groups.keys())
    
    def iso_format(x):
        t = str(x)
        return t[:4]+'-'+t[4:6]+'-'+t[6:]+'T00:00:00Z'
    
    es_date = list(map(iso_format, list(df_day.groups.keys())))
    
    rsi = talib.RSI(volume_day, timeperiod=rsi_range)
    
    k, d = talib.STOCH(high=volume_day, 
                low=volume_day, 
                close=volume_day,
                fastk_period=kd_range,
                slowk_period=3,
                slowd_period=3
    )
    
    volatility = talib.NATR(h, l, c, timeperiod=v_range) * sqrt(365)
    
    df_technical = pd.DataFrame(data = {'es_date':es_date, 'timestamp':raw_date, 'btc_volume':volume_day, 'btc_price':price_day, 
                         'RSI_{}'.format(rsi_range):rsi, 
                         'K_{}'.format(kd_range):k, 'D_{}'.format(kd_range):d, 
                         'Vola_{}'.format(v_range): volatility
                                 })
    
    for i in ['btc_volume', 'Vola_{}'.format(v_range), 'btc_price']:
        df_technical[i] = df_technical[i].apply(round, args=(3, ))
    df_technical.index = pd.to_datetime(df_technical['timestamp'], format='%Y%m%d', errors='ignore')
    return df_technical

def update_tech(Index='btc_tech', docType='indicator'):
    df_tech = technical(json_pandas(es_all()))
    es.delete_by_query(index=Index, doc_type=docType, body={'query':{"match_all": {}}})
    res = esbulk(Index, docType, df_tech)