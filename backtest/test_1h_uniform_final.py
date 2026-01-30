"""
1H - Find BEST uniform params (no per-asset customization)
Based on patterns from successful custom params: RSI<35, Trend=False worked well
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

# Extended grid based on successful patterns
ZZ = [2, 3, 4, 5]
FIB = [0.5, 0.618, 0.7, 0.786, 0.85]
TOL = [0.05, 0.10, 0.15, 0.20]
RSI = [30, 35, 40, 45]
GAP = [2, 3, 5]
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
    passing = sum(1 for r in results.values() if r['total'] >= 2 and r['wr'] >= 80)
    with_trades = sum(1 for r in results.values() if r['total'] >= 2)
    return passing, with_trades, results

best = {'passing': 0}
combos = list(product(ZZ, FIB, TOL, RSI, GAP, TREND))
print(f"Testing {len(combos)} combinations...", flush=True)

for i, (zz, fib, tol, rsi, gap, trend) in enumerate(combos):
    params = {
        'zz_depth': zz, 'fib_entry_level': fib, 'fib_tolerance': tol,
        'rsi_threshold': rsi, 'signal_gap': gap, 'use_trend_filter': trend,
        'use_volume_filter': True, 'use_rsi_filter': True,
        'rr_ratio': 1.0, 'zz_dev': 0.2, 'ema_period': 200,
    }
    passing, with_trades, results = test_combo(params)
    
    if passing > best['passing']:
        best = {'passing': passing, 'with_trades': with_trades, 'results': results,
                'zz': zz, 'fib': fib, 'tol': tol, 'rsi': rsi, 'gap': gap, 'trend': trend}
        print(f"  NEW BEST: {passing}/20 - ZZ={zz}, Fib={fib}, Tol={tol}, RSI<{rsi}, Gap={gap}, T={trend}", flush=True)
    
    if (i+1) % 200 == 0:
        print(f"  {i+1}/{len(combos)} (best: {best['passing']})...", flush=True)

print(f"\n{'='*60}", flush=True)
print(f"BEST UNIFORM: {best['passing']}/20 ({best['with_trades']} with trades)", flush=True)
print(f"ZZ={best['zz']}, Fib={best['fib']}, Tol={best['tol']}, RSI<{best['rsi']}, Gap={best['gap']}, Trend={best['trend']}", flush=True)
print(f"{'='*60}", flush=True)

for asset in sorted(FILES_1H.keys()):
    r = best['results'].get(asset, {'total': 0, 'wins': 0, 'wr': 0})
    if r['total'] >= 2:
        status = "PASS" if r['wr'] >= 80 else "FAIL"
        print(f"  {asset}: {r['wins']}/{r['total']} = {r['wr']:.0f}% [{status}]", flush=True)
    else:
        print(f"  {asset}: {r['total']} trades [NO SIGNAL]", flush=True)
