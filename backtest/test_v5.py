"""
Test v5 backtester with confirmation entry
"""
import sys
sys.path.insert(0, r'C:\Users\danie\projects\elliott-wave-indicator\backtest')

from backtester_v5 import ElliottICTBacktesterV5, load_data
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

# Parameter grid for v5
ZZ = [2, 3, 4]
FIB = [0.618, 0.70, 0.786, 0.85]
TOL = [0.05, 0.10, 0.15]
GAP = [3, 5]
CONFIRM = ['close_above_high', 'bullish_candle', 'higher_low']
MAX_WAIT = [1, 2, 3]

def test_combo(params):
    results = {}
    for asset, df in DATA.items():
        try:
            bt = ElliottICTBacktesterV5(df, params)
            result = bt.run_backtest()
            total = result.wins + result.losses
            results[asset] = {'total': total, 'wins': result.wins, 'wr': result.win_rate if total > 0 else 0}
        except:
            pass
    passing = sum(1 for r in results.values() if r['total'] >= 2 and r['wr'] >= 80)
    with_trades = sum(1 for r in results.values() if r['total'] >= 2)
    return passing, with_trades, results

best = {'passing': 0}
combos = list(product(ZZ, FIB, TOL, GAP, CONFIRM, MAX_WAIT))
print(f"Testing {len(combos)} combinations (R:R=1.0, confirmation entry)...", flush=True)

for i, (zz, fib, tol, gap, conf, wait) in enumerate(combos):
    params = {
        'zz_depth': zz, 'fib_entry_level': fib, 'fib_tolerance': tol,
        'signal_gap': gap, 'rr_ratio': 1.0, 'zz_dev': 0.2,
        'use_confirmation': True, 'confirm_type': conf, 'max_confirm_bars': wait,
    }
    passing, with_trades, results = test_combo(params)
    
    if passing > best['passing']:
        best = {'passing': passing, 'with_trades': with_trades, 'results': results, 'params': params}
        print(f"  NEW BEST: {passing}/20 - ZZ={zz}, Fib={fib}, Conf={conf}, Wait={wait}", flush=True)
    
    if (i+1) % 100 == 0:
        print(f"  {i+1}/{len(combos)} (best: {best['passing']})...", flush=True)

print(f"\n{'='*60}", flush=True)
print(f"BEST V5: {best['passing']}/20 ({best.get('with_trades', 0)} with trades)", flush=True)
p = best.get('params', {})
print(f"ZZ={p.get('zz_depth')}, Fib={p.get('fib_entry_level')}, Tol={p.get('fib_tolerance')}", flush=True)
print(f"Confirm={p.get('confirm_type')}, MaxWait={p.get('max_confirm_bars')}", flush=True)
print(f"{'='*60}", flush=True)

if 'results' in best:
    for asset in sorted(FILES_1H.keys()):
        r = best['results'].get(asset, {'total': 0, 'wins': 0, 'wr': 0})
        if r['total'] >= 2:
            status = "PASS" if r['wr'] >= 80 else "FAIL"
            print(f"  {asset}: {r['wins']}/{r['total']} = {r['wr']:.0f}% [{status}]", flush=True)
        else:
            print(f"  {asset}: {r['total']} trades [NO SIGNAL]", flush=True)
