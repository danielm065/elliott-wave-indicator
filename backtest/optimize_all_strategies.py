"""
Optimize ALL strategies on Daily with RR=2.0
Find best params for each strategy
"""
import os
import sys
sys.path.append(os.path.dirname(__file__))

from strategies.ict_pure import ICTPureStrategy
from strategies.breakout import BreakoutStrategy
from strategies.supply_demand import SupplyDemandStrategy
from strategies.dynamic_tp import DynamicTPStrategy
from strategies.momentum import MomentumStrategy
from backtester import load_data
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
    elif 'MNQ' in fname:
        return 'MNQ'
    elif 'NQ' in fname:
        return 'NQ'
    return fname.split('_')[0]

# Load all Daily data
files = glob.glob(os.path.join(DATA_DIR, '*1D*.csv'))
data = {}
for f in list(set(files)):
    asset = get_asset_name(f)
    try:
        data[asset] = load_data(f)
    except:
        pass

print(f"Loaded {len(data)} assets")

def test_strategy(strat_class, params, data):
    """Test strategy on all assets, return coverage"""
    ok = 0
    valid = 0
    
    for asset, df in data.items():
        try:
            strategy = strat_class(df, params)
            result = strategy.run_backtest()
            trades = result.wins + result.losses
            
            if trades >= 2:
                valid += 1
                if result.win_rate >= 85:
                    ok += 1
        except:
            pass
    
    return ok, valid

def optimize_strategy(name, strat_class, grid, fixed):
    """Find best params for a strategy"""
    print(f"\n{'='*60}")
    print(f"OPTIMIZING: {name}")
    print(f"{'='*60}")
    
    keys = list(grid.keys())
    values = [grid[k] for k in keys]
    total = 1
    for v in values:
        total *= len(v)
    
    print(f"Testing {total} combinations...")
    
    best_cov = 0
    best_params = None
    best_ok = 0
    best_valid = 0
    
    tested = 0
    for combo in product(*values):
        params = dict(zip(keys, combo))
        params.update(fixed)
        
        ok, valid = test_strategy(strat_class, params, data)
        
        if valid >= 5:
            cov = ok / valid * 100
            if cov > best_cov:
                best_cov = cov
                best_params = params.copy()
                best_ok = ok
                best_valid = valid
        
        tested += 1
        if tested % 200 == 0:
            print(f"  Progress: {tested}/{total} | Best: {best_cov:.0f}%")
    
    return {
        'name': name,
        'coverage': best_cov,
        'ok': best_ok,
        'valid': best_valid,
        'params': best_params
    }

# Strategy grids (all with RR=2.0 fixed)
STRATEGIES = [
    ('ICT Pure', ICTPureStrategy, {
        'signal_gap': [5, 10, 15, 20],
        'swing_depth': [3, 5, 8],
    }, {'rr_ratio': 2.0}),
    
    ('Breakout', BreakoutStrategy, {
        'signal_gap': [5, 10, 15, 20],
        'lookback': [10, 15, 20, 30],
    }, {'rr_ratio': 2.0}),
    
    ('Supply/Demand', SupplyDemandStrategy, {
        'signal_gap': [5, 10, 15, 20],
    }, {'rr_ratio': 2.0}),
    
    ('Dynamic TP', DynamicTPStrategy, {
        'signal_gap': [5, 10, 15, 20],
        'atr_mult': [2.0, 2.5, 3.0, 4.0, 5.0],
        'fib_entry_level': [0.5, 0.618, 0.70, 0.786],
    }, {}),  # No RR - uses ATR
    
    ('Momentum', MomentumStrategy, {
        'signal_gap': [5, 10, 15, 20],
        'rsi_oversold': [25, 30, 35, 40],
        'ema_period': [20, 50, 100],
        'lookback': [5, 10, 15],
    }, {'rr_ratio': 2.0}),
]

results = []

for name, strat_class, grid, fixed in STRATEGIES:
    result = optimize_strategy(name, strat_class, grid, fixed)
    results.append(result)
    
    print(f"\n  Best: {result['coverage']:.1f}% ({result['ok']}/{result['valid']})")
    if result['params']:
        print(f"  Params: {result['params']}")

# Summary
print("\n" + "="*70)
print("SUMMARY - OPTIMIZED STRATEGIES")
print("="*70)

for r in sorted(results, key=lambda x: -x['coverage']):
    status = "[BEST]" if r['coverage'] == max(x['coverage'] for x in results) else ""
    print(f"  {r['name']:15s}: {r['coverage']:5.1f}% ({r['ok']}/{r['valid']}) {status}")

best = max(results, key=lambda x: x['coverage'])
print(f"\nBest strategy: {best['name']} with {best['coverage']:.1f}% coverage")
print(f"Params: {best['params']}")
