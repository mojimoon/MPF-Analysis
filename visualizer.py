import os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import seaborn as sns
from datetime import timedelta, datetime

data_path = 'data'
output_path = 'output'
per_year_path = os.path.join(output_path, 'history')
per_fund_path = os.path.join(output_path, 'fund')
# output_img = os.path.join(output_path, 'price_history.png')

if not os.path.exists(output_path):
    os.makedirs(output_path)

prices = pd.read_csv(os.path.join(data_path, 'prices.csv'))
names = pd.read_csv(os.path.join(data_path, 'names.csv'))

df = pd.merge(prices, names[['name', 'abbr']], on='name', how='left')
df['date'] = pd.to_datetime(df['date'])
df.drop(columns=['name'], inplace=True)

last_date = df.iloc[-1, 0]

def per_year():
    if not os.path.exists(per_year_path):
        os.makedirs(per_year_path)

    period_years = [1, 3, 5, 10, 25]
    # start_dates = [last_date - timedelta(days=(1461 * period // 4)) for period in period_years]
    start_dates = [datetime(year=last_date.year - period, month=last_date.month, day=last_date.day) for period in period_years]

    fund_abbrs = names['abbr'].unique()

    # fig, axes = plt.subplots(len(period_years), 1, figsize=(14, 7 * len(period_years)), sharex=False)
    # fig.suptitle(f'Sun Life MPF Fund Price History (as of {last_date.strftime("%Y-%m-%d")})', fontsize=20, fontweight='bold', y=0.99)

    # so when axes is (1, 1), it is not subscriptable
    # if not hasattr(axes, '__iter__'):
    #     axes = [axes]

    for i in range(len(period_years)):
        start_date = start_dates[i]
        period_label = period_years[i]
        # ax = axes[i]

        fig, ax = plt.subplots(figsize=(14, 7))
        fig.suptitle(f'Sun Life MPF Fund Price History (as of {last_date.strftime("%Y-%m-%d")})', fontsize=20, fontweight='bold', y=0.99)

        ax.set_title(f'Last {period_label} Year{period_label > 1 and "s" or ""}')
        ax.axhline(0, color='grey', linestyle='--', linewidth=0.8)
        ax.set_ylabel('Price Change (%)')
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax.tick_params(axis='x', rotation=45)

        for abbr in fund_abbrs:
            period_data = df[(df['abbr'] == abbr) & (df['date'] >= start_date)].copy()

            if period_data.empty:
                continue

            actual_start_date = period_data.iloc[0, 0]
            start_price = period_data.iloc[0, 1]

            if pd.isna(start_price):
                continue

            period_data['price_change'] = (period_data['price'] - start_price) / start_price * 100
            ax.plot(period_data['date'], period_data['price_change'], label=abbr, linewidth=1.5)
            
        ax.legend(loc='upper left', bbox_to_anchor=(1, 1), fontsize='small')
        ax.grid(True, linestyle=':', linewidth=0.5)

        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        plt.savefig(os.path.join(per_year_path, f'{period_label}.png'), bbox_inches='tight')

    # plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    # plt.savefig(output_img, bbox_inches='tight') 

if __name__ == '__main__':
    per_year()
