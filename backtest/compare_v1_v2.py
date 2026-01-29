"""
Compare V1 vs V2 backtester results
"""
import sys
sys.path.insert(0, r'C:\Users\danie\projects\elliott-wave-indicator\backtest')

from backtester import ElliottICTBacktester, load_data as load_v1
from backtester_v2 import ElliottICTBacktesterV2, load_data as load_v2
from pathlib import Path

DATA_DIR = Path(r'C:\Users\danie\projects\elliott-wave-indicator\data')

# Test on a few assets
TEST_ASSETS = {
    'GOOG': 'BATS_GOOG, 240_52190.csv',
    'PLTR': 'BATS_PLTR, 240_4ba34.csv',
    'IBKR': 'BATS_IBKR, 240_eef24.csv',
}

PARAMS = {
    'zz_depth': 2,
    'rr_ratio': 1.0,
    'rsi_threshold': 40,
    'fib_tolerance': 0.10,
    'fib_entry_level': 0.786,
    'use_rsi_filter': True,
    'use_trend_filter': True,
    'ema_period': 200,
    'signal_gap': 5,
    'zz_dev': 0.2,
}

def main():
    print("Comparing V1 vs V2 backtester", flush=True)
    print("="*60, flush=True)
    
    for asset, file in TEST_ASSETS.items():
        path = DATA_DIR / file
        if not path.exists():
            continue
        
        print(f"\n{asset}:", flush=True)
        
        # V1
        df1 = load_v1(str(path))
        bt1 = ElliottICTBacktester(df1, PARAMS)
        r1 = bt1.run_backtest()
        
        print(f"  V1: {r1.wins}/{r1.wins+r1.losses} = {r1.win_rate:.0f}% ({r1.total} signals)", flush=True)
        
        # V2 (longs only)
        df2 = load_v2(str(path))
        params2 = {**PARAMS, 'enable_longs': True, 'enable_shorts': False, 'enable_fvg': False}
        bt2 = ElliottICTBacktesterV2(df2, params2)
        r2 = bt2.run_backtest()
        
        print(f"  V2: {r2.wins}/{r2.wins+r2.losses} = {r2.win_rate:.0f}% ({r2.total} signals)", flush=True)
        
        # Show V1 signal details
        print(f"  V1 signals:", flush=True)
        for s in r1.signals[-5:]:
            res = "WIN" if s.result == 1 else "LOSS" if s.result == -1 else "OPEN"
            print(f"    Bar {s.bar}: E={s.entry:.2f} TP={s.tp:.2f} SL={s.sl:.2f} -> {res}", flush=True)
        
        print(f"  V2 signals:", flush=True)
        for s in r2.signals[-5:]:
            res = "WIN" if s.result == 1 else "LOSS" if s.result == -1 else "OPEN"
            print(f"    Bar {s.bar}: E={s.entry:.2f} TP={s.tp:.2f} SL={s.sl:.2f} -> {res}", flush=True)

if __name__ == '__main__':
    main()
