"""
Test 4H with MINIMUM RR=1.0 (no lower!)
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

BASE = {
    'fib_entry_level': 0.786,
    'use_rsi_filter': True,
    'use_trend_filter': True,
    'use_volume_filter': True,
    'ema_period': 200,
    'zz_dev': 0.2,
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

# Grid with RR >= 1.0 ONLY
ZZ_VALUES = [2, 3, 4]
RR_VALUES = [1.0, 1.25, 1.5, 2.0]  # MINIMUM 1.0!
RSI_VALUES = [40, 45, 50, 55, 60]
TOL_VALUES = [0.10, 0.15, 0.20, 0.25, 0.30]
GAP_VALUES = [3, 5]

def test_combo(zz, rr, rsi, tol, gap):
    params = {**BASE, 'zz_depth': zz, 'rr_ratio': rr, 'rsi_threshold': rsi, 'fib_tolerance': tol, 'signal_gap': gap}
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
    print(f"\nSearching with RR >= 1.0 (MINIMUM)...", flush=True)
    
    combos = list(product(ZZ_VALUES, RR_VALUES, RSI_VALUES, TOL_VALUES, GAP_VALUES))
    print(f"Testing {len(combos)} combinations...", flush=True)
    
    best_results = []
    
    for i, (zz, rr, rsi, tol, gap) in enumerate(combos):
        passing, with_trades, results = test_combo(zz, rr, rsi, tol, gap)
        
        if passing >= 9:  # Track decent results
            best_results.append({
                'zz': zz, 'rr': rr, 'rsi': rsi, 'tol': tol, 'gap': gap,
                'passing': passing, 'with_trades': with_trades,
                'results': results
            })
        
        if (i + 1) % 100 == 0:
            print(f"  {i+1}/{len(combos)} tested...", flush=True)
    
    best_results.sort(key=lambda x: (-x['passing'], -x['with_trades']))
    
    print(f"\n{'='*70}", flush=True)
    print(f"TOP RESULTS (RR >= 1.0)", flush=True)
    print(f"{'='*70}", flush=True)
    
    for i, r in enumerate(best_results[:10]):
        print(f"\n{i+1}. Passing: {r['passing']}/20 ({r['with_trades']} with trades)", flush=True)
        print(f"   ZZ={r['zz']}, RR={r['rr']}, RSI<{r['rsi']}, Tol={r['tol']}, Gap={r['gap']}", flush=True)
        
        failing = [(a, res['wr']) for a, res in r['results'].items() if res['total'] >= 2 and res['wr'] < 80]
        no_signal = [a for a, res in r['results'].items() if res['total'] < 2]
        
        if failing:
            print(f"   Failing: {', '.join(f'{a}({wr:.0f}%)' for a, wr in failing)}", flush=True)
        if no_signal:
            print(f"   No signals: {', '.join(no_signal)}", flush=True)
    
    # Best result details
    if best_results:
        best = best_results[0]
        print(f"\n{'='*70}", flush=True)
        print(f"BEST: {best['passing']}/20 with RR={best['rr']}", flush=True)
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
