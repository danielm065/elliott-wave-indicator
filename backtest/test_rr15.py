"""Test with RR=1.5"""
import os
import sys
sys.path.append(os.path.dirname(__file__))

from backtester import ElliottICTBacktester, load_data
from itertools import product
import glob

DATA_DIR = r'C:\Users\danie\projects\elliott-wave-indicator\data'
ASSETS = ['GOOG', 'PLTR', 'MU', 'OSCR', 'RKLB', 'MNQ']

def find_file(asset):
    for f in glob.glob(os.path.join(DATA_DIR, '*.csv')):
        fname = os.path.basename(f).upper()
        if asset.upper() in fname and '1D' in fname:
            return f
    return None

data = {}
for asset in ASSETS:
    f = find_file(asset)
    if f:
        data[asset] = load_data(f)

print("Testing with RR=1.5")
print("="*60)

grid = {
    'zz_depth': [3, 4, 5, 6, 8],
    'zz_dev': [0.1, 0.3, 0.5],
    'signal_gap': [5, 10, 15],
    'fib_entry_level': [0.618, 0.70, 0.75, 0.786, 0.79],
}

fixed = {
    'rr_ratio': 1.5,
    'use_trend_filter': True,
    'use_rsi_filter': True,
    'use_volume_filter': True,
    'ema_period': 200,
    'rsi_threshold': 50,
    'wave_retrace_min': 0.5,
    'wave_retrace_max': 0.786,
}

best_cov = 0
best_params = None
best_results = None

keys = list(grid.keys())
values = [grid[k] for k in keys]

for combo in product(*values):
    params = dict(zip(keys, combo))
    params.update(fixed)
    
    ok = 0
    results = {}
    for asset, df in data.items():
        bt = ElliottICTBacktester(df, params)
        result = bt.run_backtest()
        wr = result.win_rate if (result.wins + result.losses) >= 2 else 0
        results[asset] = {'wr': wr, 'w': result.wins, 'l': result.losses}
        if wr >= 85:
            ok += 1
    
    cov = ok / len(data) * 100
    if cov > best_cov:
        best_cov = cov
        best_params = params.copy()
        best_results = results

print(f"\nBest with RR=1.5: {best_cov:.0f}% coverage")
print(f"Params: zz={best_params['zz_depth']}, dev={best_params['zz_dev']}, fib={best_params['fib_entry_level']}")
print("\nResults:")
for asset, r in best_results.items():
    status = "OK" if r['wr'] >= 85 else "FAIL"
    print(f"  {asset}: {r['w']}W/{r['l']}L = {r['wr']:.1f}% [{status}]")
