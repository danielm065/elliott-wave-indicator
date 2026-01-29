"""
Optimize 30m, 15m, 5m - Target 85%+
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

def get_asset(f):
    name = os.path.basename(f)
    for a in ['PLTR', 'GOOG', 'RKLB', 'OSCR', 'MNQ', 'NQ', 'MU']:
        if a in name:
            return a
    return 'UNK'

def optimize_tf(tf_name, pattern):
    data_dir = r'C:\Users\danie\projects\elliott-wave-indicator\data'
    files = glob.glob(os.path.join(data_dir, pattern))
    
    if not files:
        print(f"  No files found for {tf_name}")
        return None
    
    print(f"  Found {len(files)} files")
    
    keys = list(GRID.keys())
    values = [GRID[k] for k in keys]
    total = 1
    for v in values:
        total *= len(v)
    
    print(f"  Testing {total} combinations...")
    
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
            except:
                pass
        
        if total_w + total_l >= 10:
            wr = total_w / (total_w + total_l) * 100
            if wr > best_wr:
                best_wr = wr
                best_params = params.copy()
                best_w, best_l = total_w, total_l
        
        tested += 1
        if tested % 500 == 0:
            print(f"  Progress: {tested}/{total} | Best: {best_wr:.1f}%")
    
    return {'wr': best_wr, 'params': best_params, 'w': best_w, 'l': best_l}

def main():
    tfs = [
        ('30m', '*30*.csv'),
        ('15m', '*15*.csv'),
        ('5m', '*, 5_*.csv'),
    ]
    
    results = {}
    
    for tf_name, pattern in tfs:
        print(f"\n{'='*60}")
        print(f"OPTIMIZING {tf_name}")
        print(f"{'='*60}")
        
        result = optimize_tf(tf_name, pattern)
        
        if result and result['params']:
            results[tf_name] = result
            mark = "[OK]" if result['wr'] >= 85 else "[--]"
            print(f"\n  {mark} Best: {result['wr']:.1f}% ({result['w']}W/{result['l']}L)")
            p = result['params']
            print(f"  Params: zz={p['zz_depth']}, dev={p['zz_dev']}, gap={p['signal_gap']}, fib={p['fib_entry_level']}, rr={p['rr_ratio']}, trend={p['use_trend_filter']}, rsi={p.get('use_rsi_filter')}")
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    for tf, data in results.items():
        mark = "[OK]" if data['wr'] >= 85 else "[--]"
        print(f"{mark} {tf}: {data['wr']:.1f}% ({data['w']}W/{data['l']}L)")

if __name__ == '__main__':
    main()
