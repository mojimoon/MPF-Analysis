import pandas as pd
import glob
import os

raw_data_path = 'data/raw'
data_path = 'data'

'''
VALUATION DATE,FUND_NAME_1_EN,CLASS_FUND_1_EN,FUND_NAME_1_ZH,CLASS_FUND_1_ZH,FUND_1_PRICE_HKD
17/09/2001,Sun Life MPF Hong Kong Dollar Bond Fund,Class A,永明強積金港元債券基金,A類單位,1.0528
'''

csv_files = glob.glob(os.path.join(raw_data_path, '*.csv'))
df_list = []

for file in csv_files:
    df = pd.read_csv(file, encoding='utf-8')
    df = df[['VALUATION DATE', 'FUND_NAME_1_EN', 'FUND_1_PRICE_HKD']]
    df.columns = ['date', 'name', 'price']
    df_list.append(df)

df = pd.concat(df_list, ignore_index=True)
df['date'] = pd.to_datetime(df['date'], format='%d/%m/%Y')
df['price'] = df['price'].astype(float)

print(df.head())
df.to_csv(os.path.join(data_path, 'processed_data.csv'), index=False)