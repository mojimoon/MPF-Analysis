import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
from datetime import datetime, timedelta

data_path = 'data'

names = pd.read_csv(os.path.join(data_path, 'names.csv'))
per_year_path = os.path.join('output', 'simulation', 'history')
per_fund_path = os.path.join('output', 'simulation', 'fund')

def prepare_data():
    prices = pd.read_csv(os.path.join(data_path, 'prices.csv'))
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
    return df, month_day1

def prepare_inflation():
    inflation = pd.read_csv(os.path.join(data_path, 'inflation.csv'))
    inflation['nominal_base_today'] = 1.0
    for i in range(len(inflation) - 2, -1, -1):
        inflation.iloc[i, 2] = inflation.iloc[i + 1, 2] / (1 + inflation.iloc[i, 1] / 100)
    inflation_start_year = inflation.iloc[0, 0]
    return inflation, inflation_start_year

def simulate_without_inflation():
    df, month_day1 = prepare_data()

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
    results['roi'] = (results['current'] - results['invested']) / results['invested']
    # pow(1 + annualized_roi, years) = current / invested
    # annualized_roi = pow(current / invested, 1 / years) - 1
    # years = (today - start_date).days / 365.25
    results['annualized_roi'] = ((results['current'] / results['invested']) ** (365.25 / (today - results['start_date']).dt.days)) - 1
    results.to_csv(os.path.join(data_path, 'simulate_without_inflation.csv'), index=False)
    return results

def simulate_with_inflation():
    df, month_day1 = prepare_data()
    inflation, inflation_start_year = prepare_inflation()

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
            yr = d.year
            invested_today_value = inflation.iloc[yr - inflation_start_year, 2]
            current_today_value = invested_today_value * today_price / fund_df[fund_df['date'] == d]['price'].values[0]
            for i in range(len(invested)):
                invested[i] += invested_today_value
                current[i] += current_today_value
        results = pd.concat([results, pd.DataFrame({'abbr': abbr, 'start_date': month_day1[offset:], 'invested': invested, 'current': current})], ignore_index=True)
    results['roi'] = (results['current'] - results['invested']) / results['invested']
    results['annualized_roi'] = ((results['current'] / results['invested']) ** (365.25 / (today - results['start_date']).dt.days)) - 1
    results.to_csv(os.path.join(data_path, 'simulate_with_inflation.csv'), index=False)
    return results

def visualize_per_year(resdf, withInflation):
    if not os.path.exists(per_year_path):
        os.makedirs(per_year_path)
    
    sns.set_theme(style="darkgrid")

    last_date = resdf.iloc[-1, 1]
    period_years = [1, 3, 5, 10, 25]
    start_dates = [datetime(year=last_date.year - period, month=1, day=1) for period in period_years]
    fund_abbrs = names['abbr'].unique()

    vals = [('roi', 'Return over Investment'), ('annualized_roi', 'Annualized Return over Investment')]

    for ky, label in vals:
        for i in range(len(period_years)):
            if ky == 'annualized_roi' and i == 0:
                continue # too short period makes annualized roi very high, meaningless
            start_date = start_dates[i]
            # annualized_end_date = last_date - timedelta(days=360)
            period_label = period_years[i]
            fig, ax = plt.subplots(figsize=(14, 7))
            fig.suptitle(f'Sun Life MPF {label} ({period_label} Year{period_label > 1 and "s" or ""})', fontsize=20, fontweight='bold')
            ax.set_title(f'{start_date.strftime("%Y-%m-%d")} - {last_date.strftime("%Y-%m-%d")} {withInflation and "(considering inflation)" or ""}', fontsize=16, fontweight='bold')
            ax.axhline(0, color='grey', linestyle='--', linewidth=1.0)
            ax.set_ylabel(f'{label} (%)')
            ax.set_xlabel('Investment Start Date')
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
            ax.tick_params(axis='x', rotation=45)

            if period_label <= 2:
                ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
            elif period_label <= 5:
                ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
            elif period_label <= 10:
                ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
            elif period_label <= 25:
                ax.xaxis.set_major_locator(mdates.YearLocator(1))
            
            for abbr in fund_abbrs:
                plot_df = resdf[(resdf['abbr'] == abbr) & (resdf['start_date'] >= start_date)].copy()
                # if ky == 'annualized_roi':
                #     plot_df = plot_df[plot_df['start_date'] <= annualized_end_date]
                if plot_df.empty:
                    continue
                plot_df[ky] = plot_df[ky] * 100
                ax.plot(plot_df['start_date'], plot_df[ky], label=abbr, linewidth=1.5)

            plt.ylim(bottom=-15)
            ax.legend(loc=(ky == 'annualized_roi' and 'lower left' or 'upper right'), fontsize=10, frameon=False, ncols=3)
            ax.grid(True, linestyle=':', linewidth=1, color='#bfbfbf')
            sns.despine()

            plt.tight_layout(rect=[0, 0.03, 1, 0.95])
            plt.savefig(os.path.join(per_year_path, f'{withInflation and "inflation_" or "noinflation_"}{ky}_{period_label}.png'), bbox_inches='tight')
            plt.close(fig)

def visualize_per_fund(resdf, withInflation):
    pass

def read_result(path):
    df = pd.read_csv(os.path.join(data_path, path))
    df['start_date'] = pd.to_datetime(df['start_date'])
    df['roi'] = df['roi'].astype(float)
    df['annualized_roi'] = df['annualized_roi'].astype(float)
    return df

if __name__ == '__main__':
    # simulate_without_inflation()
    # simulate_with_inflation()
    visualize_per_year(read_result('simulate_without_inflation.csv'), False)
    # visualize_per_year(read_result('simulate_with_inflation.csv'), True)
