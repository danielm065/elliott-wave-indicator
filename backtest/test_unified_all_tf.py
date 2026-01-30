"""
Test UNIFIED parameters across ALL timeframes
Goal: Find best single parameter set that works on most assets/timeframes
"""
import sys
sys.path.insert(0, r'C:\Users\danie\projects\elliott-wave-indicator\backtest')

from backtester import ElliottICTBacktester, load_data
from pathlib import Path
from itertools import product
from multiprocessing import Pool, cpu_count
from collections import defaultdict

DATA_DIR = Path(r'C:\Users\danie\projects\elliott-wave-indicator\data')

# All timeframes with their files
TIMEFRAMES = {
    '1D': {
        'AAPL': 'NASDAQ_AAPL, 1D_4e91c.csv',
        'AMD': 'BATS_AMD, 1D_7d8f6.csv',
        'AMZN': 'NASDAQ_AMZN, 1D_fcc97.csv',
        'BTCUSDT': 'BINANCE_BTCUSDT, 1D_cdf77.csv',
        'ETHUSD': 'BINANCE_ETHUSD, 1D_d5f71.csv',
        'GOOG': 'BATS_GOOG, 1D_aae99.csv',
        'META': 'BATS_META, 1D_2b3eb.csv',
        'MNQ': 'MNQ_1D.csv',
        'MSFT': 'NASDAQ_MSFT, 1D_cfa26.csv',
        'NVDA': 'NASDAQ_NVDA, 1D_8f3be.csv',
        'TSLA': 'NASDAQ_TSLA, 1D_4bfee.csv',
    },
    '4H': {
        'AMD': 'BATS_AMD, 240_c2599.csv',
        'ASTS': 'BATS_ASTS, 240_a0ab9.csv',
        'BA': 'BATS_BA, 240_69b3b.csv',
        'BTCUSDT': 'BINANCE_BTCUSDT, 240_fe0b8.csv',
        'CRWV': 'BATS_CRWV, 240_ed96a.csv',
        'ETHUSD': 'BINANCE_ETHUSD, 240_aff0c.csv',
        'GOOG': 'BATS_GOOG, 240_52190.csv',
        'HIMS': 'BATS_HIMS, 240_9ad5f.csv',
        'IBKR': 'BATS_IBKR, 240_eef24.csv',
        'INTC': 'BATS_INTC, 240_43ac7.csv',
        'KRNT': 'BATS_KRNT, 240_38050.csv',
        'MNQ': 'MNQ_4H.csv',
        'MU': 'BATS_MU, 240_6d83f.csv',
        'OSCR': 'BATS_OSCR, 240_69bf3.csv',
        'PLTR': 'BATS_PLTR, 240_4ba34.csv',
        'RKLB': 'BATS_RKLB, 240_9e8cf.csv',
        'SOLUSD': 'COINBASE_SOLUSD, 240_b1f00.csv',
        'TTWO': 'BATS_TTWO, 240_ba1c1.csv',
    },
    '1H': {
        'AMD': 'BATS_AMD, 60_2853d.csv',
        'ASTS': 'BATS_ASTS, 60_360b6.csv',
        'BA': 'BATS_BA, 60_a5067.csv',
        'BTCUSDT': 'BINANCE_BTCUSDT, 60_b6ebd.csv',
        'CRWV': 'BATS_CRWV, 60_58712.csv',
        'ETHUSD': 'BINANCE_ETHUSD, 60_b3215.csv',
        'GOOG': 'BATS_GOOG, 60_78270.csv',
        'HIMS': 'BATS_HIMS, 60_ea867.csv',
        'IBKR': 'BATS_IBKR, 60_ebbaf.csv',
        'INTC': 'BATS_INTC, 60_59380.csv',
        'KRNT': 'BATS_KRNT, 60_f5a05.csv',
        'MNQ': 'MNQ_1H.csv',
        'MU': 'BATS_MU, 60_609b8.csv',
        'OSCR': 'BATS_OSCR, 60_092fb.csv',
        'PLTR': 'BATS_PLTR, 60_14b34.csv',
        'RKLB': 'BATS_RKLB, 60_ae005.csv',
        'SOLUSD': 'COINBASE_SOLUSD, 60_49536.csv',
        'TTWO': 'BATS_TTWO, 60_73235.csv',
        'USDILS': 'FOREXCOM_USDILS, 60_14147.csv',
        'ADAUSDT': 'BINANCE_ADAUSDT, 60_ee9e1.csv',
    },
}

# Load all data
print("Loading all timeframe data...", flush=True)
ALL_DATA = {}
for tf, files in TIMEFRAMES.items():
    ALL_DATA[tf] = {}
    for asset, file in files.items():
        path = DATA_DIR / file
        if path.exists():
            try:
                ALL_DATA[tf][asset] = load_data(str(path))
            except:
                pass
    print(f"  {tf}: {len(ALL_DATA[tf])} assets", flush=True)

# Parameter grid
ZZ = [2, 3, 4]
FIB = [0.618, 0.786, 0.85]
TOL = [0.05, 0.10, 0.15]
GAP = [3, 5, 7]
RSI = [30, 40, 50]

def test_unified(args):
    zz, fib, tol, gap, rsi_max = args
    params = {
        'zz_depth': zz, 'fib_entry_level': fib, 'fib_tolerance': tol,
        'signal_gap': gap, 'rr_ratio': 1.0, 'zz_dev': 0.2,
        'use_rsi_filter': True, 'rsi_max': rsi_max,
        'use_volume': False, 'use_trend_filter': False,
    }
    
    results_by_tf = {}
    total_passing = 0
    total_assets = 0
    
    for tf, data_dict in ALL_DATA.items():
        tf_passing = 0
        tf_total = len(data_dict)
        
        for asset, df in data_dict.items():
            try:
                bt = ElliottICTBacktester(df, params)
                result = bt.run_backtest()
                trades = result.wins + result.losses
                if trades >= 2 and result.win_rate >= 80:
                    tf_passing += 1
            except:
                pass
        
        results_by_tf[tf] = (tf_passing, tf_total)
        total_passing += tf_passing
        total_assets += tf_total
    
    return (total_passing, total_assets, args, results_by_tf)

if __name__ == '__main__':
    combos = list(product(ZZ, FIB, TOL, GAP, RSI))
    print(f"Testing {len(combos)} unified parameter combos across all TFs...", flush=True)
    
    best = {'passing': 0, 'total': 0}
    
    with Pool(processes=cpu_count()) as pool:
        for i, (passing, total, args, tf_results) in enumerate(pool.imap_unordered(test_unified, combos, chunksize=20)):
            if passing > best['passing']:
                best = {
                    'passing': passing, 'total': total,
                    'args': args, 'tf_results': tf_results
                }
                zz, fib, tol, gap, rsi = args
                print(f"  NEW BEST: {passing}/{total} - ZZ={zz}, Fib={fib}, Tol={tol}, Gap={gap}, RSI<{rsi}", flush=True)
                for tf, (p, t) in tf_results.items():
                    print(f"    {tf}: {p}/{t}", flush=True)
            
            if (i+1) % 50 == 0:
                print(f"  Progress: {i+1}/{len(combos)} (best: {best['passing']}/{best['total']})...", flush=True)
    
    print(f"\n{'='*70}", flush=True)
    print(f"BEST UNIFIED PARAMETERS:", flush=True)
    print(f"  ZZ={best['args'][0]}, Fib={best['args'][1]}, Tol={best['args'][2]}, Gap={best['args'][3]}, RSI<{best['args'][4]}", flush=True)
    print(f"\nRESULTS BY TIMEFRAME:", flush=True)
    for tf, (p, t) in best['tf_results'].items():
        pct = p/t*100 if t > 0 else 0
        status = "✅" if pct >= 80 else "❌"
        print(f"  {tf}: {p}/{t} ({pct:.0f}%) {status}", flush=True)
    print(f"\nTOTAL: {best['passing']}/{best['total']} ({best['passing']/best['total']*100:.0f}%)", flush=True)
    print(f"{'='*70}", flush=True)
