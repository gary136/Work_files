from pd_sql import *
from pd_ela import *

if __name__ == "__main__":
    Base, engine, conn, metadata = connect_sql()
    a = Sql_result(conn=conn)
    sql_latest_time = a.latest_time()
    
    e = Ela_result(es)
    e.time_filtered(sql_latest_time)
    df = e.res_pandas()
    if len(df) > 0:
        dtypedict = mapping_df_types(df.sort_values('Time (UTC)', ascending=False))
        df.to_sql(name='btc', con=conn, if_exists='append', index=False, dtype=dtypedict)
        print('{} docs has been updated'.format(len(df)))
    else:
        print('nothing has been updated')
    
    update_tech()