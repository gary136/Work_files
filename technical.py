import numpy as np
import talib
import pandas as pd

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
                                 }).sort_values(by='timestamp', ascending=False)
    return df_technical