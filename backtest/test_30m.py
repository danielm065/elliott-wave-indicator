"""
30M TIMEFRAME OPTIMIZATION - Parallel testing
"""
import sys
sys.path.insert(0, r'C:\Users\danie\projects\elliott-wave-indicator\backtest')

from backtester import ElliottICTBacktester, load_data
from pathlib import Path
from itertools import product
from multiprocessing import Pool, cpu_count
import time

DATA_DIR = Path(r'C:\Users\danie\projects\elliott-wave-indicator\data')

FILES_30M = {
    'AMD': 'BATS_AMD, 30_cfc90.csv',
    'ASTS': 'BATS_ASTS, 30_7f37b.csv',
    'BA': 'BATS_BA, 30_46d47.csv',
    'CRWV': 'BATS_CRWV, 30_05e77.csv',
    'GOOG': 'BATS_GOOG, 30_2c4a7.csv',
    'HIMS': 'BATS_HIMS, 30_99196.csv',
    'IBKR': 'BATS_IBKR, 30_092a2.csv',
    'INTC': 'BATS_INTC, 30_a2d5b.csv',
    'KRNT': 'BATS_KRNT, 30_eb176.csv',
    'MU': 'BATS_MU, 30_cb8e4.csv',
    'OSCR': 'BATS_OSCR, 30_c1577.csv',
    'PLTR': 'BATS_PLTR, 30_25ae9.csv',
    'RKLB': 'BATS_RKLB, 30_3756c.csv',
    'TTWO': 'BATS_TTWO, 30_e5d22.csv',
    'ADAUSDT': 'BINANCE_ADAUSDT, 30_d120f.csv',
    'BTCUSDT': 'BINANCE_BTCUSDT, 30_af66c.csv',
    'ETHUSD': 'BINANCE_ETHUSD, 30_c3cd4.csv',
    'MNQ': 'MNQ_30m.csv',
    'SOLUSD': 'COINBASE_SOLUSD, 30_e1ec0.csv',
    'USDILS': 'FOREXCOM_USDILS, 30_740f2.csv',
}

# Load data once globally
print("Loading 30m data...", flush=True)
DATA = {}
for asset, file in FILES_30M.items():
    path = DATA_DIR / file
    if path.exists():
        try:
            DATA[asset] = load_data(str(path))
        except:
            pass
print(f"Loaded {len(DATA)} assets", flush=True)

# Parameter grid
ZZ = [2, 3, 4, 5]
FIB = [0.50, 0.618, 0.70, 0.786, 0.85]
TOL = [0.05, 0.10, 0.15]
RSI = [25, 30, 40, 50]
GAP = [3, 5, 7]
TREND = [True, False]
VOL = [True, False]
RSI_F = [True, False]

def test_single_combo(args):
    """Test a single combination - for parallel execution"""
    zz, fib, tol, rsi, gap, trend, vol, rsi_f = args
    
    params = {
        'zz_depth': zz, 'fib_entry_level': fib, 'fib_tolerance': tol,
        'rsi_threshold': rsi, 'signal_gap': gap, 'use_trend_filter': trend,
        'use_volume_filter': vol, 'use_rsi_filter': rsi_f,
        'rr_ratio': 1.0, 'zz_dev': 0.2, 'ema_period': 200,
    }
    
    results = {}
    for asset, df in DATA.items():
        try:
            bt = ElliottICTBacktester(df, params)
            result = bt.run_backtest()
            total = result.wins + result.losses
            results[asset] = {'total': total, 'wins': result.wins, 'wr': result.win_rate if total > 0 else 0}
        except:
            pass
    
    passing = sum(1 for r in results.values() if r['total'] >= 2 and r['wr'] >= 80)
    return (passing, args, results)

if __name__ == '__main__':
    # Generate all combinations
    combos = []
    for zz, fib, tol, rsi, gap, trend, vol, rsi_f in product(ZZ, FIB, TOL, RSI, GAP, TREND, VOL, RSI_F):
        # Skip if no filters at all
        if not vol and not rsi_f and not trend:
            continue
        combos.append((zz, fib, tol, rsi, gap, trend, vol, rsi_f))
    
    print(f"Testing {len(combos)} combinations with {cpu_count()} CPU cores...", flush=True)
    start = time.time()
    
    # Run in parallel
    best = {'passing': 0}
    with Pool(processes=cpu_count()) as pool:
        for i, (passing, args, results) in enumerate(pool.imap_unordered(test_single_combo, combos, chunksize=50)):
            if passing > best['passing']:
                zz, fib, tol, rsi, gap, trend, vol, rsi_f = args
                best = {
                    'passing': passing, 'results': results,
                    'zz': zz, 'fib': fib, 'tol': tol, 'rsi': rsi, 'gap': gap,
                    'trend': trend, 'vol': vol, 'rsi_f': rsi_f
                }
                print(f"  NEW BEST: {passing}/20 - ZZ={zz}, Fib={fib}, RSI<{rsi}", flush=True)
            
            if (i+1) % 500 == 0:
                elapsed = time.time() - start
                rate = (i+1) / elapsed
                eta = (len(combos) - i - 1) / rate / 60
                print(f"  {i+1}/{len(combos)} ({rate:.0f}/sec, ETA: {eta:.1f}min)...", flush=True)
    
    elapsed = time.time() - start
    print(f"\nCompleted in {elapsed:.1f} seconds", flush=True)
    print(f"\n{'='*60}", flush=True)
    print(f"BEST: {best['passing']}/20", flush=True)
    print(f"ZZ={best.get('zz')}, Fib={best.get('fib')}, Tol={best.get('tol')}", flush=True)
    print(f"RSI<{best.get('rsi')}, Gap={best.get('gap')}", flush=True)
    print(f"Trend={best.get('trend')}, Vol={best.get('vol')}, RSI_F={best.get('rsi_f')}", flush=True)
    print(f"{'='*60}", flush=True)
    
    if 'results' in best:
        print("\nDETAILED RESULTS:", flush=True)
        passing_list = []
        failing_list = []
        for asset in sorted(FILES_30M.keys()):
            r = best['results'].get(asset, {'total': 0, 'wins': 0, 'wr': 0})
            if r['total'] >= 2:
                status = "PASS" if r['wr'] >= 80 else "FAIL"
                print(f"  {asset}: {r['wins']}/{r['total']} = {r['wr']:.0f}% [{status}]", flush=True)
                if r['wr'] >= 80:
                    passing_list.append(f"{asset}({r['wr']:.0f}%)")
                else:
                    failing_list.append(f"{asset}({r['wr']:.0f}%)")
            else:
                print(f"  {asset}: {r['total']} trades [NO SIGNAL]", flush=True)
                failing_list.append(f"{asset}(no signal)")
        
        print(f"\n{'='*60}", flush=True)
        print("SUMMARY:", flush=True)
        print(f"TIMEFRAME: 30m", flush=True)
        print(f"BEST RESULT: {best['passing']}/20 passing 80%+", flush=True)
        print(f"PARAMETERS: ZZ={best.get('zz')}, Fib={best.get('fib')}, Tol={best.get('tol')}, RSI<{best.get('rsi')}, Gap={best.get('gap')}, Trend={best.get('trend')}, Vol={best.get('vol')}, RSI_F={best.get('rsi_f')}", flush=True)
        print(f"\nPASSING: {passing_list}", flush=True)
        print(f"FAILING: {failing_list}", flush=True)
