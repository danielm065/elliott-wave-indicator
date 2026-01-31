"""
Deep optimization for 30m timeframe
Based on lessons learned from 1H optimization
"""
import sys
sys.path.insert(0, r'C:\Users\danie\projects\elliott-wave-indicator\backtest')

from backtester import ElliottICTBacktester, load_data
from pathlib import Path
from itertools import product
from multiprocessing import Pool, cpu_count

DATA_DIR = Path(r'C:\Users\danie\projects\elliott-wave-indicator\data')

# 30m files
FILES_30M = {
    'AMD': 'BATS_AMD, 30_d8cd3.csv',
    'ASTS': 'BATS_ASTS, 30_0ae49.csv',
    'BA': 'BATS_BA, 30_88ff7.csv',
    'CRWV': 'BATS_CRWV, 30_18bd5.csv',
    'GOOG': 'BATS_GOOG, 30_7c8e9.csv',
    'HIMS': 'BATS_HIMS, 30_44cf9.csv',
    'IBKR': 'BATS_IBKR, 30_8ad1d.csv',
    'INTC': 'BATS_INTC, 30_6b01b.csv',
    'KRNT': 'BATS_KRNT, 30_55fc2.csv',
    'MU': 'BATS_MU, 30_bd2ae.csv',
    'OSCR': 'BATS_OSCR, 30_be3f9.csv',
    'PLTR': 'BATS_PLTR, 30_b0c8d.csv',
    'RKLB': 'BATS_RKLB, 30_16acd.csv',
    'TTWO': 'BATS_TTWO, 30_ebade.csv',
    'ADAUSDT': 'BINANCE_ADAUSDT, 30_5df7d.csv',
    'BTCUSDT': 'BINANCE_BTCUSDT, 30_82cc5.csv',
    'ETHUSD': 'BINANCE_ETHUSD, 30_f34d8.csv',
    'SOLUSD': 'COINBASE_SOLUSD, 30_8b25e.csv',
    'USDILS': 'FOREXCOM_USDILS, 30_48cf9.csv',
}

print("Loading 30m data...", flush=True)
DATA = {}
for asset, file in FILES_30M.items():
    path = DATA_DIR / file
    if path.exists():
        try:
            DATA[asset] = load_data(str(path))
        except Exception as e:
            print(f"  Error loading {asset}: {e}", flush=True)
    else:
        print(f"  Missing: {file}", flush=True)
print(f"Loaded {len(DATA)} assets", flush=True)

# Parameter grid - focused based on 1H lessons
ZZ = [2, 3, 4, 5]
FIB = [0.618, 0.705, 0.786, 0.85, 0.9]
TOL = [0.03, 0.05, 0.08, 0.10, 0.12]
GAP = [3, 5, 7, 10]
RSI = [25, 30, 35, 40, 45]
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
    combos = list(product(ZZ, FIB, TOL, GAP, RSI, DEV, TREND, VOL))
    print(f"Testing {len(combos)} combinations for 30m optimization...", flush=True)
    
    best = {'passing': 0}
    
    with Pool(processes=cpu_count()) as pool:
        for i, (passing, args, results) in enumerate(pool.imap_unordered(test_combo, combos, chunksize=50)):
            if passing > best['passing']:
                zz, fib, tol, gap, rsi, dev, trend, vol = args
                best = {
                    'passing': passing, 'results': results,
                    'zz': zz, 'fib': fib, 'tol': tol, 'gap': gap,
                    'rsi': rsi, 'dev': dev, 'trend': trend, 'vol': vol
                }
                print(f"  NEW BEST: {passing}/{len(DATA)} - ZZ={zz}, Fib={fib}, Tol={tol}, RSI<{rsi}, Trend={trend}, Vol={vol}", flush=True)
            
            if (i+1) % 500 == 0:
                pct = (i+1)/len(combos)*100
                print(f"  Progress: {i+1}/{len(combos)} ({pct:.0f}%) - best: {best['passing']}/{len(DATA)}", flush=True)
    
    print(f"\n{'='*70}", flush=True)
    print(f"FINAL 30m RESULT: {best['passing']}/{len(DATA)} ({best['passing']/len(DATA)*100:.0f}%)", flush=True)
    if 'zz' in best:
        print(f"Parameters:", flush=True)
        print(f"  ZZ={best.get('zz')}, Fib={best.get('fib')}, Tol={best.get('tol')}, Gap={best.get('gap')}", flush=True)
        print(f"  RSI<{best.get('rsi')}, Dev={best.get('dev')}, Trend={best.get('trend')}, Vol={best.get('vol')}", flush=True)
    print(f"{'='*70}", flush=True)
    
    if 'results' in best:
        print("\nPer-asset results:", flush=True)
        passing_list = []
        failing_list = []
        for asset in sorted(FILES_30M.keys()):
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
