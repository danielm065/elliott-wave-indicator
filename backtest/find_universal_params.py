"""
Find params that work on ALL assets (or most) for a TF
Target: 85% win rate on 90% of assets
"""
import os
import sys
sys.path.append(os.path.dirname(__file__))

from backtester import ElliottICTBacktester, load_data
from itertools import product
import glob

DATA_DIR = r'C:\Users\danie\projects\elliott-wave-indicator\data'
ASSETS = ['GOOG', 'PLTR', 'MU', 'OSCR', 'RKLB', 'MNQ']

TF_MAP = {
    '1D': ['1D'],
    '4H': ['240', '4H'],
    '1H': ['60', '1H'],
    '30m': [', 30_', '30m'],
    '15m': [', 15_', '15m'],
    '5m': [', 5_', '5m'],
}

def find_file(asset, tf):
    patterns = TF_MAP.get(tf, [tf])
    for f in glob.glob(os.path.join(DATA_DIR, '*.csv')):
        fname = os.path.basename(f).upper()
        if asset.upper() in fname and any(p.upper() in fname for p in patterns):
            return f
    return None

def load_all_data(tf):
    """Load all asset data for a TF"""
    data = {}
    for asset in ASSETS:
        f = find_file(asset, tf)
        if f:
            data[asset] = load_data(f)
    return data

def test_params(data, params):
    """Test params on all assets, return coverage %"""
    ok = 0
    results = {}
    
    for asset, df in data.items():
        try:
            bt = ElliottICTBacktester(df, params)
            result = bt.run_backtest()
            wr = result.win_rate if (result.wins + result.losses) >= 2 else 0
            results[asset] = {'wr': wr, 'w': result.wins, 'l': result.losses}
            if wr >= 85:
                ok += 1
        except:
            results[asset] = {'wr': 0, 'w': 0, 'l': 0}
    
    coverage = ok / len(data) * 100 if data else 0
    return coverage, results

def main():
    tf = sys.argv[1] if len(sys.argv) > 1 else '1D'
    
    print(f"{'='*60}")
    print(f"Finding universal params for {tf}")
    print(f"Target: 85% WR on 90% of assets")
    print(f"{'='*60}")
    
    data = load_all_data(tf)
    print(f"Loaded {len(data)} assets: {list(data.keys())}")
    
    # Search grid
    grid = {
        'zz_depth': [3, 4, 5, 6, 8],
        'zz_dev': [0.1, 0.3, 0.5],
        'signal_gap': [5, 10, 15],
        'fib_entry_level': [0.618, 0.70, 0.75, 0.786, 0.79],
        'rr_ratio': [1.0, 1.5, 2.0],  # Min 1:1, target 2:1
        'use_trend_filter': [True, False],
        'use_rsi_filter': [True, False],
    }
    
    fixed = {
        'use_volume_filter': True,
        'ema_period': 200,
        'rsi_threshold': 50,
        'wave_retrace_min': 0.5,
        'wave_retrace_max': 0.786,
    }
    
    keys = list(grid.keys())
    values = [grid[k] for k in keys]
    total = 1
    for v in values:
        total *= len(v)
    
    print(f"Testing {total} combinations...\n")
    
    best_coverage = 0
    best_params = None
    best_results = None
    candidates = []
    
    tested = 0
    for combo in product(*values):
        params = dict(zip(keys, combo))
        params.update(fixed)
        
        coverage, results = test_params(data, params)
        
        if coverage >= 83:  # Keep good candidates
            candidates.append({
                'params': params.copy(),
                'coverage': coverage,
                'results': results
            })
        
        if coverage > best_coverage:
            best_coverage = coverage
            best_params = params.copy()
            best_results = results
        
        tested += 1
        if tested % 2000 == 0:
            print(f"Progress: {tested}/{total} | Best coverage: {best_coverage:.0f}%")
    
    print(f"\n{'='*60}")
    print(f"BEST RESULT: {best_coverage:.0f}% coverage")
    print(f"{'='*60}")
    print(f"Params:")
    print(f"  zz_depth: {best_params['zz_depth']}")
    print(f"  zz_dev: {best_params['zz_dev']}")
    print(f"  signal_gap: {best_params['signal_gap']}")
    print(f"  fib_entry: {best_params['fib_entry_level']}")
    print(f"  rr_ratio: {best_params['rr_ratio']}")
    print(f"  trend_filter: {best_params['use_trend_filter']}")
    print(f"  rsi_filter: {best_params['use_rsi_filter']}")
    
    print(f"\nResults per asset:")
    for asset, r in best_results.items():
        status = "OK" if r['wr'] >= 85 else "FAIL"
        print(f"  {asset}: {r['w']}W/{r['l']}L = {r['wr']:.1f}% [{status}]")
    
    # Show other good candidates
    if len(candidates) > 1:
        print(f"\n{len(candidates)} candidates with 83%+ coverage:")
        for c in sorted(candidates, key=lambda x: -x['coverage'])[:5]:
            p = c['params']
            print(f"  {c['coverage']:.0f}%: zz={p['zz_depth']}, fib={p['fib_entry_level']}, rr={p['rr_ratio']}, trend={p['use_trend_filter']}")

if __name__ == '__main__':
    main()
