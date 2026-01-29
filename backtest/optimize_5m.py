"""
Optimize 5m only
"""
import os
import sys
sys.path.append(os.path.dirname(__file__))

from backtester import ElliottICTBacktester, load_data
from itertools import product
import glob

GRID = {
    'zz_depth': [2, 3, 4, 5],
    'zz_dev': [0.01, 0.02, 0.03],
    'signal_gap': [5, 8, 10, 15],
    'fib_entry_level': [0.618, 0.70, 0.75, 0.786],
    'rr_ratio': [0.8, 1.0, 1.2],
    'use_trend_filter': [True, False],
    'use_rsi_filter': [True, False],
}

def optimize_5m():
    data_dir = r'C:\Users\danie\projects\elliott-wave-indicator\data'
    
    # Find all 5m files (both formats)
    files = []
    files.extend(glob.glob(os.path.join(data_dir, '*_5m.csv')))
    files.extend(glob.glob(os.path.join(data_dir, '*, 5_*.csv')))
    files.extend(glob.glob(os.path.join(data_dir, '*5m*.csv')))
    files = list(set(files))  # Remove duplicates
    
    if not files:
        print("No 5m files found!")
        return None
    
    print(f"Found {len(files)} 5m files:")
    for f in files:
        print(f"  - {os.path.basename(f)}")
    
    keys = list(GRID.keys())
    values = [GRID[k] for k in keys]
    total = 1
    for v in values:
        total *= len(v)
    
    print(f"\nTesting {total} combinations...")
    
    best_wr = 0
    best_params = None
    best_w, best_l = 0, 0
    
    tested = 0
    for combo in product(*values):
        params = dict(zip(keys, combo))
        
        total_w, total_l = 0, 0
        for f in files:
            try:
                df = load_data(f)
                bt = ElliottICTBacktester(df, params)
                result = bt.run_backtest()
                total_w += result.wins
                total_l += result.losses
            except Exception as e:
                pass
        
        if total_w + total_l >= 10:
            wr = total_w / (total_w + total_l) * 100
            if wr > best_wr:
                best_wr = wr
                best_params = params.copy()
                best_w, best_l = total_w, total_l
        
        tested += 1
        if tested % 500 == 0:
            print(f"Progress: {tested}/{total} | Best: {best_wr:.1f}%")
    
    return {'wr': best_wr, 'params': best_params, 'w': best_w, 'l': best_l}

if __name__ == '__main__':
    print("="*60)
    print("OPTIMIZING 5m TIMEFRAME")
    print("="*60)
    
    result = optimize_5m()
    
    if result and result['params']:
        mark = "[OK]" if result['wr'] >= 85 else "[--]"
        print(f"\n{mark} Best: {result['wr']:.1f}% ({result['w']}W/{result['l']}L)")
        p = result['params']
        print(f"Params: zz={p['zz_depth']}, dev={p['zz_dev']}, gap={p['signal_gap']}, fib={p['fib_entry_level']}, rr={p['rr_ratio']}, trend={p['use_trend_filter']}, rsi={p['use_rsi_filter']}")
    else:
        print("\nNo valid results found")
