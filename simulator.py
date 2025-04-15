import os
import pandas as pd
from datetime import datetime

data_path = 'data'
# output_path = 'output/simulator'

# if not os.path.exists(output_path):
#     os.makedirs(output_path)

prices = pd.read_csv(os.path.join(data_path, 'prices.csv'))
names = pd.read_csv(os.path.join(data_path, 'names.csv'))

df = pd.merge(prices, names[['name', 'abbr']], on='name', how='left')
df['date'] = pd.to_datetime(df['date'])
df.drop(columns=['name'], inplace=True)

df_hkbond = df[df['abbr'] == 'HKBOND']
months = df_hkbond['date'].dt.to_period('M').unique()
month_day1 = []
for month in months:
    first_trading_day = df_hkbond[df_hkbond['date'].dt.to_period('M') == month]['date'].min()
    month_day1.append(first_trading_day)
month_day1 = month_day1[1:]

def simulate_without_inflation():
    results = pd.DataFrame(columns=['abbr', 'start_date', 'invested', 'current'])
    fund_abbrs = names['abbr'].unique()
    today = df.iloc[-1, 0]

    for abbr in fund_abbrs:
        invested = []
        current = []
        fund_df = df[df['abbr'] == abbr].copy()
        actual_start_date = fund_df.iloc[0, 0]
        today_price = fund_df.iloc[-1, 1]
        offset = -1
        for i, d in enumerate(month_day1):
            if d < actual_start_date:
                continue
            elif offset == -1:
                offset = i
            invested.append(0)
            current.append(0)
            relative_price = today_price / fund_df[fund_df['date'] == d]['price'].values[0]
            for i in range(len(invested)):
                invested[i] += 1
                current[i] += relative_price
        results = pd.concat([results, pd.DataFrame({'abbr': abbr, 'start_date': month_day1[offset:], 'invested': invested, 'current': current})], ignore_index=True)
    results['roi'] = (results['current'] - results['invested']) / results['invested'] * 100
    # pow(1 + annualized_roi, years) = current / invested
    # annualized_roi = pow(current / invested, 1 / years) - 1
    # years = (today - start_date).days / 365.25
    results['annualized_roi'] = ((results['current'] / results['invested']) ** (365.25 / (today - results['start_date']).dt.days)) - 1
    results.to_csv(os.path.join(data_path, 'simulate_without_inflation.csv'), index=False)
    return results

if __name__ == '__main__':
    simulate_without_inflation()