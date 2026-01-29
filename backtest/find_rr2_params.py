"""
Deep search for params that work with RR=2.0
Target: 85% win rate on 90% of assets (at least 5/6)
"""
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

# Load all data
data = {}
for asset in ASSETS:
    f = find_file(asset)
    if f:
        data[asset] = load_data(f)

print("="*60)
print("DEEP SEARCH: RR=2.0 on Daily")
print("Target: 85% WR on 90% of assets (5/6)")
print("="*60)

# Wider grid search
grid = {
    'zz_depth': [2, 3, 4, 5, 6, 8, 10],
    'zz_dev': [0.05, 0.1, 0.2, 0.3, 0.5, 1.0],
    'signal_gap': [3, 5, 8, 10, 15, 20],
    'fib_entry_level': [0.5, 0.55, 0.618, 0.65, 0.70, 0.75, 0.786, 0.79, 0.85],
    'use_trend_filter': [True, False],
    'use_rsi_filter': [True, False],
}

fixed = {
    'rr_ratio': 2.0,  # FIXED at target
    'use_volume_filter': True,
    'ema_period': 200,
    'rsi_threshold': 50,
    'wave_retrace_min': 0.5,
    'wave_retrace_max': 0.786,
}

keys = list(grid.keys())
values = [grid[k] for k in keys]
total = 1
for v in values:
    total *= len(v)

print(f"Testing {total} combinations...")

best_cov = 0
best_params = None
best_results = None
candidates_90 = []  # 90%+ coverage (5/6)
candidates_83 = []  # 83%+ coverage (5/6)

tested = 0
for combo in product(*values):
    params = dict(zip(keys, combo))
    params.update(fixed)
    
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
    
    cov = ok / len(data) * 100
    
    if cov >= 83:
        candidates_83.append({'params': params.copy(), 'cov': cov, 'results': results.copy()})
    if cov >= 90:
        candidates_90.append({'params': params.copy(), 'cov': cov, 'results': results.copy()})
    
    if cov > best_cov:
        best_cov = cov
        best_params = params.copy()
        best_results = results.copy()
    
    tested += 1
    if tested % 5000 == 0:
        print(f"Progress: {tested}/{total} | Best: {best_cov:.0f}%")

print(f"\n{'='*60}")
print(f"RESULTS")
print(f"{'='*60}")

if candidates_90:
    print(f"\n[SUCCESS] Found {len(candidates_90)} params with 90%+ coverage!")
    for c in candidates_90[:3]:
        p = c['params']
        print(f"\n  Coverage: {c['cov']:.0f}%")
        print(f"  zz={p['zz_depth']}, dev={p['zz_dev']}, gap={p['signal_gap']}, fib={p['fib_entry_level']}")
        print(f"  trend={p['use_trend_filter']}, rsi={p['use_rsi_filter']}")
        for asset, r in c['results'].items():
            status = "OK" if r['wr'] >= 85 else "FAIL"
            print(f"    {asset}: {r['w']}W/{r['l']}L = {r['wr']:.1f}% [{status}]")
else:
    print(f"\n[FAIL] No params found with 90%+ coverage")
    print(f"Best achieved: {best_cov:.0f}%")
    print(f"\nBest params:")
    print(f"  zz={best_params['zz_depth']}, dev={best_params['zz_dev']}, gap={best_params['signal_gap']}, fib={best_params['fib_entry_level']}")
    print(f"  trend={best_params['use_trend_filter']}, rsi={best_params['use_rsi_filter']}")
    print(f"\nResults:")
    for asset, r in best_results.items():
        status = "OK" if r['wr'] >= 85 else "FAIL"
        print(f"  {asset}: {r['w']}W/{r['l']}L = {r['wr']:.1f}% [{status}]")

if candidates_83 and not candidates_90:
    print(f"\n{len(candidates_83)} params with 83%+ coverage (close but not 90%)")
