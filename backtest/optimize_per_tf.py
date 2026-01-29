"""
Optimize parameters for EACH timeframe across ALL assets
Goal: Find params that work best for each TF on all stocks combined
"""
import os
import sys
sys.path.append(os.path.dirname(__file__))

from backtester import ElliottICTBacktester, load_data
from itertools import product
import glob

DATA_DIR = r'C:\Users\danie\projects\elliott-wave-indicator\data'

# Optimization grid
GRID = {
    'zz_depth': [3, 4, 5, 6, 8],
    'zz_dev': [0.01, 0.1, 0.3, 0.5],
    'signal_gap': [3, 5, 8, 10, 15],
    'fib_entry_level': [0.618, 0.70, 0.75, 0.786, 0.79],
    'rr_ratio': [0.5, 0.8, 1.0, 1.5, 2.0],
    'use_trend_filter': [True, False],
    'use_rsi_filter': [True, False],
}

# Fixed params
FIXED = {
    'use_volume_filter': True,
    'ema_period': 200,
    'rsi_threshold': 50,
    'wave_retrace_min': 0.5,
    'wave_retrace_max': 0.786,
}

TF_PATTERNS = {
    'Daily': ['*1D*.csv', '*_1D_*.csv'],
    '4H': ['*240*.csv', '*_4H*.csv'],
    '1H': ['*60*.csv', '*_1H*.csv'],
    '30m': ['*30*.csv', '*_30m*.csv'],
    '15m': ['*15*.csv', '*_15m*.csv'],
    '5m': ['*, 5_*.csv', '*_5m*.csv'],
}

def get_files_for_tf(tf_name):
    """Get all data files for a timeframe"""
    files = []
    for pattern in TF_PATTERNS.get(tf_name, []):
        files.extend(glob.glob(os.path.join(DATA_DIR, pattern)))
    # Remove duplicates
    return list(set(files))

def test_params_on_tf(params, files):
    """Test parameters on all files for a TF, return combined win rate"""
    total_w, total_l = 0, 0
    
    for f in files:
        try:
            df = load_data(f)
            bt = ElliottICTBacktester(df, params)
            result = bt.run_backtest()
            total_w += result.wins
            total_l += result.losses
        except:
            pass
    
    if total_w + total_l < 5:  # Minimum trades required
        return 0, 0, 0
    
    wr = total_w / (total_w + total_l) * 100
    return wr, total_w, total_l

def optimize_tf(tf_name):
    """Find best params for a timeframe"""
    files = get_files_for_tf(tf_name)
    
    if not files:
        print(f"  No files for {tf_name}")
        return None
    
    print(f"  Files: {len(files)}")
    for f in files:
        print(f"    - {os.path.basename(f)}")
    
    # Generate all combinations
    keys = list(GRID.keys())
    values = [GRID[k] for k in keys]
    total_combos = 1
    for v in values:
        total_combos *= len(v)
    
    print(f"  Testing {total_combos} combinations...")
    
    best_wr = 0
    best_params = None
    best_w, best_l = 0, 0
    
    tested = 0
    for combo in product(*values):
        params = dict(zip(keys, combo))
        params.update(FIXED)
        
        wr, w, l = test_params_on_tf(params, files)
        
        if wr > best_wr:
            best_wr = wr
            best_params = params.copy()
            best_w, best_l = w, l
        
        tested += 1
        if tested % 1000 == 0:
            print(f"  Progress: {tested}/{total_combos} | Best: {best_wr:.1f}%")
    
    return {
        'tf': tf_name,
        'win_rate': best_wr,
        'wins': best_w,
        'losses': best_l,
        'params': best_params
    }

def main():
    print("="*80)
    print("OPTIMIZING EACH TIMEFRAME (ALL ASSETS COMBINED)")
    print("="*80)
    
    results = {}
    
    for tf in ['Daily', '4H', '1H', '30m', '15m', '5m']:
        print(f"\n{'='*60}")
        print(f"OPTIMIZING {tf}")
        print(f"{'='*60}")
        
        result = optimize_tf(tf)
        
        if result and result['params']:
            results[tf] = result
            mark = "[OK]" if result['win_rate'] >= 65 else "[--]"
            print(f"\n  {mark} Best: {result['win_rate']:.1f}% ({result['wins']}W/{result['losses']}L)")
            p = result['params']
            print(f"  zz_depth: {p['zz_depth']}")
            print(f"  zz_dev: {p['zz_dev']}")
            print(f"  signal_gap: {p['signal_gap']}")
            print(f"  fib_entry: {p['fib_entry_level']}")
            print(f"  rr_ratio: {p['rr_ratio']}")
            print(f"  trend_filter: {p['use_trend_filter']}")
            print(f"  rsi_filter: {p['use_rsi_filter']}")
    
    # Final summary
    print("\n" + "="*80)
    print("FINAL OPTIMIZED PARAMETERS BY TIMEFRAME")
    print("="*80)
    
    for tf in ['Daily', '4H', '1H', '30m', '15m', '5m']:
        if tf in results:
            r = results[tf]
            mark = "[OK]" if r['win_rate'] >= 65 else "[--]"
            p = r['params']
            print(f"\n{tf} {mark} {r['win_rate']:.1f}% ({r['wins']}W/{r['losses']}L):")
            print(f"  zz={p['zz_depth']}, dev={p['zz_dev']}, gap={p['signal_gap']}, fib={p['fib_entry_level']}, rr={p['rr_ratio']}, trend={p['use_trend_filter']}, rsi={p['use_rsi_filter']}")

if __name__ == '__main__':
    main()
