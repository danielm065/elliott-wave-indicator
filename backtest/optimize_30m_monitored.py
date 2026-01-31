"""
30m optimization with monitoring support
Writes progress to status.json for external monitoring
"""
import sys
import json
from datetime import datetime
sys.path.insert(0, r'C:\Users\danie\projects\elliott-wave-indicator\backtest')

from backtester import ElliottICTBacktester, load_data
from pathlib import Path
from itertools import product
from multiprocessing import Pool, cpu_count

DATA_DIR = Path(r'C:\Users\danie\projects\elliott-wave-indicator\data')
STATUS_FILE = Path(r'C:\Users\danie\projects\elliott-wave-indicator\optimization_status.json')

# 30m files - CORRECTED
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
    'SOLUSD': 'COINBASE_SOLUSD, 30_e1ec0.csv',
    'USDILS': 'FOREXCOM_USDILS, 30_740f2.csv',
    'MNQ': 'MNQ_30m.csv',
}

def write_status(status_dict):
    """Write status to JSON file for monitoring"""
    status_dict['updated'] = datetime.now().isoformat()
    with open(STATUS_FILE, 'w') as f:
        json.dump(status_dict, f, indent=2)

print("Loading 30m data...", flush=True)
DATA = {}
for asset, file in FILES_30M.items():
    path = DATA_DIR / file
    if path.exists():
        try:
            DATA[asset] = load_data(str(path))
            print(f"  Loaded {asset}", flush=True)
        except Exception as e:
            print(f"  Error loading {asset}: {e}", flush=True)
    else:
        print(f"  Missing: {file}", flush=True)
print(f"Loaded {len(DATA)} assets", flush=True)

# Parameter grid
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
    total_combos = len(combos)
    
    print(f"Testing {total_combos} combinations for 30m optimization...", flush=True)
    
    # Initialize status
    write_status({
        'timeframe': '30m',
        'status': 'running',
        'progress': 0,
        'total': total_combos,
        'percent': 0,
        'best_passing': 0,
        'best_params': None,
        'assets_loaded': len(DATA)
    })
    
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
            
            # Update status every 100 iterations
            if (i+1) % 100 == 0:
                pct = (i+1)/total_combos*100
                write_status({
                    'timeframe': '30m',
                    'status': 'running',
                    'progress': i+1,
                    'total': total_combos,
                    'percent': round(pct, 1),
                    'best_passing': best['passing'],
                    'best_params': {
                        'zz': best.get('zz'), 'fib': best.get('fib'),
                        'tol': best.get('tol'), 'gap': best.get('gap'),
                        'rsi': best.get('rsi'), 'trend': best.get('trend'),
                        'vol': best.get('vol')
                    } if best['passing'] > 0 else None,
                    'assets_loaded': len(DATA)
                })
            
            if (i+1) % 500 == 0:
                pct = (i+1)/total_combos*100
                print(f"  Progress: {i+1}/{total_combos} ({pct:.0f}%) - best: {best['passing']}/{len(DATA)}", flush=True)
    
    # Final status
    passing_list = []
    failing_list = []
    if 'results' in best:
        for asset in sorted(FILES_30M.keys()):
            r = best['results'].get(asset, {'total': 0, 'wins': 0, 'wr': 0})
            if r['total'] >= 2:
                if r['wr'] >= 80:
                    passing_list.append(f"{asset}({r['wr']:.0f}%,n={r['total']})")
                else:
                    failing_list.append(f"{asset}({r['wr']:.0f}%,n={r['total']})")
            else:
                failing_list.append(f"{asset}(n={r['total']})")
    
    write_status({
        'timeframe': '30m',
        'status': 'completed',
        'progress': total_combos,
        'total': total_combos,
        'percent': 100,
        'best_passing': best['passing'],
        'best_params': {
            'zz': best.get('zz'), 'fib': best.get('fib'),
            'tol': best.get('tol'), 'gap': best.get('gap'),
            'rsi': best.get('rsi'), 'trend': best.get('trend'),
            'vol': best.get('vol')
        } if best['passing'] > 0 else None,
        'assets_loaded': len(DATA),
        'passing_assets': passing_list,
        'failing_assets': failing_list
    })
    
    print(f"\n{'='*70}", flush=True)
    print(f"FINAL 30m RESULT: {best['passing']}/{len(DATA)} ({best['passing']/len(DATA)*100:.0f}%)", flush=True)
    if 'zz' in best:
        print(f"Parameters:", flush=True)
        print(f"  ZZ={best.get('zz')}, Fib={best.get('fib')}, Tol={best.get('tol')}, Gap={best.get('gap')}", flush=True)
        print(f"  RSI<{best.get('rsi')}, Dev={best.get('dev')}, Trend={best.get('trend')}, Vol={best.get('vol')}", flush=True)
    print(f"{'='*70}", flush=True)
    print(f"\nPASSING ({len(passing_list)}): {passing_list}", flush=True)
    print(f"FAILING ({len(failing_list)}): {failing_list}", flush=True)
