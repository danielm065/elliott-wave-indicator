"""
Analyze why AMD, HIMS, BTCUSDT, USDILS have no signals
Try to find params that generate signals for them
"""
import sys
sys.path.insert(0, r'C:\Users\danie\projects\elliott-wave-indicator\backtest')

from backtester import ElliottICTBacktester, load_data
from pathlib import Path
from itertools import product

DATA_DIR = Path(r'C:\Users\danie\projects\elliott-wave-indicator\data')

NO_SIGNAL_ASSETS = {
    'AMD': 'BATS_AMD, 240_c2599.csv',
    'HIMS': 'BATS_HIMS, 240_9ad5f.csv',
    'BTCUSDT': 'BINANCE_BTCUSDT, 240_fe0b8.csv',
    'USDILS': 'FOREXCOM_USDILS, 240_3fecc.csv',
}

# Aggressive params to generate more signals
ZZ = [2, 3, 4]
RSI = [40, 50, 60, 70, 80]
TOL = [0.05, 0.10, 0.15, 0.20, 0.30, 0.40]
FIB = [0.50, 0.618, 0.70, 0.786, 0.85]
GAP = [2, 3, 5]
TREND = [True, False]
VOLUME = [True, False]

BASE = {
    'rr_ratio': 1.0,
    'zz_dev': 0.2,
    'ema_period': 200,
    'use_rsi_filter': True,
}

def find_signals(asset, file):
    path = DATA_DIR / file
    if not path.exists():
        return None
    
    df = load_data(str(path))
    print(f"\n{'='*60}", flush=True)
    print(f"Analyzing: {asset} ({len(df)} bars)", flush=True)
    print(f"{'='*60}", flush=True)
    
    best = {'signals': 0, 'wins': 0, 'wr': 0, 'params': None}
    
    for zz, rsi, tol, fib, gap, trend, vol in product(ZZ, RSI, TOL, FIB, GAP, TREND, VOLUME):
        params = {
            **BASE,
            'zz_depth': zz,
            'rsi_threshold': rsi,
            'fib_tolerance': tol,
            'fib_entry_level': fib,
            'signal_gap': gap,
            'use_trend_filter': trend,
            'use_volume_filter': vol,
        }
        
        try:
            bt = ElliottICTBacktester(df, params)
            result = bt.run_backtest()
            total = result.wins + result.losses
            
            if total >= 2 and result.win_rate >= 80:
                if total > best['signals'] or (total == best['signals'] and result.win_rate > best['wr']):
                    best = {
                        'signals': total,
                        'wins': result.wins,
                        'wr': result.win_rate,
                        'params': {
                            'zz': zz, 'rsi': rsi, 'tol': tol, 'fib': fib, 
                            'gap': gap, 'trend': trend, 'vol': vol
                        }
                    }
        except:
            pass
    
    if best['params']:
        p = best['params']
        print(f"FOUND: {best['wins']}/{best['signals']} = {best['wr']:.0f}%", flush=True)
        print(f"  ZZ={p['zz']}, RSI<{p['rsi']}, Tol={p['tol']}, Fib={p['fib']}", flush=True)
        print(f"  Gap={p['gap']}, Trend={p['trend']}, Vol={p['vol']}", flush=True)
        return best
    else:
        # Find any params that generate signals
        print("No params with 80%+ WR found. Checking for any signals...", flush=True)
        for zz in [2, 3]:
            for trend in [True, False]:
                for tol in [0.30, 0.40]:
                    params = {
                        **BASE,
                        'zz_depth': zz,
                        'rsi_threshold': 80,
                        'fib_tolerance': tol,
                        'fib_entry_level': 0.618,
                        'signal_gap': 2,
                        'use_trend_filter': trend,
                        'use_volume_filter': False,
                    }
                    try:
                        bt = ElliottICTBacktester(df, params)
                        result = bt.run_backtest()
                        if result.total > 0:
                            print(f"  With ZZ={zz}, Trend={trend}, Tol={tol}: {result.wins}/{result.wins+result.losses} = {result.win_rate:.0f}%", flush=True)
                    except:
                        pass
        return None

def main():
    results = {}
    for asset, file in NO_SIGNAL_ASSETS.items():
        results[asset] = find_signals(asset, file)
    
    print(f"\n{'='*60}", flush=True)
    print("SUMMARY", flush=True)
    print(f"{'='*60}", flush=True)
    
    for asset, r in results.items():
        if r:
            print(f"{asset}: CAN PASS with custom params ({r['wins']}/{r['signals']} = {r['wr']:.0f}%)", flush=True)
        else:
            print(f"{asset}: Cannot achieve 80% with any tested params", flush=True)

if __name__ == '__main__':
    main()
