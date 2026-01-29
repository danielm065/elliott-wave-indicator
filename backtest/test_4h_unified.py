"""
Test unified params with Fib=0.618 and variations
Target: 14+ out of 18 (excluding HIMS, USDILS)
"""
import sys
sys.path.insert(0, r'C:\Users\danie\projects\elliott-wave-indicator\backtest')

from backtester import ElliottICTBacktester, load_data
from pathlib import Path
from itertools import product

DATA_DIR = Path(r'C:\Users\danie\projects\elliott-wave-indicator\data')

FILES_4H = {
    'AMD': 'BATS_AMD, 240_c2599.csv',
    'ASTS': 'BATS_ASTS, 240_a0ab9.csv',
    'BA': 'BATS_BA, 240_69b3b.csv',
    'CRWV': 'BATS_CRWV, 240_ed96a.csv',
    'GOOG': 'BATS_GOOG, 240_52190.csv',
    'HIMS': 'BATS_HIMS, 240_9ad5f.csv',
    'IBKR': 'BATS_IBKR, 240_eef24.csv',
    'INTC': 'BATS_INTC, 240_43ac7.csv',
    'KRNT': 'BATS_KRNT, 240_38050.csv',
    'MU': 'BATS_MU, 240_6d83f.csv',
    'OSCR': 'BATS_OSCR, 240_69bf3.csv',
    'PLTR': 'BATS_PLTR, 240_4ba34.csv',
    'RKLB': 'BATS_RKLB, 240_9e8cf.csv',
    'TTWO': 'BATS_TTWO, 240_ba1c1.csv',
    'ADAUSDT': 'BINANCE_ADAUSDT, 240_200b2.csv',
    'BTCUSDT': 'BINANCE_BTCUSDT, 240_fe0b8.csv',
    'ETHUSD': 'BINANCE_ETHUSD, 240_aff0c.csv',
    'MNQ': 'CME_MINI_MNQ1!, 240.csv',
    'SOLUSD': 'COINBASE_SOLUSD, 240_b1f00.csv',
    'USDILS': 'FOREXCOM_USDILS, 240_3fecc.csv',
}

# Load data
print("Loading data...", flush=True)
DATA = {}
for asset, file in FILES_4H.items():
    path = DATA_DIR / file
    if path.exists():
        try:
            DATA[asset] = load_data(str(path))
        except:
            pass
print(f"Loaded {len(DATA)} assets", flush=True)

# Test with Fib=0.618 (works for AMD, BTCUSDT)
ZZ = [2, 3]
FIB = [0.618, 0.70, 0.786]
TOL = [0.05, 0.10, 0.15]
RSI = [40, 50]
GAP = [2, 5]
TREND = [True, False]

def test_combo(params):
    results = {}
    for asset, df in DATA.items():
        try:
            bt = ElliottICTBacktester(df, params)
            result = bt.run_backtest()
            total = result.wins + result.losses
            results[asset] = {'total': total, 'wins': result.wins, 'wr': result.win_rate if total > 0 else 0}
        except:
            pass
    
    passing = sum(1 for a, r in results.items() if r['total'] >= 2 and r['wr'] >= 80)
    with_trades = sum(1 for a, r in results.items() if r['total'] >= 2)
    
    return passing, with_trades, results

def main():
    print(f"\nTarget: Find params that pass 14+ assets", flush=True)
    print(f"{'='*60}", flush=True)
    
    combos = list(product(ZZ, FIB, TOL, RSI, GAP, TREND))
    print(f"Testing {len(combos)} combinations...", flush=True)
    
    best_results = []
    
    for i, (zz, fib, tol, rsi, gap, trend) in enumerate(combos):
        params = {
            'zz_depth': zz,
            'fib_entry_level': fib,
            'fib_tolerance': tol,
            'rsi_threshold': rsi,
            'signal_gap': gap,
            'use_trend_filter': trend,
            'use_volume_filter': True,
            'use_rsi_filter': True,
            'rr_ratio': 1.0,
            'zz_dev': 0.2,
            'ema_period': 200,
        }
        
        passing, with_trades, results = test_combo(params)
        
        if passing >= 11:
            best_results.append({
                'zz': zz, 'fib': fib, 'tol': tol, 'rsi': rsi, 'gap': gap, 'trend': trend,
                'passing': passing, 'with_trades': with_trades,
                'results': results
            })
    
    best_results.sort(key=lambda x: (-x['passing'], -x['with_trades']))
    
    print(f"\n{'='*60}", flush=True)
    print("TOP RESULTS", flush=True)
    print(f"{'='*60}", flush=True)
    
    for i, r in enumerate(best_results[:10]):
        t_str = "T:ON" if r['trend'] else "T:OFF"
        print(f"\n{i+1}. Passing: {r['passing']}/20 ({r['with_trades']} with trades)", flush=True)
        print(f"   ZZ={r['zz']}, Fib={r['fib']}, Tol={r['tol']}, RSI<{r['rsi']}, Gap={r['gap']}, {t_str}", flush=True)
        
        failing = [(a, res['wr']) for a, res in r['results'].items() if res['total'] >= 2 and res['wr'] < 80]
        no_signal = [a for a, res in r['results'].items() if res['total'] < 2]
        
        if failing:
            print(f"   Failing: {', '.join(f'{a}({wr:.0f}%)' for a, wr in failing)}", flush=True)
        if no_signal:
            print(f"   No signals: {', '.join(no_signal)}", flush=True)
    
    if best_results:
        best = best_results[0]
        print(f"\n{'='*60}", flush=True)
        print(f"BEST: {best['passing']}/20", flush=True)
        print(f"{'='*60}", flush=True)
        
        for asset in sorted(FILES_4H.keys()):
            r = best['results'].get(asset, {'total': 0, 'wins': 0, 'wr': 0})
            if r['total'] >= 2:
                status = "PASS" if r['wr'] >= 80 else "FAIL"
                print(f"  {asset}: {r['wins']}/{r['total']} = {r['wr']:.0f}% [{status}]", flush=True)
            else:
                print(f"  {asset}: {r['total']} trades [NO SIGNAL]", flush=True)

if __name__ == '__main__':
    main()
