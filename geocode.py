import pandas as pd
import numpy as np
import requests
import time
from bs4 import BeautifulSoup

new_key1 = 'AIzaSyA1yfLkwTFPMVUs6Ms8VBvHp1EarM-PL0Q'
new_key2 = 'AIzaSyDzpcg00DecOXcDrRrVw16V_yOYj8H62XM'
new_key3 = 'AIzaSyDebea1g0MYe_AM44BrW5IkEwVIQrjzof4'
new_key4 = 'AIzaSyCGQ9tGC8H2hpfwRHycKRZBic78eEfBEF0'
new_key5 = 'AIzaSyBWzTtSzpf9u9Wxki_AKKR9CrvhO_Iw0gQ'
new_key6 = 'AIzaSyDFNqrxtoAHYAQVA0QVim0nM7bAivpXm5w'
new_key7 = 'AIzaSyA2q3Zo3RDCNtYw4rzmO4rCyB41ZozJK6I'
new_key8 = 'AIzaSyDCvTAN8k57d-w_D5P8Pur2nJwHs7DNOSY'
key1 = 'AIzaSyC_vcarGfMvLtfT9Hzgn1Q8ZgUbShHDSjk'
key2 = 'AIzaSyBQlgzxJoj-bFlT1HkIY6rAYeTFrT_YcSE'
key3 = 'AIzaSyArwew-mKF3WtQ_TSOvCTJl-2PfSatDvaQ'
key4 = 'AIzaSyBnoc6s57rpUmrzXyGkeXvjteWKhXL8VKI'
key5 = 'AIzaSyDDUiVULyAhtJ_RJSyP3TUOTk_fK9ir6YI'
key6 = 'AIzaSyD5X8K0uC3aLMuJ6crbbc0djiyEIWJb9kk'
key7 = 'AIzaSyCO0xnAgE7AT1a6c29A_PZWDsQl_yXIlI8'
key8 = 'AIzaSyCoF0hPC9XSwprvJ7QTn9sRsnNceo9j-tE'

key_list = [new_key1, new_key2, new_key3, new_key4, new_key5, new_key6, new_key7, new_key8,
            key1, key2, key3, key4, key5, key6, key7, key8]

def geoc(df, key_num1):
    if 'lat' not in df.columns:
        df['lat'] = pd.Series(np.zeros(len(df)), index=df.index)
        df['lon'] = pd.Series(np.zeros(len(df)), index=df.index)
#     start_n = input("starting number ")
    print("the current key number is " + str(key_num1))
#     for i in range(int(start_n), len(df)):
    i = int(input('start from '))
    global keyStatus
    keyStatus = 1
    while i < len(df):
        addr = df['address'][i]
        
        # 經緯度
        url = 'https://maps.googleapis.com/maps/api/geocode/xml?address=' + addr + '&key=' + key_list[int(key_num1)]
        r = requests.get(url)
        content = r.content
        bsobj = BeautifulSoup(content, 'html.parser')
        status = bsobj.find('status').get_text()
        if status == 'OVER_QUERY_LIMIT':
            print('need to change key, the current file number is ' + str(i))
            key_num1 = int(key_num1) + 1
            print('key number has changed to ' + str(key_num1))
            i-=1
            if key_num1 > len(key_list) - 1:
                keyStatus = 0
                break
        elif status == 'OK':
            lat = bsobj.find_all('lat')[0].get_text()    
            lon = bsobj.find_all('lng')[0].get_text()
            df['lat'][i] = lat
            df['lon'][i] = lon
        else:
            print('address is not vlaid')
            lat = 0
            lon = 0
            df['lat'][i] = lat
            df['lon'][i] = lon
        if i % 500 == 0:
            print(i)
            print('緯度為: ' + str(lat))
            print('經度為: ' + str(lon))
        i+=1
        time.sleep(1)
        
        # 里
        t_url = 'https://maps.googleapis.com/maps/api/geocode/xml?latlng=' + lan + ',' + long + '&key=' + key_list[int(key_num2)]
        r = requests.get(t_url)
        content = r.content
        bsobj = BeautifulSoup(content, 'html.parser')
        if status == 'OVER_QUERY_LIMIT':
            print('need to change key, the current number = ' + str(i))
            df.to_csv('house_temp.csv', index=False)
            break
        elif status == 'OK':
            vil = bsobj.find(text='administrative_area_level_4').parent.parent.long_name.get_text()
        else:
            vil = 0
        df['vil'][i] = vil
        print('里名為: ' + str(vil))    
        
        if total == 300:
            df.to_csv('house_temp.csv', index=False)
            total = 0
            print('==============================')
#     df['geo'] = pd.Series(np.zeros(len(df)), index=df.index)
#     for i in range(len(df)):
#         df['geo'][i] = int(str(int(df['lan'][i]*100)) + str(int(df['long'][i]*100)))
    return df