"""
Target: 16/20 assets above 80% win rate
Need to get more signals AND more passing
"""
import sys
sys.path.insert(0, r'C:\Users\danie\projects\elliott-wave-indicator\backtest')

from backtester import ElliottICTBacktester, load_data
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

BASE = {
    'fib_entry_level': 0.786,
    'use_rsi_filter': True,
    'use_trend_filter': True,
    'use_volume_filter': True,
    'ema_period': 200,
    'signal_gap': 5,
    'zz_dev': 0.2,
}

# Load data once
print("Loading data...", flush=True)
DATA = {}
for asset, file in FILES_4H.items():
    path = DATA_DIR / file
    if path.exists():
        try:
            DATA[asset] = load_data(str(path))
        except:
            pass
print(f"Loaded {len(DATA)} assets", flush=True)

# More aggressive grid to get more signals
ZZ_VALUES = [2, 3]  # Lower = more signals
RR_VALUES = [0.5, 0.75, 1.0]  # Lower = easier to hit TP
RSI_VALUES = [40, 50, 60, 70]  # Higher = more signals
TOL_VALUES = [0.10, 0.15, 0.20, 0.25, 0.30]  # Higher = more signals
TREND_FILTER = [True, False]  # False = more signals

def test_combo(zz, rr, rsi, tol, trend):
    params = {
        **BASE, 
        'zz_depth': zz, 
        'rr_ratio': rr, 
        'rsi_threshold': rsi, 
        'fib_tolerance': tol,
        'use_trend_filter': trend
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
    
    # Count passing at 80% with 2+ trades
    passing = sum(1 for a, r in results.items() if r['total'] >= 2 and r['wr'] >= 80)
    with_trades = sum(1 for a, r in results.items() if r['total'] >= 2)
    
    return passing, with_trades, results

def main():
    print(f"\nTarget: 16/20 assets above 80% WR", flush=True)
    
    combos = list(product(ZZ_VALUES, RR_VALUES, RSI_VALUES, TOL_VALUES, TREND_FILTER))
    print(f"Testing {len(combos)} combinations...", flush=True)
    
    best_results = []
    
    for i, (zz, rr, rsi, tol, trend) in enumerate(combos):
        passing, with_trades, results = test_combo(zz, rr, rsi, tol, trend)
        
        # Track if we get 16+ passing
        if passing >= 14:  # Track good results
            best_results.append({
                'zz': zz, 'rr': rr, 'rsi': rsi, 'tol': tol, 'trend': trend,
                'passing': passing, 'with_trades': with_trades,
                'results': results
            })
        
        if (i + 1) % 50 == 0:
            print(f"  {i+1}/{len(combos)} tested...", flush=True)
    
    # Sort by passing count
    best_results.sort(key=lambda x: (-x['passing'], -x['with_trades']))
    
    print(f"\n{'='*70}", flush=True)
    print(f"TOP RESULTS", flush=True)
    print(f"{'='*70}", flush=True)
    
    if not best_results:
        print("No combinations achieved 14+ passing", flush=True)
        return
    
    for i, r in enumerate(best_results[:10]):
        trend_str = "ON" if r['trend'] else "OFF"
        print(f"\n{i+1}. Passing: {r['passing']}/20 ({r['with_trades']} with trades)", flush=True)
        print(f"   Params: ZZ={r['zz']}, RR={r['rr']}, RSI<{r['rsi']}, Tol={r['tol']}, Trend={trend_str}", flush=True)
        
        # Show failing assets
        failing = [(a, res['wr']) for a, res in r['results'].items() if res['total'] >= 2 and res['wr'] < 80]
        no_signal = [a for a, res in r['results'].items() if res['total'] < 2]
        
        if failing:
            fail_str = ', '.join(f"{a}({wr:.0f}%)" for a, wr in failing)
            print(f"   Failing: {fail_str}", flush=True)
        if no_signal:
            print(f"   No signals: {', '.join(no_signal)}", flush=True)
    
    # Show best result details
    best = best_results[0]
    trend_str = "ON" if best['trend'] else "OFF"
    print(f"\n{'='*70}", flush=True)
    print(f"BEST RESULT", flush=True)
    print(f"{'='*70}", flush=True)
    print(f"Params: ZZ={best['zz']}, RR={best['rr']}, RSI<{best['rsi']}, Tol={best['tol']}, Trend={trend_str}", flush=True)
    print(f"Passing: {best['passing']}/20", flush=True)
    
    print("\nAll 20 assets:", flush=True)
    for asset in sorted(FILES_4H.keys()):
        r = best['results'].get(asset, {'total': 0, 'wins': 0, 'wr': 0})
        if r['total'] >= 2:
            status = "PASS" if r['wr'] >= 80 else "FAIL"
            print(f"  {asset}: {r['wins']}/{r['total']} = {r['wr']:.0f}% [{status}]", flush=True)
        else:
            print(f"  {asset}: {r['total']} trades [NO SIGNAL]", flush=True)

if __name__ == '__main__':
    main()
