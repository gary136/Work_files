import numpy as np
import talib
import pandas as pd

def technical(df, rsi_range=15, kd_range=9, v_range=30):
    import numpy as np
    import talib
    import pandas as pd
    from math import sqrt
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
    
    df_technical = pd.DataFrame(data = {'es_date':es_date, 'raw_date':raw_date, 'btc_volume':volume_day, 'btc_price':price_day, 
                         'RSI_{}'.format(rsi_range):rsi, 
                         'K_{}'.format(kd_range):k, 'D_{}'.format(kd_range):d, 
                         'V_{}'.format(v_range): volatility
                                 })
    df_technical.index = pd.to_datetime(df_technical['raw_date'], format='%Y%m%d', errors='ignore')
    return df_technical