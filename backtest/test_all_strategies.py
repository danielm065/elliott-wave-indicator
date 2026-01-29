"""
Test ALL strategies on Daily with RR=2.0
"""
import os
import sys
sys.path.append(os.path.dirname(__file__))

from strategies.base import BaseStrategy
from strategies.ict_pure import ICTPureStrategy
from strategies.breakout import BreakoutStrategy
from strategies.supply_demand import SupplyDemandStrategy
from strategies.dynamic_tp import DynamicTPStrategy
from strategies.momentum import MomentumStrategy
from backtester import load_data
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
print("TESTING ALL STRATEGIES ON DAILY (RR=2.0)")
print("="*70)
print(f"Assets: {len(data)}")

STRATEGIES = {
    'ICT Pure': (ICTPureStrategy, {'rr_ratio': 2.0, 'signal_gap': 10, 'swing_depth': 5}),
    'Breakout': (BreakoutStrategy, {'rr_ratio': 2.0, 'signal_gap': 10, 'lookback': 20}),
    'Supply/Demand': (SupplyDemandStrategy, {'rr_ratio': 2.0, 'signal_gap': 10}),
    'Dynamic TP': (DynamicTPStrategy, {'signal_gap': 10, 'atr_mult': 3.0, 'fib_entry_level': 0.618}),
    'Momentum': (MomentumStrategy, {'rr_ratio': 2.0, 'signal_gap': 10, 'rsi_oversold': 35, 'ema_period': 50}),
}

results = {}

for strat_name, (strat_class, params) in STRATEGIES.items():
    print(f"\n{'='*60}")
    print(f"TESTING: {strat_name}")
    print(f"{'='*60}")
    
    strat_results = {}
    
    for asset, df in data.items():
        try:
            strategy = strat_class(df, params)
            result = strategy.run_backtest()
            
            trades = result.wins + result.losses
            if trades >= 2:
                wr = result.win_rate
                status = "OK" if wr >= 85 else "FAIL"
                strat_results[asset] = {'wr': wr, 'w': result.wins, 'l': result.losses, 'status': status}
                print(f"  {asset:12s}: {result.wins:2d}W/{result.losses:2d}L = {wr:5.1f}% [{status}]")
            else:
                print(f"  {asset:12s}: {result.wins:2d}W/{result.losses:2d}L = FEW trades")
        except Exception as e:
            print(f"  {asset:12s}: ERROR - {e}")
    
    # Calculate coverage
    valid = [r for r in strat_results.values()]
    ok = sum(1 for r in valid if r['status'] == 'OK')
    total = len(valid)
    coverage = ok / total * 100 if total > 0 else 0
    
    results[strat_name] = {'coverage': coverage, 'ok': ok, 'total': total, 'details': strat_results}
    
    print(f"\n  Coverage: {ok}/{total} = {coverage:.0f}%")

# Summary
print("\n" + "="*70)
print("SUMMARY - ALL STRATEGIES")
print("="*70)

for name, res in sorted(results.items(), key=lambda x: -x[1]['coverage']):
    status = "[BEST]" if res['coverage'] == max(r['coverage'] for r in results.values()) else ""
    print(f"  {name:15s}: {res['coverage']:5.1f}% ({res['ok']}/{res['total']}) {status}")

# Best strategy details
best_name = max(results.keys(), key=lambda k: results[k]['coverage'])
print(f"\n{'='*70}")
print(f"BEST STRATEGY: {best_name}")
print(f"{'='*70}")

best = results[best_name]
print(f"Coverage: {best['coverage']:.1f}%")
print("\nPassing assets:")
for asset, r in best['details'].items():
    if r['status'] == 'OK':
        print(f"  {asset}: {r['wr']:.1f}%")

print("\nFailing assets:")
for asset, r in best['details'].items():
    if r['status'] == 'FAIL':
        print(f"  {asset}: {r['wr']:.1f}%")
