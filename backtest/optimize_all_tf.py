"""
Optimize ALL timeframes - smaller grid, faster execution
Results saved to file
"""
import os
import sys
sys.path.append(os.path.dirname(__file__))

from backtester import ElliottICTBacktester, load_data
from itertools import product
import glob
import json
from datetime import datetime

# Smaller grid for faster execution
GRID = {
    'zz_depth': [3, 4, 5],
    'zz_dev': [0.03, 0.05, 0.1],
    'signal_gap': [3, 5, 8],
    'fib_entry_level': [0.70, 0.786, 0.79],
    'rr_ratio': [1.5, 2.0],
    'use_trend_filter': [True, False],
}

TF_PATTERNS = {
    '1D': '*1D*.csv',
    '4H': '*240*.csv',
    '1H': '*60*.csv',
    '30m': '*30*.csv',
    '15m': '*15*.csv',
    '5m': '*, 5_*.csv',
}

def get_asset(filename):
    name = os.path.basename(filename)
    for asset in ['PLTR', 'GOOG', 'RKLB', 'OSCR', 'MNQ', 'NQ', 'MU']:
        if asset in name:
            return asset
    return 'UNKNOWN'

def optimize_tf(tf_name, pattern):
    data_dir = r'C:\Users\danie\projects\elliott-wave-indicator\data'
    files = glob.glob(os.path.join(data_dir, pattern))
    
    if not files:
        return None
    
    keys = list(GRID.keys())
    values = [GRID[k] for k in keys]
    
    best_wr = 0
    best_params = None
    best_results = None
    
    for combo in product(*values):
        params = dict(zip(keys, combo))
        
        total_w, total_l = 0, 0
        results = {}
        
        for f in files:
            try:
                df = load_data(f)
                bt = ElliottICTBacktester(df, params)
                result = bt.run_backtest()
                asset = get_asset(f)
                results[asset] = {'wr': result.win_rate, 'w': result.wins, 'l': result.losses}
                total_w += result.wins
                total_l += result.losses
            except:
                pass
        
        if total_w + total_l >= 5:
            wr = total_w / (total_w + total_l) * 100
            if wr > best_wr:
                best_wr = wr
                best_params = params.copy()
                best_results = results.copy()
    
    return {
        'tf': tf_name,
        'wr': best_wr,
        'params': best_params,
        'results': best_results
    }

def main():
    print("=" * 60)
    print("OPTIMIZING ALL TIMEFRAMES")
    print("=" * 60)
    
    all_results = {}
    
    for tf_name, pattern in TF_PATTERNS.items():
        print(f"\n{tf_name}...")
        result = optimize_tf(tf_name, pattern)
        
        if result:
            all_results[tf_name] = result
            mark = "[OK]" if result['wr'] >= 85 else "[--]"
            print(f"  {mark} Best WR: {result['wr']:.1f}%")
            if result['params']:
                p = result['params']
                print(f"  Params: zz={p['zz_depth']}, dev={p['zz_dev']}, gap={p['signal_gap']}, fib={p['fib_entry_level']}, rr={p['rr_ratio']}, trend={p['use_trend_filter']}")
        else:
            print(f"  No data found")
    
    # Save results
    output_file = r'C:\Users\danie\projects\elliott-wave-indicator\OPTIMIZATION_RESULTS.json'
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    for tf, data in all_results.items():
        mark = "[OK]" if data['wr'] >= 85 else "[--]" if data['wr'] >= 70 else "[XX]"
        print(f"{mark} {tf}: {data['wr']:.1f}%")
    
    print(f"\nResults saved to: {output_file}")

if __name__ == '__main__':
    main()
