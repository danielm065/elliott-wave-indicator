"""
Deep Optimization - Find the BEST parameters for each TF
"""
import os
import sys
sys.path.append(os.path.dirname(__file__))

from backtester import ElliottICTBacktester, load_data
from itertools import product
import glob

# Comprehensive parameter grid
FULL_GRID = {
    'zz_depth': [3, 4, 5, 6, 8],
    'zz_dev': [0.1, 0.2, 0.3, 0.5],
    'signal_gap': [3, 5, 8, 10],
    'fib_entry_level': [0.618, 0.70, 0.786, 0.79],
    'rr_ratio': [1.5, 2.0, 2.5],
    'use_trend_filter': [True, False],
}

def optimize_tf(csv_files, tf_name, min_signals=5):
    """Optimize parameters for a specific timeframe across all assets"""
    
    keys = list(FULL_GRID.keys())
    values = [FULL_GRID[k] for k in keys]
    
    best_combo_score = -1
    best_combo_params = None
    best_combo_stats = None
    
    total_combos = 1
    for v in values:
        total_combos *= len(v)
    
    print(f"Testing {total_combos} parameter combinations for {tf_name}...")
    
    tested = 0
    for combo in product(*values):
        params = dict(zip(keys, combo))
        
        total_wins = 0
        total_losses = 0
        total_signals = 0
        
        for csv_path in csv_files:
            try:
                df = load_data(csv_path)
                bt = ElliottICTBacktester(df, params)
                result = bt.run_backtest()
                
                total_wins += result.wins
                total_losses += result.losses
                total_signals += result.total
            except:
                pass
        
        closed = total_wins + total_losses
        if closed >= min_signals:
            wr = (total_wins / closed * 100) if closed > 0 else 0
            # Score: prioritize WR but need reasonable signal count
            score = wr * (1 + min(total_signals, 100) / 200)
            
            if score > best_combo_score:
                best_combo_score = score
                best_combo_params = params.copy()
                best_combo_stats = {'wins': total_wins, 'losses': total_losses, 'total': total_signals, 'wr': wr}
        
        tested += 1
        if tested % 200 == 0:
            print(f"  Progress: {tested}/{total_combos}", end='\r')
    
    return best_combo_params, best_combo_stats, best_combo_score

def get_tf_from_filename(filename):
    name = os.path.basename(filename).upper()
    if '1D' in name:
        return '1D'
    elif '240' in name or '4H' in name:
        return '4H'
    elif '60' in name or '1H' in name:
        return '1H'
    elif '30' in name or '30M' in name:
        return '30m'
    elif '15' in name or '15M' in name:
        return '15m'
    elif '5' in name or '5M' in name:
        return '5m'
    return '1D'

def main():
    data_dir = r'C:\Users\danie\projects\elliott-wave-indicator\data'
    csv_files = glob.glob(os.path.join(data_dir, '*.csv'))
    
    # Group files by timeframe
    tf_files = {}
    for f in csv_files:
        tf = get_tf_from_filename(f)
        if tf not in tf_files:
            tf_files[tf] = []
        tf_files[tf].append(f)
    
    print("=" * 80)
    print("DEEP OPTIMIZATION - Finding best params per timeframe")
    print("=" * 80)
    print()
    
    results = {}
    
    for tf in ['1D', '4H', '1H', '30m', '15m', '5m']:
        if tf not in tf_files:
            continue
        
        files = tf_files[tf]
        print(f"\n{'='*40}")
        print(f"Optimizing {tf} ({len(files)} files)")
        print(f"{'='*40}")
        
        params, stats, score = optimize_tf(files, tf, min_signals=3)
        
        if params:
            results[tf] = {'params': params, 'stats': stats}
            print(f"\nBEST for {tf}:")
            print(f"  WR: {stats['wr']:.1f}% ({stats['wins']}W / {stats['losses']}L)")
            print(f"  Params: {params}")
        else:
            print(f"  No valid results found")
    
    # Print final summary
    print("\n" + "=" * 80)
    print("FINAL OPTIMIZED PARAMETERS FOR PINE SCRIPT v21")
    print("=" * 80)
    
    print("\n// PASTE THIS INTO YOUR PINE SCRIPT:")
    print()
    
    for tf in ['1D', '4H', '1H', '30m', '15m', '5m']:
        if tf not in results:
            continue
        p = results[tf]['params']
        s = results[tf]['stats']
        
        tf_var = tf.replace('m', '').replace('H', 'h')
        print(f"// {tf}: WR {s['wr']:.1f}% ({s['wins']}W/{s['losses']}L)")
        print(f"// zz_depth={p['zz_depth']}, zz_dev={p['zz_dev']}, gap={p['signal_gap']}, fib={p['fib_entry_level']}, rr={p['rr_ratio']}, trend={p['use_trend_filter']}")
        print()
    
    # Calculate overall stats
    total_wins = sum(r['stats']['wins'] for r in results.values())
    total_losses = sum(r['stats']['losses'] for r in results.values())
    overall_wr = (total_wins / (total_wins + total_losses) * 100) if (total_wins + total_losses) > 0 else 0
    
    print("=" * 80)
    print(f"OVERALL WIN RATE (with optimized params): {overall_wr:.1f}%")
    print(f"Total: {total_wins}W / {total_losses}L")
    print("=" * 80)

if __name__ == '__main__':
    main()
