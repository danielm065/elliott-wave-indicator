"""
Grid search for 4H optimization
Test all combinations and find best overall coverage
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

# Load all data once
print("Loading data...")
DATA = {}
for asset, file in FILES_4H.items():
    path = DATA_DIR / file
    if path.exists():
        try:
            DATA[asset] = load_data(str(path))
        except:
            pass
print(f"Loaded {len(DATA)} assets")

# Parameter grid
GRID = {
    'zz_depth': [3, 4, 5],
    'rr_ratio': [1.0, 1.5, 2.0],
    'rsi_threshold': [40, 45, 50, 55],
    'fib_tolerance': [0.15, 0.20, 0.25, 0.30],
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

def test_combo(params):
    """Test all assets, return (passing, total, details)"""
    full_params = {**BASE, **params}
    results = {}
    
    for asset, df in DATA.items():
        try:
            bt = ElliottICTBacktester(df, full_params)
            result = bt.run_backtest()
            total = result.wins + result.losses
            results[asset] = {
                'total': total,
                'wins': result.wins,
                'wr': result.win_rate if total >= 2 else None
            }
        except:
            pass
    
    passing = 0
    with_trades = 0
    for asset, r in results.items():
        if r['total'] >= 2:
            with_trades += 1
            if r['wr'] and r['wr'] >= 85:
                passing += 1
    
    return passing, with_trades, results

def main():
    print("="*60)
    print("4H GRID SEARCH")
    print("="*60)
    
    keys = list(GRID.keys())
    combos = list(product(*[GRID[k] for k in keys]))
    print(f"Testing {len(combos)} combinations...")
    
    best_coverage = 0
    best_params = None
    best_results = None
    
    results_list = []
    
    for i, combo in enumerate(combos):
        params = dict(zip(keys, combo))
        passing, total, details = test_combo(params)
        coverage = passing/total*100 if total > 0 else 0
        
        results_list.append({
            'params': params,
            'passing': passing,
            'total': total,
            'coverage': coverage,
            'details': details
        })
        
        if coverage > best_coverage:
            best_coverage = coverage
            best_params = params
            best_results = details
        
        if (i+1) % 50 == 0:
            print(f"  {i+1}/{len(combos)} tested, best so far: {best_coverage:.0f}%")
    
    # Sort by coverage
    results_list.sort(key=lambda x: (-x['coverage'], -x['passing']))
    
    print("\n" + "="*60)
    print("TOP 10 COMBINATIONS")
    print("="*60)
    
    for i, r in enumerate(results_list[:10]):
        p = r['params']
        print(f"\n{i+1}. Coverage: {r['passing']}/{r['total']} = {r['coverage']:.0f}%")
        print(f"   ZZ={p['zz_depth']}, RR={p['rr_ratio']}, RSI<{p['rsi_threshold']}, Tol={p['fib_tolerance']}")
    
    print("\n" + "="*60)
    print("BEST RESULT DETAILS")
    print("="*60)
    print(f"\nParams: ZZ={best_params['zz_depth']}, RR={best_params['rr_ratio']}, RSI<{best_params['rsi_threshold']}, Tol={best_params['fib_tolerance']}")
    print(f"Coverage: {results_list[0]['passing']}/{results_list[0]['total']} = {results_list[0]['coverage']:.0f}%")
    
    print("\nAsset details:")
    for asset, r in sorted(best_results.items()):
        if r['total'] >= 2:
            status = "PASS" if r['wr'] and r['wr'] >= 85 else "FAIL"
            print(f"  {asset}: {r['wins']}/{r['total']} = {r['wr']:.0f}% {status}")
    
    print("\nFailing assets:")
    for asset, r in sorted(best_results.items()):
        if r['total'] >= 2 and (not r['wr'] or r['wr'] < 85):
            print(f"  {asset}: {r['wins']}/{r['total']} = {r['wr']:.0f}%")

if __name__ == '__main__':
    main()
