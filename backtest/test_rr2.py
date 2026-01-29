"""Test specifically with RR=2.0"""
import os
import sys
sys.path.append(os.path.dirname(__file__))

from backtester import ElliottICTBacktester, load_data
from itertools import product
import glob

DATA_DIR = r'C:\Users\danie\projects\elliott-wave-indicator\data'
ASSETS = ['GOOG', 'PLTR', 'MU', 'OSCR', 'RKLB', 'MNQ']

TF_MAP = {'1D': ['1D']}

def find_file(asset, tf):
    patterns = TF_MAP.get(tf, [tf])
    for f in glob.glob(os.path.join(DATA_DIR, '*.csv')):
        fname = os.path.basename(f).upper()
        if asset.upper() in fname and any(p.upper() in fname for p in patterns):
            return f
    return None

def load_all_data(tf):
    data = {}
    for asset in ASSETS:
        f = find_file(asset, tf)
        if f:
            data[asset] = load_data(f)
    return data

def test_params(data, params):
    ok = 0
    results = {}
    for asset, df in data.items():
        try:
            bt = ElliottICTBacktester(df, params)
            result = bt.run_backtest()
            wr = result.win_rate if (result.wins + result.losses) >= 2 else 0
            results[asset] = {'wr': wr, 'w': result.wins, 'l': result.losses}
            if wr >= 85:
                ok += 1
        except:
            results[asset] = {'wr': 0, 'w': 0, 'l': 0}
    return ok / len(data) * 100 if data else 0, results

print("Testing with RR=2.0 (target)")
print("="*60)

data = load_all_data('1D')

grid = {
    'zz_depth': [3, 4, 5, 6, 8],
    'zz_dev': [0.1, 0.3, 0.5],
    'signal_gap': [5, 10, 15],
    'fib_entry_level': [0.618, 0.70, 0.75, 0.786, 0.79],
}

fixed = {
    'rr_ratio': 2.0,  # Fixed at target
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
    cov, res = test_params(data, params)
    if cov > best_cov:
        best_cov = cov
        best_params = params.copy()
        best_results = res

print(f"\nBest with RR=2.0: {best_cov:.0f}% coverage")
print(f"Params: zz={best_params['zz_depth']}, dev={best_params['zz_dev']}, fib={best_params['fib_entry_level']}")
print("\nResults:")
for asset, r in best_results.items():
    status = "OK" if r['wr'] >= 85 else "FAIL"
    print(f"  {asset}: {r['w']}W/{r['l']}L = {r['wr']:.1f}% [{status}]")
