"""
Deep test single asset with multiple param combinations
"""
import os
import sys
sys.path.append(os.path.dirname(__file__))

from backtester import ElliottICTBacktester, load_data
from itertools import product
import glob

DATA_DIR = r'C:\Users\danie\projects\elliott-wave-indicator\data'

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

def test_combinations(asset, tf):
    """Test many param combinations to find what works"""
    filepath = find_file(asset, tf)
    if not filepath:
        print(f"No file found for {asset} {tf}")
        return
    
    print(f"\n{'='*60}")
    print(f"DEEP TEST: {asset} {tf}")
    print(f"{'='*60}")
    
    df = load_data(filepath)
    
    # Grid to test
    grid = {
        'zz_depth': [3, 5, 8],
        'fib_entry_level': [0.618, 0.75, 0.79],
        'rr_ratio': [0.5, 0.8, 1.0],
        'use_trend_filter': [True, False],
    }
    
    fixed = {
        'zz_dev': 0.5,
        'signal_gap': 10,
        'use_rsi_filter': True,
        'use_volume_filter': True,
        'ema_period': 200,
        'rsi_threshold': 50,
        'wave_retrace_min': 0.5,
        'wave_retrace_max': 0.786,
    }
    
    best_wr = 0
    best_params = None
    best_trades = 0
    
    keys = list(grid.keys())
    values = [grid[k] for k in keys]
    
    results_85 = []
    
    for combo in product(*values):
        params = dict(zip(keys, combo))
        params.update(fixed)
        
        bt = ElliottICTBacktester(df, params)
        result = bt.run_backtest()
        
        if result.wins + result.losses >= 2:  # Min trades
            wr = result.win_rate
            
            if wr >= 85:
                results_85.append({
                    'params': params.copy(),
                    'wr': wr,
                    'wins': result.wins,
                    'losses': result.losses
                })
            
            if wr > best_wr or (wr == best_wr and result.total > best_trades):
                best_wr = wr
                best_params = params.copy()
                best_trades = result.total
    
    print(f"\nBest result: {best_wr:.1f}% with params:")
    print(f"  zz_depth: {best_params['zz_depth']}")
    print(f"  fib_entry: {best_params['fib_entry_level']}")
    print(f"  rr_ratio: {best_params['rr_ratio']}")
    print(f"  trend_filter: {best_params['use_trend_filter']}")
    
    if results_85:
        print(f"\n{len(results_85)} combinations achieved 85%+:")
        for r in results_85[:5]:  # Show top 5
            p = r['params']
            print(f"  {r['wr']:.1f}% ({r['wins']}W/{r['losses']}L): zz={p['zz_depth']}, fib={p['fib_entry_level']}, rr={p['rr_ratio']}, trend={p['use_trend_filter']}")
    else:
        print("\nNo combination achieved 85%!")

if __name__ == '__main__':
    asset = sys.argv[1] if len(sys.argv) > 1 else 'OSCR'
    tf = sys.argv[2] if len(sys.argv) > 2 else '1D'
    test_combinations(asset, tf)
