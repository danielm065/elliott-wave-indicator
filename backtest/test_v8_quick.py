"""
Quick test of v8 EMA Pullback strategy
"""
import sys
sys.path.insert(0, r'C:\Users\danie\projects\elliott-wave-indicator\backtest')

from backtester_v8_ema import EMAPullbackBacktester, load_data
from pathlib import Path

DATA_DIR = Path(r'C:\Users\danie\projects\elliott-wave-indicator\data')

# Test on a few assets first
FILES = {
    'GOOG': 'BATS_GOOG, 60_78270.csv',
    'PLTR': 'BATS_PLTR, 60_14b34.csv',
    'AMD': 'BATS_AMD, 60_2853d.csv',
    'BTCUSDT': 'BINANCE_BTCUSDT, 60_b6ebd.csv',
    'MNQ': 'MNQ_1H.csv',
    'ETHUSD': 'BINANCE_ETHUSD, 60_b3215.csv',
    'MU': 'BATS_MU, 60_609b8.csv',
    'CRWV': 'BATS_CRWV, 60_58712.csv',
}

print("Testing EMA Pullback Strategy (v8)...")
print("="*50)

for asset, file in FILES.items():
    path = DATA_DIR / file
    if not path.exists():
        print(f"{asset}: FILE NOT FOUND")
        continue
    
    df = load_data(str(path))
    
    # Test with different EMA combos
    best_wr = 0
    best_params = None
    
    for ema_fast in [10, 15, 20]:
        for ema_slow in [30, 50]:
            for rsi_min, rsi_max in [(30, 60), (25, 55), (35, 65)]:
                params = {
                    'ema_fast': ema_fast,
                    'ema_slow': ema_slow,
                    'swing_lookback': 10,
                    'signal_gap': 5,
                    'rr_ratio': 1.0,
                    'touch_tolerance': 0.003,
                    'bounce_candles': 1,
                    'use_rsi': True,
                    'rsi_min': rsi_min,
                    'rsi_max': rsi_max,
                }
                
                bt = EMAPullbackBacktester(df, params)
                result = bt.run_backtest()
                
                if result.total >= 2 and result.win_rate > best_wr:
                    best_wr = result.win_rate
                    best_params = (ema_fast, ema_slow, rsi_min, rsi_max, result.total)
    
    if best_params:
        status = "PASS" if best_wr >= 80 else "FAIL"
        print(f"{asset}: {best_wr:.0f}% (EMA {best_params[0]}/{best_params[1]}, RSI {best_params[2]}-{best_params[3]}, n={best_params[4]}) [{status}]")
    else:
        print(f"{asset}: NO SIGNAL")

print("="*50)
