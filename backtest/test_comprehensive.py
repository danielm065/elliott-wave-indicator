"""
COMPREHENSIVE TEST - Original backtester with ALL possible combinations
No shortcuts, test everything to find the best R:R=1.0 settings
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

print("Loading data...", flush=True)
DATA = {}
for asset, file in FILES_1H.items():
    path = DATA_DIR / file
    if path.exists():
        try:
            DATA[asset] = load_data(str(path))
        except:
            pass
print(f"Loaded {len(DATA)} assets", flush=True)

# COMPREHENSIVE grid - all reasonable values
ZZ = [2, 3, 4, 5, 6]
FIB = [0.50, 0.55, 0.618, 0.65, 0.70, 0.75, 0.786, 0.80, 0.85, 0.90]
TOL = [0.03, 0.05, 0.08, 0.10, 0.12, 0.15, 0.20]
RSI = [20, 25, 30, 35, 40, 45, 50, 55, 60]
GAP = [2, 3, 4, 5, 6, 8]
TREND = [True, False]
VOL = [True, False]
RSI_F = [True, False]

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
    passing = sum(1 for r in results.values() if r['total'] >= 2 and r['wr'] >= 80)
    with_trades = sum(1 for r in results.values() if r['total'] >= 2)
    return passing, with_trades, results

best = {'passing': 0}

# Filter combinations that don't make sense
count = 0
for zz, fib, tol, rsi, gap, trend, vol, rsi_f in product(ZZ, FIB, TOL, RSI, GAP, TREND, VOL, RSI_F):
    # Skip if no filters at all
    if not vol and not rsi_f and not trend:
        continue
    count += 1

print(f"Testing {count} combinations (R:R=1.0)...", flush=True)

i = 0
for zz, fib, tol, rsi, gap, trend, vol, rsi_f in product(ZZ, FIB, TOL, RSI, GAP, TREND, VOL, RSI_F):
    if not vol and not rsi_f and not trend:
        continue
    
    i += 1
    params = {
        'zz_depth': zz, 'fib_entry_level': fib, 'fib_tolerance': tol,
        'rsi_threshold': rsi, 'signal_gap': gap, 'use_trend_filter': trend,
        'use_volume_filter': vol, 'use_rsi_filter': rsi_f,
        'rr_ratio': 1.0, 'zz_dev': 0.2, 'ema_period': 200,
    }
    passing, with_trades, results = test_combo(params)
    
    if passing > best['passing']:
        best = {'passing': passing, 'with_trades': with_trades, 'results': results,
                'zz': zz, 'fib': fib, 'tol': tol, 'rsi': rsi, 'gap': gap, 
                'trend': trend, 'vol': vol, 'rsi_f': rsi_f}
        print(f"  NEW BEST: {passing}/20 @ combo {i}", flush=True)
    
    if i % 500 == 0:
        print(f"  {i}/{count} (best: {best['passing']})...", flush=True)

print(f"\n{'='*60}", flush=True)
print(f"BEST COMPREHENSIVE: {best['passing']}/20", flush=True)
print(f"ZZ={best.get('zz')}, Fib={best.get('fib')}, Tol={best.get('tol')}", flush=True)
print(f"RSI<{best.get('rsi')}, Gap={best.get('gap')}", flush=True)
print(f"Trend={best.get('trend')}, Vol={best.get('vol')}, RSI_F={best.get('rsi_f')}", flush=True)
print(f"{'='*60}", flush=True)

if 'results' in best:
    for asset in sorted(FILES_1H.keys()):
        r = best['results'].get(asset, {'total': 0, 'wins': 0, 'wr': 0})
        if r['total'] >= 2:
            status = "PASS" if r['wr'] >= 80 else "FAIL"
            print(f"  {asset}: {r['wins']}/{r['total']} = {r['wr']:.0f}% [{status}]", flush=True)
        else:
            print(f"  {asset}: {r['total']} trades [NO SIGNAL]", flush=True)
