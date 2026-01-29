"""
Test backtester v2 with Longs + Shorts + FVG patterns
"""
import sys
sys.path.insert(0, r'C:\Users\danie\projects\elliott-wave-indicator\backtest')

from backtester_v2 import ElliottICTBacktesterV2, load_data
from pathlib import Path
from itertools import product

DATA_DIR = Path(r'C:\Users\danie\projects\elliott-wave-indicator\data')

FILES_4H = {
    'AMD': 'BATS_AMD, 240_c2599.csv',
    'ASTS': 'BATS_ASTS, 240_a0ab9.csv',
    'BA': 'BATS_BA, 240_69b3b.csv',
    'CRWV': 'BATS_CRWV, 240_ed96a.csv',
    'GOOG': 'BATS_GOOG, 240_52190.csv',
    'HIMS': 'BATS_HIMS, 240_9ad5f.csv',
    'IBKR': 'BATS_IBKR, 240_eef24.csv',
    'INTC': 'BATS_INTC, 240_43ac7.csv',
    'KRNT': 'BATS_KRNT, 240_38050.csv',
    'MU': 'BATS_MU, 240_6d83f.csv',
    'OSCR': 'BATS_OSCR, 240_69bf3.csv',
    'PLTR': 'BATS_PLTR, 240_4ba34.csv',
    'RKLB': 'BATS_RKLB, 240_9e8cf.csv',
    'TTWO': 'BATS_TTWO, 240_ba1c1.csv',
    'ADAUSDT': 'BINANCE_ADAUSDT, 240_200b2.csv',
    'BTCUSDT': 'BINANCE_BTCUSDT, 240_fe0b8.csv',
    'ETHUSD': 'BINANCE_ETHUSD, 240_aff0c.csv',
    'MNQ': 'CME_MINI_MNQ1!, 240.csv',
    'SOLUSD': 'COINBASE_SOLUSD, 240_b1f00.csv',
    'USDILS': 'FOREXCOM_USDILS, 240_3fecc.csv',
}

# Load data
print("Loading data...", flush=True)
DATA = {}
for asset, file in FILES_4H.items():
    path = DATA_DIR / file
    if path.exists():
        try:
            DATA[asset] = load_data(str(path))
        except Exception as e:
            print(f"Error loading {asset}: {e}", flush=True)
print(f"Loaded {len(DATA)} assets", flush=True)

# Test params with shorts enabled
ZZ_VALUES = [2, 3]
RR_VALUES = [1.0, 1.5]
RSI_VALUES = [40, 50]
TOL_VALUES = [0.10, 0.15, 0.20]
FVG_OPTIONS = [True, False]

def test_combo(params):
    results = {}
    for asset, df in DATA.items():
        try:
            bt = ElliottICTBacktesterV2(df, params)
            result = bt.run_backtest()
            total = result.wins + result.losses
            results[asset] = {
                'total': total,
                'wins': result.wins,
                'losses': result.losses,
                'wr': result.win_rate if total > 0 else 0,
                'long_w': result.long_wins,
                'long_l': result.long_losses,
                'short_w': result.short_wins,
                'short_l': result.short_losses
            }
        except:
            pass
    
    passing = sum(1 for a, r in results.items() if r['total'] >= 2 and r['wr'] >= 80)
    with_trades = sum(1 for a, r in results.items() if r['total'] >= 2)
    
    return passing, with_trades, results

def main():
    print(f"\n{'='*70}", flush=True)
    print("Testing Backtester V2: Longs + Shorts + FVG", flush=True)
    print(f"{'='*70}", flush=True)
    
    combos = list(product(ZZ_VALUES, RR_VALUES, RSI_VALUES, TOL_VALUES, FVG_OPTIONS))
    print(f"Testing {len(combos)} combinations...", flush=True)
    
    best_results = []
    
    for i, (zz, rr, rsi, tol, fvg) in enumerate(combos):
        params = {
            'zz_depth': zz,
            'rr_ratio': rr,
            'rsi_threshold': rsi,
            'fib_tolerance': tol,
            'fib_entry_level': 0.786,
            'use_rsi_filter': True,
            'use_trend_filter': True,
            'ema_period': 200,
            'signal_gap': 5,
            'zz_dev': 0.2,
            'enable_longs': True,
            'enable_shorts': True,
            'enable_fvg': fvg,
        }
        
        passing, with_trades, results = test_combo(params)
        
        if passing >= 10:
            best_results.append({
                'zz': zz, 'rr': rr, 'rsi': rsi, 'tol': tol, 'fvg': fvg,
                'passing': passing, 'with_trades': with_trades,
                'results': results
            })
        
        if (i + 1) % 20 == 0:
            print(f"  {i+1}/{len(combos)} tested...", flush=True)
    
    best_results.sort(key=lambda x: (-x['passing'], -x['with_trades']))
    
    print(f"\n{'='*70}", flush=True)
    print("TOP RESULTS (Longs + Shorts)", flush=True)
    print(f"{'='*70}", flush=True)
    
    for i, r in enumerate(best_results[:10]):
        fvg_str = "FVG:ON" if r['fvg'] else "FVG:OFF"
        print(f"\n{i+1}. Passing: {r['passing']}/20 ({r['with_trades']} with trades)", flush=True)
        print(f"   ZZ={r['zz']}, RR={r['rr']}, RSI<{r['rsi']}, Tol={r['tol']}, {fvg_str}", flush=True)
        
        failing = [(a, res['wr']) for a, res in r['results'].items() if res['total'] >= 2 and res['wr'] < 80]
        no_signal = [a for a, res in r['results'].items() if res['total'] < 2]
        
        if failing:
            print(f"   Failing: {', '.join(f'{a}({wr:.0f}%)' for a, wr in failing)}", flush=True)
        if no_signal:
            print(f"   No signals: {', '.join(no_signal)}", flush=True)
    
    if best_results:
        best = best_results[0]
        print(f"\n{'='*70}", flush=True)
        print(f"BEST: {best['passing']}/20", flush=True)
        print(f"{'='*70}", flush=True)
        
        total_longs = sum(r['long_w'] + r['long_l'] for r in best['results'].values())
        total_shorts = sum(r['short_w'] + r['short_l'] for r in best['results'].values())
        long_wr = sum(r['long_w'] for r in best['results'].values()) / total_longs * 100 if total_longs > 0 else 0
        short_wr = sum(r['short_w'] for r in best['results'].values()) / total_shorts * 100 if total_shorts > 0 else 0
        
        print(f"\nLong trades: {total_longs} ({long_wr:.0f}% WR)", flush=True)
        print(f"Short trades: {total_shorts} ({short_wr:.0f}% WR)", flush=True)
        
        print("\nAll assets:", flush=True)
        for asset in sorted(FILES_4H.keys()):
            r = best['results'].get(asset, {'total': 0, 'wins': 0, 'wr': 0, 'long_w': 0, 'long_l': 0, 'short_w': 0, 'short_l': 0})
            if r['total'] >= 2:
                status = "PASS" if r['wr'] >= 80 else "FAIL"
                l_str = f"L:{r['long_w']}/{r['long_w']+r['long_l']}" if r['long_w']+r['long_l'] > 0 else ""
                s_str = f"S:{r['short_w']}/{r['short_w']+r['short_l']}" if r['short_w']+r['short_l'] > 0 else ""
                print(f"  {asset}: {r['wins']}/{r['total']} = {r['wr']:.0f}% [{status}] {l_str} {s_str}", flush=True)
            else:
                print(f"  {asset}: {r['total']} trades [NO SIGNAL]", flush=True)

if __name__ == '__main__':
    main()
