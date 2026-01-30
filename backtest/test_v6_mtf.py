"""
Test v6 backtester with Multi-Timeframe + Confluence
"""
import sys
sys.path.insert(0, r'C:\Users\danie\projects\elliott-wave-indicator\backtest')

from backtester_v6_mtf import ElliottICTBacktesterV6, load_data
from pathlib import Path
from itertools import product
from multiprocessing import Pool, cpu_count

DATA_DIR = Path(r'C:\Users\danie\projects\elliott-wave-indicator\data')

# 1H data + 4H for MTF
FILES_1H = {
    'AMD': ('BATS_AMD, 60_2853d.csv', 'BATS_AMD, 240_c2599.csv'),
    'ASTS': ('BATS_ASTS, 60_360b6.csv', 'BATS_ASTS, 240_a0ab9.csv'),
    'BA': ('BATS_BA, 60_a5067.csv', 'BATS_BA, 240_69b3b.csv'),
    'CRWV': ('BATS_CRWV, 60_58712.csv', 'BATS_CRWV, 240_ed96a.csv'),
    'GOOG': ('BATS_GOOG, 60_78270.csv', 'BATS_GOOG, 240_52190.csv'),
    'HIMS': ('BATS_HIMS, 60_ea867.csv', 'BATS_HIMS, 240_9ad5f.csv'),
    'IBKR': ('BATS_IBKR, 60_ebbaf.csv', 'BATS_IBKR, 240_eef24.csv'),
    'INTC': ('BATS_INTC, 60_59380.csv', 'BATS_INTC, 240_43ac7.csv'),
    'KRNT': ('BATS_KRNT, 60_f5a05.csv', 'BATS_KRNT, 240_38050.csv'),
    'MU': ('BATS_MU, 60_609b8.csv', 'BATS_MU, 240_6d83f.csv'),
    'OSCR': ('BATS_OSCR, 60_092fb.csv', 'BATS_OSCR, 240_69bf3.csv'),
    'PLTR': ('BATS_PLTR, 60_14b34.csv', 'BATS_PLTR, 240_4ba34.csv'),
    'RKLB': ('BATS_RKLB, 60_ae005.csv', 'BATS_RKLB, 240_9e8cf.csv'),
    'TTWO': ('BATS_TTWO, 60_73235.csv', 'BATS_TTWO, 240_ba1c1.csv'),
    'ADAUSDT': ('BINANCE_ADAUSDT, 60_ee9e1.csv', 'BINANCE_ADAUSDT, 240_200b2.csv'),
    'BTCUSDT': ('BINANCE_BTCUSDT, 60_b6ebd.csv', 'BINANCE_BTCUSDT, 240_fe0b8.csv'),
    'ETHUSD': ('BINANCE_ETHUSD, 60_b3215.csv', 'BINANCE_ETHUSD, 240_aff0c.csv'),
    'MNQ': ('MNQ_1H.csv', 'MNQ_4H.csv'),
    'SOLUSD': ('COINBASE_SOLUSD, 60_49536.csv', 'COINBASE_SOLUSD, 240_b1f00.csv'),
    'USDILS': ('FOREXCOM_USDILS, 60_14147.csv', 'FOREXCOM_USDILS, 240_3fecc.csv'),
}

print("Loading data...", flush=True)
DATA = {}
for asset, (file_1h, file_4h) in FILES_1H.items():
    path_1h = DATA_DIR / file_1h
    path_4h = DATA_DIR / file_4h
    if path_1h.exists() and path_4h.exists():
        try:
            DATA[asset] = {
                '1h': load_data(str(path_1h)),
                '4h': load_data(str(path_4h))
            }
        except Exception as e:
            print(f"Error loading {asset}: {e}")
print(f"Loaded {len(DATA)} assets with MTF data", flush=True)

# Parameter grid
ZZ = [2, 3, 4]
FIB = [0.618, 0.786, 0.85]
TOL = [0.08, 0.10]
GAP = [5, 7]
MIN_CONF = [2, 3, 4]  # Minimum confluence required
USE_HTF = [True, False]
USE_FVG = [True, False]
USE_OB = [True, False]

def test_single_combo(args):
    zz, fib, tol, gap, conf, htf, fvg, ob = args
    
    params = {
        'zz_depth': zz, 'fib_entry_level': fib, 'fib_tolerance': tol,
        'signal_gap': gap, 'rr_ratio': 1.0, 'zz_dev': 0.2,
        'min_confluence': conf, 'use_htf_trend': htf,
        'use_fvg': fvg, 'use_ob': ob,
    }
    
    results = {}
    for asset, data in DATA.items():
        try:
            bt = ElliottICTBacktesterV6(data['1h'], data['4h'], params)
            result = bt.run_backtest()
            total = result.wins + result.losses
            results[asset] = {
                'total': total, 
                'wins': result.wins, 
                'wr': result.win_rate if total > 0 else 0
            }
        except Exception as e:
            results[asset] = {'total': 0, 'wins': 0, 'wr': 0}
    
    passing = sum(1 for r in results.values() if r['total'] >= 2 and r['wr'] >= 80)
    return (passing, args, results)

if __name__ == '__main__':
    combos = list(product(ZZ, FIB, TOL, GAP, MIN_CONF, USE_HTF, USE_FVG, USE_OB))
    
    # Filter: at least one of HTF/FVG/OB must be True
    combos = [c for c in combos if c[5] or c[6] or c[7]]
    
    print(f"Testing {len(combos)} combinations (MTF + Confluence)...", flush=True)
    
    best = {'passing': 0}
    with Pool(processes=cpu_count()) as pool:
        for i, (passing, args, results) in enumerate(pool.imap_unordered(test_single_combo, combos, chunksize=20)):
            if passing > best['passing']:
                zz, fib, tol, gap, conf, htf, fvg, ob = args
                best = {
                    'passing': passing, 'results': results,
                    'zz': zz, 'fib': fib, 'tol': tol, 'gap': gap,
                    'conf': conf, 'htf': htf, 'fvg': fvg, 'ob': ob
                }
                print(f"  NEW BEST: {passing}/20 - ZZ={zz}, Fib={fib}, Conf>={conf}, HTF={htf}, FVG={fvg}, OB={ob}", flush=True)
            
            if (i+1) % 100 == 0:
                print(f"  {i+1}/{len(combos)} (best: {best['passing']})...", flush=True)
    
    print(f"\n{'='*60}", flush=True)
    print(f"BEST MTF: {best['passing']}/20", flush=True)
    print(f"ZZ={best.get('zz')}, Fib={best.get('fib')}, Tol={best.get('tol')}, Gap={best.get('gap')}", flush=True)
    print(f"MinConf={best.get('conf')}, HTF={best.get('htf')}, FVG={best.get('fvg')}, OB={best.get('ob')}", flush=True)
    print(f"{'='*60}", flush=True)
    
    if 'results' in best:
        passing_list = []
        failing_list = []
        for asset in sorted(FILES_1H.keys()):
            r = best['results'].get(asset, {'total': 0, 'wins': 0, 'wr': 0})
            if r['total'] >= 2:
                if r['wr'] >= 80:
                    passing_list.append(f"{asset}({r['wr']:.0f}%)")
                else:
                    failing_list.append(f"{asset}({r['wr']:.0f}%)")
            else:
                failing_list.append(f"{asset}(NO SIG)")
        
        print(f"PASSING: {passing_list}", flush=True)
        print(f"FAILING: {failing_list}", flush=True)
