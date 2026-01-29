"""
Test different params specifically on failing assets
"""
import sys
sys.path.insert(0, r'C:\Users\danie\projects\elliott-wave-indicator\backtest')

from backtester import ElliottICTBacktester, load_data
from pathlib import Path
from itertools import product

DATA_DIR = Path(r'C:\Users\danie\projects\elliott-wave-indicator\data')

FAILING_ASSETS = {
    'GOOG': 'BATS_GOOG, 240_52190.csv',
    'PLTR': 'BATS_PLTR, 240_4ba34.csv',
    'ADAUSDT': 'BINANCE_ADAUSDT, 240_200b2.csv',
}

BASE = {
    'fib_entry_level': 0.786,
    'use_rsi_filter': True,
    'use_trend_filter': True,
    'use_volume_filter': True,
    'ema_period': 200,
    'signal_gap': 5,
    'zz_dev': 0.2,
}

# Parameter grid
ZZ_VALUES = [3, 4, 5, 6, 7, 8]
RR_VALUES = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0]
RSI_VALUES = [35, 40, 45, 50, 55, 60]
TOL_VALUES = [0.10, 0.15, 0.20, 0.25, 0.30]

def test_asset(asset, file, params):
    path = DATA_DIR / file
    if not path.exists():
        return None
    try:
        df = load_data(str(path))
        bt = ElliottICTBacktester(df, params)
        result = bt.run_backtest()
        return {
            'total': result.wins + result.losses,
            'wins': result.wins,
            'wr': result.win_rate
        }
    except:
        return None

def main():
    for asset, file in FAILING_ASSETS.items():
        print("="*60)
        print(f"OPTIMIZING: {asset}")
        print("="*60)
        
        best_wr = 0
        best_params = None
        best_trades = 0
        
        combos = list(product(ZZ_VALUES, RR_VALUES, RSI_VALUES, TOL_VALUES))
        print(f"Testing {len(combos)} combinations...")
        
        for zz, rr, rsi, tol in combos:
            params = {
                **BASE,
                'zz_depth': zz,
                'rr_ratio': rr,
                'rsi_threshold': rsi,
                'fib_tolerance': tol,
            }
            
            result = test_asset(asset, file, params)
            if result and result['total'] >= 2:
                if result['wr'] > best_wr or (result['wr'] == best_wr and result['total'] > best_trades):
                    best_wr = result['wr']
                    best_trades = result['total']
                    best_params = {'zz': zz, 'rr': rr, 'rsi': rsi, 'tol': tol}
        
        if best_params:
            print(f"\nBest for {asset}:")
            print(f"  Win Rate: {best_wr:.0f}% ({best_trades} trades)")
            print(f"  Params: ZZ={best_params['zz']}, RR={best_params['rr']}, RSI<{best_params['rsi']}, Tol={best_params['tol']}")
        else:
            print(f"\nNo valid result for {asset}")
        
        # Also show top 5 combinations with 85%+ WR
        print(f"\nAll combinations with 85%+ WR and 2+ trades:")
        good_combos = []
        for zz, rr, rsi, tol in combos:
            params = {
                **BASE,
                'zz_depth': zz,
                'rr_ratio': rr,
                'rsi_threshold': rsi,
                'fib_tolerance': tol,
            }
            result = test_asset(asset, file, params)
            if result and result['total'] >= 2 and result['wr'] >= 85:
                good_combos.append({
                    'zz': zz, 'rr': rr, 'rsi': rsi, 'tol': tol,
                    'wr': result['wr'], 'trades': result['total']
                })
        
        if good_combos:
            good_combos.sort(key=lambda x: (-x['wr'], -x['trades']))
            for c in good_combos[:10]:
                print(f"  ZZ={c['zz']}, RR={c['rr']}, RSI<{c['rsi']}, Tol={c['tol']} -> {c['wr']:.0f}% ({c['trades']} trades)")
        else:
            print("  NONE - no params achieve 85% with 2+ trades")
        
        print()

if __name__ == '__main__':
    main()
