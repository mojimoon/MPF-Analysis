import os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np
import seaborn as sns
from datetime import timedelta, datetime
from scipy.signal import find_peaks

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
    
    sns.set_theme(style="darkgrid")

    period_years = [1, 3, 5, 10, 25]
    start_dates = [datetime(year=last_date.year - period, month=last_date.month, day=last_date.day) for period in period_years]

    fund_abbrs = names['abbr'].unique()

    for i in range(len(period_years)):
        start_date = start_dates[i]
        period_label = period_years[i]

        fig, ax = plt.subplots(figsize=(14, 7))
        fig.suptitle(f'Sun Life MPF Fund Price History ({period_label} Year{period_label > 1 and "s" or ""})', fontsize=20, fontweight='bold')
        
        ax.set_title(f'{start_date.strftime("%Y-%m-%d")} - {last_date.strftime("%Y-%m-%d")}', fontsize=16, fontweight='bold')
        ax.axhline(0, color='grey', linestyle='--', linewidth=0.8)
        ax.set_ylabel('Price Change (%)')
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax.tick_params(axis='x', rotation=45)

        if period_label <= 2:
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
        elif period_label <= 5:
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3, bymonth=[1, 4, 7, 10]))
        # elif period_label <= 10:
        #     ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6, bymonth=[1, 7]))
        elif 10 < period_label <= 25:
            ax.xaxis.set_major_locator(mdates.YearLocator(1))

        for abbr in fund_abbrs:
            plot_df = df[(df['abbr'] == abbr) & (df['date'] >= start_date)].copy()

            if plot_df.empty:
                continue

            actual_start_date = plot_df.iloc[0, 0]
            start_price = plot_df.iloc[0, 1]

            if pd.isna(start_price):
                continue

            plot_df['price_change'] = (plot_df['price'] - start_price) / start_price * 100
            plot_df = plot_df.set_index('date')

            if period_label == 10:
                plot_df = plot_df[['price_change']].resample('5D').mean().interpolate(method='linear')
            elif period_label == 25:
                plot_df = plot_df[['price_change']].resample('10D').mean().interpolate(method='linear')
            
            plot_df = plot_df.reset_index()
            ax.plot(plot_df['date'], plot_df['price_change'], label=abbr, linewidth=1.0)
        
        ax.legend(loc='upper left', fontsize=10, frameon=False, ncols=3)
        ax.grid(True, linestyle=':', linewidth=1, color='#bfbfbf')
        sns.despine()

        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        plt.savefig(os.path.join(per_year_path, f'{period_label}.png'), bbox_inches='tight')
        plt.close(fig)

def per_fund():
    if not os.path.exists(per_fund_path):
        os.makedirs(per_fund_path)

    sns.set_theme(style="darkgrid")

    fund_abbrs = names['abbr'].unique()

    for abbr in fund_abbrs:
        plot_df = df[df['abbr'] == abbr].copy()

        if plot_df.empty:
            continue

        actual_start_date = plot_df.iloc[0, 0]
        start_price = plot_df.iloc[0, 1]

        if pd.isna(start_price):
            continue

        plot_df['price_change'] = (plot_df['price'] - start_price) / start_price * 100
        diff = (last_date - actual_start_date).days
        if diff >= 3650:
            plot_df = plot_df.set_index('date')
            plot_df_resampled = plot_df[['price_change']].resample('5D').mean().interpolate(method='linear').reset_index()
        elif diff >= 7300:
            plot_df = plot_df.set_index('date')
            plot_df_resampled = plot_df[['price_change']].resample('15D').mean().interpolate(method='linear').reset_index()
        else:
            plot_df_resampled = plot_df.copy()

        yext = plot_df_resampled['price_change'].max() - plot_df_resampled['price_change'].min()
        peak_prominence = max(5, yext * 0.05)
        trough_prominence = peak_prominence
        peak_distance = max(30, diff // 35)

        price_change = plot_df_resampled['price_change'].to_numpy()
        if len(price_change) > peak_distance:
            peaks, _ = find_peaks(price_change, prominence=peak_prominence, distance=peak_distance)
            troughs, _ = find_peaks(-price_change, prominence=trough_prominence, distance=peak_distance)
        else:
            peaks = []
            troughs = []

        fig, ax = plt.subplots(figsize=(12, 6))
        full_name = names[names['abbr'] == abbr]['name'].values[0]
        fig.suptitle(f'{full_name} Price History (As of {last_date.strftime("%Y-%m-%d")})', fontsize=18, fontweight='bold')
        
        # ax.set_title(f'As of {last_date.strftime("%Y-%m-%d")}', fontsize=16, fontweight='bold')
        ax.axhline(0, color='grey', linestyle='--', linewidth=1.0)
        ax.set_ylabel('Price Change (%)')
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax.tick_params(axis='x', rotation=45)

        if diff < 732:
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
        elif diff < 1828:
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3, bymonth=[1, 4, 7, 10]))
        elif diff < 3654:
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6, bymonth=[1, 7]))
        elif diff < 7306:
            ax.xaxis.set_major_locator(mdates.YearLocator(1))
        else:
            ax.xaxis.set_major_locator(mdates.YearLocator(2))
        
        ax.plot(plot_df_resampled['date'], plot_df_resampled['price_change'], linewidth=1.5, zorder=1, color='green')

        for idx in peaks:
            d, pc = plot_df_resampled['date'].iloc[idx], plot_df_resampled['price_change'].iloc[idx]
            ax.plot(d, pc, 'ro', markersize=5, zorder=2)
            ax.annotate(f"{d.strftime('%Y-%m-%d')}\n{1 + pc / 100:.4f}", (d, pc),
                        textcoords="offset points", xytext=(0, 10), ha='center', fontsize=10, color='red')
    
        for idx in troughs:
            d, pc = plot_df_resampled['date'].iloc[idx], plot_df_resampled['price_change'].iloc[idx]
            ax.plot(d, pc, 'bo', markersize=5, zorder=2)
            ax.annotate(f"{d.strftime('%Y-%m-%d')}\n{1 + pc / 100:.4f}", (d, pc),
                        textcoords="offset points", xytext=(0, -25), ha='center', fontsize=10, color='blue')
        
        ax.grid(True, linestyle=':', linewidth=1, color='#bfbfbf')
        sns.despine()

        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        plt.savefig(os.path.join(per_fund_path, f'{abbr}.png'), bbox_inches='tight')
        plt.close(fig)

if __name__ == '__main__':
    # per_year()
    per_fund()
