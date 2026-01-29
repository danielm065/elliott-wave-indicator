"""
Deep 1H Optimization - Target 85%+
Current best: 80.3% with R:R 1:1
"""
import os
import sys
sys.path.append(os.path.dirname(__file__))

from backtester import ElliottICTBacktester, load_data
from itertools import product
import glob

# Extended grid for 1H
GRID = {
    'zz_depth': [2, 3, 4, 5],
    'zz_dev': [0.01, 0.02, 0.03, 0.05],
    'signal_gap': [5, 8, 10, 15],
    'fib_entry_level': [0.618, 0.70, 0.75, 0.786, 0.79],
    'rr_ratio': [0.8, 1.0, 1.2],
    'use_trend_filter': [True, False],
    'use_rsi_filter': [True, False],
}

def get_1h_files():
    data_dir = r'C:\Users\danie\projects\elliott-wave-indicator\data'
    return glob.glob(os.path.join(data_dir, '*60*.csv'))

def get_asset(f):
    name = os.path.basename(f)
    for a in ['PLTR', 'GOOG', 'RKLB', 'OSCR', 'MNQ', 'NQ', 'MU']:
        if a in name:
            return a
    return 'UNK'

def main():
    files = get_1h_files()
    print(f"Found {len(files)} 1H files")
    
    keys = list(GRID.keys())
    values = [GRID[k] for k in keys]
    total = 1
    for v in values:
        total *= len(v)
    
    print(f"Testing {total} combinations...")
    
    best_wr = 0
    best_params = None
    best_results = None
    top5 = []
    
    tested = 0
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
        
        if total_w + total_l >= 10:
            wr = total_w / (total_w + total_l) * 100
            if wr > best_wr:
                best_wr = wr
                best_params = params.copy()
                best_results = results.copy()
                
                top5.append({'wr': wr, 'params': params.copy(), 'w': total_w, 'l': total_l})
                top5 = sorted(top5, key=lambda x: x['wr'], reverse=True)[:5]
        
        tested += 1
        if tested % 500 == 0:
            print(f"Progress: {tested}/{total} | Best: {best_wr:.1f}%")
    
    print(f"\nDone! Best: {best_wr:.1f}%")
    
    print("\n" + "=" * 60)
    print("TOP 5 RESULTS FOR 1H")
    print("=" * 60)
    
    for i, r in enumerate(top5):
        p = r['params']
        print(f"\n#{i+1}: {r['wr']:.1f}% ({r['w']}W/{r['l']}L)")
        print(f"  zz={p['zz_depth']}, dev={p['zz_dev']}, gap={p['signal_gap']}, fib={p['fib_entry_level']}, rr={p['rr_ratio']}, trend={p['use_trend_filter']}, rsi={p.get('use_rsi_filter', False)}")
    
    if best_params and best_results:
        print("\n" + "=" * 60)
        print("BEST 1H PARAMETERS")
        print("=" * 60)
        print(f"WR: {best_wr:.1f}%")
        for k, v in best_params.items():
            print(f"  {k}: {v}")
        
        print("\nPer asset:")
        for asset, stats in sorted(best_results.items()):
            mark = "[OK]" if stats['wr'] >= 85 else "[--]" if stats['wr'] >= 70 else "[XX]"
            print(f"  {mark} {asset}: {stats['wr']:.1f}%")

if __name__ == '__main__':
    main()
