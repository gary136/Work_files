import pandas as pd
from espandas import Espandas
import json
from elasticsearch import Elasticsearch, TransportError

def write(mesg, path='/Users/gary/bitscrappinglog', mode='a'):
    with open(path, mode) as f:
        f.write(mesg+'\n')
        
def create(Index, Type, Host='35.194.152.180'):
    es = Elasticsearch([Host], timeout=30)
    empty = {
    }
    res = es.index(index=Index, doc_type=Type, id=1, body=empty)
    print(res['result'])
    es.delete(index=Index,doc_type=Type,id=1)
    
def pd_elastic(df):
    df['indexId'] = (df.index).astype(str)
    Index = input('index name: ')
    Type = input('type name: ')
    esp = Espandas()
    esp.es_write(df, Index, Type)

def get_last(Host='35.194.152.180'):
    es = Elasticsearch([Host], timeout=30)
    result = es.search(index="btc_top100_index", body={
        "aggs" : {"max_time" : { "max" : { "field" : "Time (UTC)" } }
        },
        "size":0
    })
    last = result['aggregations']['max_time']['value']/1000
    return last

def esbulk(Index, Type, df, Host='35.194.152.180'):
    es = Elasticsearch([Host], timeout=30)
    if not isinstance(df, pd.DataFrame):
        raise ValueError('df must be a pandas DataFrame')        

    def rec_to_actions(df):
        for record in df.to_dict(orient="records"):
            yield ('{ "index" : { "_index" : "%s", "_type" : "%s" }}'% (Index, Type))
            yield (json.dumps(record, default=int))
    if not es.indices.exists(Index):
        raise RuntimeError('index does not exists')
    
#     r = es.bulk(rec_to_actions(df)) # return a dict
#     write('not r["errors"]: {}'.format(not r["errors"]))
    
    try:
        r = es.bulk(rec_to_actions(df)) # return a dict
        write('not r["errors"]: {}'.format(not r["errors"]))
    except Exception as e:
        write('An unknown error occured connecting to ElasticSearch: %s' % e)