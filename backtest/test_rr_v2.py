"""
Continue optimization - focus on R:R=0.5 range and fine-tune other params
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

# Fine-tuned grid around best params
ZZ = [2, 3, 4, 5]
FIB = [0.70, 0.75, 0.786, 0.80, 0.85]
TOL = [0.05, 0.08, 0.10, 0.12, 0.15]
RSI = [25, 30, 35]
GAP = [2, 3, 4, 5]
RR = [0.4, 0.5, 0.6, 0.7]  # Focus on lower R:R

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
# Trend=False was best
combos = list(product(ZZ, FIB, TOL, RSI, GAP, RR))
print(f"Testing {len(combos)} combinations (Trend=False fixed)...", flush=True)

for i, (zz, fib, tol, rsi, gap, rr) in enumerate(combos):
    params = {
        'zz_depth': zz, 'fib_entry_level': fib, 'fib_tolerance': tol,
        'rsi_threshold': rsi, 'signal_gap': gap, 'use_trend_filter': False,
        'use_volume_filter': True, 'use_rsi_filter': True,
        'rr_ratio': rr, 'zz_dev': 0.2, 'ema_period': 200,
    }
    passing, with_trades, results = test_combo(params)
    
    if passing > best['passing']:
        best = {'passing': passing, 'with_trades': with_trades, 'results': results,
                'zz': zz, 'fib': fib, 'tol': tol, 'rsi': rsi, 'gap': gap, 'rr': rr}
        print(f"  NEW BEST: {passing}/20 - ZZ={zz}, Fib={fib}, Tol={tol}, RSI<{rsi}, Gap={gap}, RR={rr}", flush=True)
    
    if (i+1) % 200 == 0:
        print(f"  {i+1}/{len(combos)} (best: {best['passing']})...", flush=True)

print(f"\n{'='*60}", flush=True)
print(f"BEST: {best['passing']}/20 ({best.get('with_trades', 0)} with trades)", flush=True)
print(f"ZZ={best.get('zz')}, Fib={best.get('fib')}, Tol={best.get('tol')}", flush=True)
print(f"RSI<{best.get('rsi')}, Gap={best.get('gap')}, RR={best.get('rr')}", flush=True)
print(f"{'='*60}", flush=True)

if 'results' in best:
    for asset in sorted(FILES_1H.keys()):
        r = best['results'].get(asset, {'total': 0, 'wins': 0, 'wr': 0})
        if r['total'] >= 2:
            status = "PASS" if r['wr'] >= 80 else "FAIL"
            print(f"  {asset}: {r['wins']}/{r['total']} = {r['wr']:.0f}% [{status}]", flush=True)
        else:
            print(f"  {asset}: {r['total']} trades [NO SIGNAL]", flush=True)
