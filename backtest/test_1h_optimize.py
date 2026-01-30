"""
1H Timeframe Optimization
Target: 16/20 assets with 80%+ WR, RR >= 1.0
"""
import sys
sys.path.insert(0, r'C:\Users\danie\projects\elliott-wave-indicator\backtest')

from backtester import ElliottICTBacktester, load_data
from pathlib import Path
from itertools import product

DATA_DIR = Path(r'C:\Users\danie\projects\elliott-wave-indicator\data')

FILES_1H = {
    'AMD': 'BATS_AMD, 60_2853d.csv',
    'ASTS': 'BATS_ASTS, 60_360b6.csv',
    'BA': 'BATS_BA, 60_a5067.csv',
    'CRWV': 'BATS_CRWV, 60_58712.csv',
    'GOOG': 'BATS_GOOG, 60_78270.csv',
    'HIMS': 'BATS_HIMS, 60_ea867.csv',
    'IBKR': 'BATS_IBKR, 60_ebbaf.csv',
    'INTC': 'BATS_INTC, 60_59380.csv',
    'KRNT': 'BATS_KRNT, 60_f5a05.csv',
    'MU': 'BATS_MU, 60_609b8.csv',
    'OSCR': 'BATS_OSCR, 60_092fb.csv',
    'PLTR': 'BATS_PLTR, 60_14b34.csv',
    'RKLB': 'BATS_RKLB, 60_ae005.csv',
    'TTWO': 'BATS_TTWO, 60_73235.csv',
    'ADAUSDT': 'BINANCE_ADAUSDT, 60_ee9e1.csv',
    'BTCUSDT': 'BINANCE_BTCUSDT, 60_b6ebd.csv',
    'ETHUSD': 'BINANCE_ETHUSD, 60_b3215.csv',
    'MNQ': 'MNQ_1H.csv',
    'SOLUSD': 'COINBASE_SOLUSD, 60_49536.csv',
    'USDILS': 'FOREXCOM_USDILS, 60_14147.csv',
}

# Load data
print("Loading 1H data...", flush=True)
DATA = {}
for asset, file in FILES_1H.items():
    path = DATA_DIR / file
    if path.exists():
        try:
            DATA[asset] = load_data(str(path))
            print(f"  {asset}: {len(DATA[asset])} bars", flush=True)
        except Exception as e:
            print(f"  {asset}: Error - {e}", flush=True)
print(f"Loaded {len(DATA)} assets", flush=True)

# Parameter grid
ZZ = [2, 3, 4, 5]
FIB = [0.618, 0.70, 0.786]
TOL = [0.03, 0.05, 0.08, 0.10]
RSI = [35, 40, 45, 50]
GAP = [3, 5, 8, 10]
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
    print(f"\n{'='*70}", flush=True)
    print("1H OPTIMIZATION - Target: 16/20 with 80%+ WR", flush=True)
    print(f"{'='*70}", flush=True)
    
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
        
        if passing >= 12:
            best_results.append({
                'zz': zz, 'fib': fib, 'tol': tol, 'rsi': rsi, 'gap': gap, 'trend': trend,
                'passing': passing, 'with_trades': with_trades,
                'results': results
            })
        
        if (i + 1) % 200 == 0:
            print(f"  {i+1}/{len(combos)} tested...", flush=True)
    
    best_results.sort(key=lambda x: (-x['passing'], -x['with_trades']))
    
    print(f"\n{'='*70}", flush=True)
    print("TOP RESULTS", flush=True)
    print(f"{'='*70}", flush=True)
    
    for i, r in enumerate(best_results[:15]):
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
        print(f"\n{'='*70}", flush=True)
        print(f"BEST: {best['passing']}/20", flush=True)
        print(f"{'='*70}", flush=True)
        
        for asset in sorted(FILES_1H.keys()):
            r = best['results'].get(asset, {'total': 0, 'wins': 0, 'wr': 0})
            if r['total'] >= 2:
                status = "PASS" if r['wr'] >= 80 else "FAIL"
                print(f"  {asset}: {r['wins']}/{r['total']} = {r['wr']:.0f}% [{status}]", flush=True)
            else:
                print(f"  {asset}: {r['total']} trades [NO SIGNAL]", flush=True)

if __name__ == '__main__':
    main()
