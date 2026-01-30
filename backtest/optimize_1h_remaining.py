"""
Deep optimization for 1H timeframe - REMAINING 50%
"""
import sys
sys.path.insert(0, r'C:\Users\danie\projects\elliott-wave-indicator\backtest')

from backtester import ElliottICTBacktester, load_data
from pathlib import Path
from itertools import product
from multiprocessing import Pool, cpu_count

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

print("Loading 1H data...", flush=True)
DATA = {}
for asset, file in FILES_1H.items():
    path = DATA_DIR / file
    if path.exists():
        try:
            DATA[asset] = load_data(str(path))
        except:
            pass
print(f"Loaded {len(DATA)} assets", flush=True)

# Same grid as before
ZZ = [2, 3, 4, 5]
FIB = [0.5, 0.618, 0.705, 0.786, 0.85, 0.9]
TOL = [0.03, 0.05, 0.08, 0.10, 0.12, 0.15]
GAP = [3, 5, 7, 10]
RSI = [25, 30, 35, 40, 45, 50]
DEV = [0.1, 0.2, 0.3]
TREND = [True, False]
VOL = [True, False]

def test_combo(args):
    zz, fib, tol, gap, rsi, dev, trend, vol = args
    params = {
        'zz_depth': zz, 'fib_entry_level': fib, 'fib_tolerance': tol,
        'signal_gap': gap, 'rr_ratio': 1.0, 'zz_dev': dev,
        'use_rsi_filter': True, 'rsi_max': rsi,
        'use_trend_filter': trend, 'use_volume': vol,
    }
    
    results = {}
    for asset, df in DATA.items():
        try:
            bt = ElliottICTBacktester(df, params)
            result = bt.run_backtest()
            total = result.wins + result.losses
            results[asset] = {
                'total': total,
                'wins': result.wins,
                'wr': result.win_rate if total > 0 else 0
            }
        except:
            results[asset] = {'total': 0, 'wins': 0, 'wr': 0}
    
    passing = sum(1 for r in results.values() if r['total'] >= 2 and r['wr'] >= 80)
    return (passing, args, results)

if __name__ == '__main__':
    all_combos = list(product(ZZ, FIB, TOL, GAP, RSI, DEV, TREND, VOL))
    
    # Start from 50% (index 20736)
    start_idx = 21500
    combos = all_combos[start_idx:]
    
    print(f"Testing REMAINING {len(combos)} combinations (from {start_idx})...", flush=True)
    
    # Start with best known result
    best = {'passing': 12}
    
    with Pool(processes=cpu_count()) as pool:
        for i, (passing, args, results) in enumerate(pool.imap_unordered(test_combo, combos, chunksize=50)):
            if passing > best['passing']:
                zz, fib, tol, gap, rsi, dev, trend, vol = args
                best = {
                    'passing': passing, 'results': results,
                    'zz': zz, 'fib': fib, 'tol': tol, 'gap': gap,
                    'rsi': rsi, 'dev': dev, 'trend': trend, 'vol': vol
                }
                print(f"  NEW BEST: {passing}/20 - ZZ={zz}, Fib={fib}, Tol={tol}, RSI<{rsi}, Trend={trend}, Vol={vol}", flush=True)
            
            if (i+1) % 500 == 0:
                pct = (i+1)/len(combos)*100
                print(f"  Progress: {i+1}/{len(combos)} ({pct:.0f}%) - best: {best['passing']}/20", flush=True)
    
    print(f"\n{'='*70}", flush=True)
    print(f"FINAL 1H RESULT: {best['passing']}/20 ({best['passing']/20*100:.0f}%)", flush=True)
    if 'zz' in best:
        print(f"Parameters:", flush=True)
        print(f"  ZZ={best.get('zz')}, Fib={best.get('fib')}, Tol={best.get('tol')}, Gap={best.get('gap')}", flush=True)
        print(f"  RSI<{best.get('rsi')}, Dev={best.get('dev')}, Trend={best.get('trend')}, Vol={best.get('vol')}", flush=True)
    print(f"{'='*70}", flush=True)
    
    if 'results' in best:
        print("\nPer-asset results:", flush=True)
        passing_list = []
        failing_list = []
        for asset in sorted(FILES_1H.keys()):
            r = best['results'].get(asset, {'total': 0, 'wins': 0, 'wr': 0})
            if r['total'] >= 2:
                if r['wr'] >= 80:
                    passing_list.append(f"{asset}({r['wr']:.0f}%,n={r['total']})")
                else:
                    failing_list.append(f"{asset}({r['wr']:.0f}%,n={r['total']})")
            else:
                failing_list.append(f"{asset}(n={r['total']})")
        
        print(f"PASSING ({len(passing_list)}): {passing_list}", flush=True)
        print(f"FAILING ({len(failing_list)}): {failing_list}", flush=True)
