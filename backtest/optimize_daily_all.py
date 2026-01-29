"""
Find best params for ALL Daily assets with RR=2.0
Target: 85% WR on 90% of assets
"""
import os
import sys
sys.path.append(os.path.dirname(__file__))

from backtester import ElliottICTBacktester, load_data
from itertools import product
import glob

DATA_DIR = r'C:\Users\danie\projects\elliott-wave-indicator\data'

def get_asset_name(filepath):
    fname = os.path.basename(filepath)
    if fname.startswith('BATS_'):
        return fname.split(',')[0].replace('BATS_', '')
    elif fname.startswith('BINANCE_'):
        return fname.split(',')[0].replace('BINANCE_', '')
    elif fname.startswith('COINBASE_'):
        return fname.split(',')[0].replace('COINBASE_', '')
    elif fname.startswith('FOREXCOM_'):
        return fname.split(',')[0].replace('FOREXCOM_', '')
    elif fname.startswith('MNQ'):
        return 'MNQ'
    elif fname.startswith('NQ'):
        return 'NQ'
    return fname.split('_')[0]

# Load all Daily data
files = glob.glob(os.path.join(DATA_DIR, '*1D*.csv'))
files = list(set(files))

data = {}
for f in files:
    asset = get_asset_name(f)
    try:
        data[asset] = load_data(f)
    except:
        pass

print("="*70)
print("OPTIMIZING DAILY - ALL ASSETS WITH RR=2.0")
print("="*70)
print(f"Loaded {len(data)} assets: {sorted(data.keys())}")

# Search grid
grid = {
    'zz_depth': [2, 3, 4, 5, 6, 8],
    'zz_dev': [0.05, 0.1, 0.3, 0.5],
    'signal_gap': [3, 5, 8, 10],
    'fib_entry_level': [0.5, 0.618, 0.70, 0.75, 0.786, 0.79],
    'use_trend_filter': [True, False],
    'use_rsi_filter': [True, False],
}

fixed = {
    'rr_ratio': 2.0,
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

tested = 0
for combo in product(*values):
    params = dict(zip(keys, combo))
    params.update(fixed)
    
    ok = 0
    valid = 0
    results = {}
    
    for asset, df in data.items():
        try:
            bt = ElliottICTBacktester(df, params)
            result = bt.run_backtest()
            trades = result.wins + result.losses
            
            if trades >= 2:
                valid += 1
                wr = result.win_rate
                results[asset] = {'wr': wr, 'w': result.wins, 'l': result.losses}
                if wr >= 85:
                    ok += 1
        except:
            pass
    
    if valid >= 10:  # Need at least 10 valid assets
        cov = ok / valid * 100
        if cov > best_cov:
            best_cov = cov
            best_params = params.copy()
            best_results = results.copy()
    
    tested += 1
    if tested % 500 == 0:
        print(f"Progress: {tested}/{total} | Best: {best_cov:.0f}%")

print()
print("="*70)
print("BEST RESULT")
print("="*70)
print(f"Coverage: {best_cov:.0f}%")
print(f"Params:")
print(f"  zz_depth: {best_params['zz_depth']}")
print(f"  zz_dev: {best_params['zz_dev']}")
print(f"  signal_gap: {best_params['signal_gap']}")
print(f"  fib_entry: {best_params['fib_entry_level']}")
print(f"  trend_filter: {best_params['use_trend_filter']}")
print(f"  rsi_filter: {best_params['use_rsi_filter']}")

print(f"\nResults per asset:")
for asset in sorted(best_results.keys()):
    r = best_results[asset]
    status = "OK" if r['wr'] >= 85 else "FAIL"
    print(f"  {asset:12s}: {r['w']:2d}W/{r['l']:2d}L = {r['wr']:5.1f}% [{status}]")

ok_count = sum(1 for r in best_results.values() if r['wr'] >= 85)
fail_count = sum(1 for r in best_results.values() if r['wr'] < 85)
print(f"\nPassing: {ok_count}, Failing: {fail_count}")
