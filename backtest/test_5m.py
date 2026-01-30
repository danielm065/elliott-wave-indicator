"""
5M PARALLEL OPTIMIZED TEST - Uses multiprocessing for speed
"""
import sys
sys.path.insert(0, r'C:\Users\danie\projects\elliott-wave-indicator\backtest')

from backtester import ElliottICTBacktester, load_data
from pathlib import Path
from itertools import product
from multiprocessing import Pool, cpu_count
import time

DATA_DIR = Path(r'C:\Users\danie\projects\elliott-wave-indicator\data')

FILES_5M = {
    'AMD': 'BATS_AMD, 5_f7455.csv',
    'ASTS': 'BATS_ASTS, 5_521f9.csv',
    'BA': 'BATS_BA, 5_e3560.csv',
    'CRWV': 'BATS_CRWV, 5_8bf0e.csv',
    'GOOG': 'BATS_GOOG, 5_8b9d7.csv',
    'HIMS': 'BATS_HIMS, 5_58bb0.csv',
    'IBKR': 'BATS_IBKR, 5_d46be.csv',
    'INTC': 'BATS_INTC, 5_c9971.csv',
    'KRNT': 'BATS_KRNT, 5_204ad.csv',
    'MU': 'BATS_MU, 5_b2508.csv',
    'OSCR': 'BATS_OSCR, 5_864be.csv',
    'PLTR': 'BATS_PLTR, 5_f339c.csv',
    'RKLB': 'BATS_RKLB, 5_b0b72.csv',
    'TTWO': 'BATS_TTWO, 5_d7ea8.csv',
    'ADAUSDT': 'BINANCE_ADAUSDT, 5_e01b1.csv',
    'BTCUSDT': 'BINANCE_BTCUSDT, 5_69b1c.csv',
    'ETHUSD': 'BINANCE_ETHUSD, 5_26e57.csv',
    'MNQ': 'MNQ_5m.csv',
    'SOLUSD': 'COINBASE_SOLUSD, 5_77193.csv',
    'USDILS': 'FOREXCOM_USDILS, 5_7aa81.csv',
}

# Load data once globally
print("Loading 5m data...", flush=True)
DATA = {}
for asset, file in FILES_5M.items():
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
    print(f"TIMEFRAME: 5m", flush=True)
    print(f"BEST RESULT: {best['passing']}/20 passing 80%+", flush=True)
    print(f"PARAMETERS: ZZ={best.get('zz')}, Fib={best.get('fib')}, Tol={best.get('tol')}, RSI<{best.get('rsi')}, Gap={best.get('gap')}, Trend={best.get('trend')}, Vol={best.get('vol')}, RSI_F={best.get('rsi_f')}", flush=True)
    print(f"{'='*60}", flush=True)
    
    if 'results' in best:
        passing_list = []
        failing_list = []
        no_signal_list = []
        
        for asset in sorted(FILES_5M.keys()):
            r = best['results'].get(asset, {'total': 0, 'wins': 0, 'wr': 0})
            if r['total'] >= 2:
                if r['wr'] >= 80:
                    passing_list.append(f"{asset}({r['wr']:.0f}%)")
                else:
                    failing_list.append(f"{asset}({r['wr']:.0f}%)")
            else:
                no_signal_list.append(asset)
        
        print(f"\nPASSING: {passing_list}", flush=True)
        print(f"FAILING: {failing_list}", flush=True)
        print(f"NO SIGNAL: {no_signal_list}", flush=True)
