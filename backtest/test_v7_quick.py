"""
Quick test of v7 Breakout + Pullback strategy
"""
import sys
sys.path.insert(0, r'C:\Users\danie\projects\elliott-wave-indicator\backtest')

from backtester_v7_breakout import BreakoutPullbackBacktester, load_data
from pathlib import Path

DATA_DIR = Path(r'C:\Users\danie\projects\elliott-wave-indicator\data')

# Test on a few assets first
FILES = {
    'GOOG': 'BATS_GOOG, 60_78270.csv',
    'PLTR': 'BATS_PLTR, 60_14b34.csv',
    'AMD': 'BATS_AMD, 60_2853d.csv',
    'BTCUSDT': 'BINANCE_BTCUSDT, 60_b6ebd.csv',
    'MNQ': 'MNQ_1H.csv',
}

print("Testing Breakout + Pullback Strategy (v7)...")
print("="*50)

for asset, file in FILES.items():
    path = DATA_DIR / file
    if not path.exists():
        print(f"{asset}: FILE NOT FOUND")
        continue
    
    df = load_data(str(path))
    
    # Test with default params
    params = {
        'lookback': 15,
        'pullback_pct': 0.4,
        'max_pullback_pct': 0.9,
        'signal_gap': 5,
        'rr_ratio': 1.0,
        'use_volume_confirm': False,  # Disable for now
        'use_ema_filter': True,
        'ema_period': 50,
    }
    
    bt = BreakoutPullbackBacktester(df, params)
    result = bt.run_backtest()
    
    if result.total >= 2:
        status = "PASS" if result.win_rate >= 80 else "FAIL"
        print(f"{asset}: {result.wins}/{result.total} = {result.win_rate:.0f}% [{status}]")
    else:
        print(f"{asset}: {result.total} trades [NO SIGNAL]")

print("="*50)
print("If this looks promising, will run full grid search")
