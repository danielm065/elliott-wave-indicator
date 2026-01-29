"""Quick test remaining strategies"""
import os
import sys
sys.path.append(os.path.dirname(__file__))

from strategies.dynamic_tp import DynamicTPStrategy
from strategies.momentum import MomentumStrategy
from backtester import load_data
from itertools import product
import glob

DATA_DIR = r'C:\Users\danie\projects\elliott-wave-indicator\data'

def get_asset_name(filepath):
    fname = os.path.basename(filepath)
    for prefix in ['BATS_', 'BINANCE_', 'COINBASE_', 'FOREXCOM_']:
        if fname.startswith(prefix):
            return fname.split(',')[0].replace(prefix, '')
    if 'MNQ' in fname: return 'MNQ'
    if 'NQ' in fname: return 'NQ'
    return fname.split('_')[0]

files = glob.glob(os.path.join(DATA_DIR, '*1D*.csv'))
data = {}
for f in list(set(files)):
    asset = get_asset_name(f)
    try:
        data[asset] = load_data(f)
    except:
        pass

print(f"Testing on {len(data)} assets")

def test_strat(strat_class, params):
    ok, valid = 0, 0
    for df in data.values():
        try:
            result = strat_class(df, params).run_backtest()
            if result.wins + result.losses >= 2:
                valid += 1
                if result.win_rate >= 85:
                    ok += 1
        except:
            pass
    return ok, valid

# Dynamic TP - smaller grid
print("\n=== Dynamic TP ===")
best_cov, best_p = 0, None
for atr in [2.0, 3.0, 4.0]:
    for fib in [0.5, 0.618, 0.786]:
        for gap in [5, 10, 15]:
            p = {'signal_gap': gap, 'atr_mult': atr, 'fib_entry_level': fib}
            ok, valid = test_strat(DynamicTPStrategy, p)
            if valid >= 5:
                cov = ok/valid*100
                if cov > best_cov:
                    best_cov, best_p = cov, p
print(f"Best: {best_cov:.1f}% - {best_p}")

# Momentum - smaller grid
print("\n=== Momentum ===")
best_cov, best_p = 0, None
for rsi in [30, 35, 40]:
    for ema in [20, 50]:
        for gap in [5, 10, 15]:
            p = {'rr_ratio': 2.0, 'signal_gap': gap, 'rsi_oversold': rsi, 'ema_period': ema, 'lookback': 10}
            ok, valid = test_strat(MomentumStrategy, p)
            if valid >= 5:
                cov = ok/valid*100
                if cov > best_cov:
                    best_cov, best_p = cov, p
print(f"Best: {best_cov:.1f}% - {best_p}")

print("\n=== SUMMARY ===")
print("Breakout: 21.1% (best so far)")
print(f"Dynamic TP: {best_cov:.1f}%")
