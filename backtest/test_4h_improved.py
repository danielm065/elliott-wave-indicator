"""
Test improved strategy variations to reach 16/20
Try different Fib levels, wave patterns, filters
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

# Extended parameter grid with more Fib options
ZZ_VALUES = [2, 3]
RR_VALUES = [1.0, 1.5]  # Min 1.0!
RSI_VALUES = [40, 50, 60]
TOL_VALUES = [0.10, 0.15, 0.20, 0.25]
FIB_ENTRY = [0.618, 0.70, 0.786, 0.85]  # Different Fib levels
TREND_FILTER = [True, False]
VOLUME_FILTER = [True, False]

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
    print(f"\nTesting improved strategy variations...", flush=True)
    print(f"Target: 16/20 assets above 80% WR with RR >= 1.0", flush=True)
    
    combos = list(product(ZZ_VALUES, RR_VALUES, RSI_VALUES, TOL_VALUES, FIB_ENTRY, TREND_FILTER, VOLUME_FILTER))
    print(f"Testing {len(combos)} combinations...", flush=True)
    
    best_results = []
    
    for i, (zz, rr, rsi, tol, fib, trend, vol) in enumerate(combos):
        params = {
            'zz_depth': zz,
            'rr_ratio': rr,
            'rsi_threshold': rsi,
            'fib_tolerance': tol,
            'fib_entry_level': fib,
            'use_rsi_filter': True,
            'use_trend_filter': trend,
            'use_volume_filter': vol,
            'ema_period': 200,
            'signal_gap': 5,
            'zz_dev': 0.2,
        }
        
        passing, with_trades, results = test_combo(params)
        
        if passing >= 12:
            best_results.append({
                'zz': zz, 'rr': rr, 'rsi': rsi, 'tol': tol, 'fib': fib,
                'trend': trend, 'vol': vol,
                'passing': passing, 'with_trades': with_trades,
                'results': results
            })
        
        if (i + 1) % 100 == 0:
            print(f"  {i+1}/{len(combos)} tested...", flush=True)
    
    best_results.sort(key=lambda x: (-x['passing'], -x['with_trades']))
    
    print(f"\n{'='*70}", flush=True)
    print(f"TOP RESULTS", flush=True)
    print(f"{'='*70}", flush=True)
    
    for i, r in enumerate(best_results[:15]):
        t_str = "T:ON" if r['trend'] else "T:OFF"
        v_str = "V:ON" if r['vol'] else "V:OFF"
        print(f"\n{i+1}. Passing: {r['passing']}/20 ({r['with_trades']} with trades)", flush=True)
        print(f"   ZZ={r['zz']}, RR={r['rr']}, RSI<{r['rsi']}, Tol={r['tol']}, Fib={r['fib']}, {t_str}, {v_str}", flush=True)
        
        failing = [(a, res['wr']) for a, res in r['results'].items() if res['total'] >= 2 and res['wr'] < 80]
        no_signal = [a for a, res in r['results'].items() if res['total'] < 2]
        
        if failing:
            print(f"   Failing: {', '.join(f'{a}({wr:.0f}%)' for a, wr in failing)}", flush=True)
        if no_signal:
            print(f"   No signals: {', '.join(no_signal)}", flush=True)
    
    if best_results:
        best = best_results[0]
        print(f"\n{'='*70}", flush=True)
        print(f"BEST: {best['passing']}/20", flush=True)
        print(f"{'='*70}", flush=True)
        
        for asset in sorted(FILES_4H.keys()):
            r = best['results'].get(asset, {'total': 0, 'wins': 0, 'wr': 0})
            if r['total'] >= 2:
                status = "PASS" if r['wr'] >= 80 else "FAIL"
                print(f"  {asset}: {r['wins']}/{r['total']} = {r['wr']:.0f}% [{status}]", flush=True)
            else:
                print(f"  {asset}: {r['total']} trades [NO SIGNAL]", flush=True)

if __name__ == '__main__':
    main()
