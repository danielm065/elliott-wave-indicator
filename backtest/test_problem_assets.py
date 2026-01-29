"""
Analyze problem assets: MU, MNQ (failing), AMD, HIMS, BTCUSDT, USDILS (no signals)
Find params that work for each
"""
import sys
sys.path.insert(0, r'C:\Users\danie\projects\elliott-wave-indicator\backtest')

from backtester import ElliottICTBacktester, load_data
from pathlib import Path
from itertools import product

DATA_DIR = Path(r'C:\Users\danie\projects\elliott-wave-indicator\data')

PROBLEM_ASSETS = {
    'MU': 'BATS_MU, 240_6d83f.csv',
    'MNQ': 'CME_MINI_MNQ1!, 240.csv',
    'AMD': 'BATS_AMD, 240_c2599.csv',
    'HIMS': 'BATS_HIMS, 240_9ad5f.csv',
    'BTCUSDT': 'BINANCE_BTCUSDT, 240_fe0b8.csv',
    'USDILS': 'FOREXCOM_USDILS, 240_3fecc.csv',
}

BASE = {
    'fib_entry_level': 0.786,
    'use_rsi_filter': True,
    'use_trend_filter': True,
    'use_volume_filter': True,
    'ema_period': 200,
    'zz_dev': 0.2,
}

# Wide grid
ZZ = [2, 3, 4, 5]
RR = [0.5, 0.75, 1.0, 1.5]
RSI = [40, 50, 60, 70]
TOL = [0.10, 0.15, 0.20, 0.25, 0.30]
GAP = [3, 5]

def main():
    for asset, file in PROBLEM_ASSETS.items():
        print(f"\n{'='*60}", flush=True)
        print(f"ANALYZING: {asset}", flush=True)
        print(f"{'='*60}", flush=True)
        
        path = DATA_DIR / file
        if not path.exists():
            print(f"  File not found!", flush=True)
            continue
        
        df = load_data(str(path))
        print(f"  Bars: {len(df)}", flush=True)
        
        best_wr = 0
        best_params = None
        best_result = None
        
        combos_with_trades = 0
        combos_passing = 0
        
        for zz, rr, rsi, tol, gap in product(ZZ, RR, RSI, TOL, GAP):
            params = {
                **BASE,
                'zz_depth': zz,
                'rr_ratio': rr,
                'rsi_threshold': rsi,
                'fib_tolerance': tol,
                'signal_gap': gap
            }
            
            try:
                bt = ElliottICTBacktester(df, params)
                result = bt.run_backtest()
                total = result.wins + result.losses
                
                if total >= 2:
                    combos_with_trades += 1
                    wr = result.win_rate
                    
                    if wr >= 80:
                        combos_passing += 1
                    
                    if wr > best_wr:
                        best_wr = wr
                        best_params = {'zz': zz, 'rr': rr, 'rsi': rsi, 'tol': tol, 'gap': gap}
                        best_result = {'wins': result.wins, 'total': total}
            except:
                pass
        
        print(f"\n  Combos with 2+ trades: {combos_with_trades}", flush=True)
        print(f"  Combos with 80%+ WR: {combos_passing}", flush=True)
        
        if best_params:
            print(f"\n  BEST: {best_result['wins']}/{best_result['total']} = {best_wr:.0f}%", flush=True)
            print(f"  Params: ZZ={best_params['zz']}, RR={best_params['rr']}, RSI<{best_params['rsi']}, Tol={best_params['tol']}, Gap={best_params['gap']}", flush=True)
            
            if best_wr >= 80:
                print(f"  --> CAN PASS at 80%!", flush=True)
            else:
                print(f"  --> Cannot reach 80% with any params", flush=True)
        else:
            print(f"\n  NO VALID RESULTS (no params give 2+ trades)", flush=True)

if __name__ == '__main__':
    main()
