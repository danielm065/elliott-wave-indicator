"""
Parameter Optimizer - Find best settings for each timeframe
"""
import os
import sys
sys.path.append(os.path.dirname(__file__))

from backtester import ElliottICTBacktester, load_data
from itertools import product
import glob

# Parameter ranges to test
PARAM_GRID = {
    'zz_depth': [3, 4, 5, 6, 8],
    'zz_dev': [0.1, 0.2, 0.3, 0.5, 0.8],
    'signal_gap': [3, 5, 10, 15, 20],
    'fib_entry_level': [0.618, 0.70, 0.79, 0.786],
    'rr_ratio': [1.5, 2.0, 2.5, 3.0],
    'use_trend_filter': [True, False],
    'use_rsi_filter': [True, False],
    'rsi_threshold': [40, 50, 60],
}

# Smaller grid for quick testing
QUICK_GRID = {
    'zz_depth': [4, 5, 6],
    'zz_dev': [0.2, 0.5],
    'signal_gap': [5, 10, 15],
    'fib_entry_level': [0.70, 0.79],
    'rr_ratio': [2.0, 2.5],
    'use_trend_filter': [True, False],
}

def optimize_file(csv_path, param_grid, min_signals=5):
    """Find best parameters for a single data file"""
    df = load_data(csv_path)
    
    keys = list(param_grid.keys())
    values = [param_grid[k] for k in keys]
    
    best_result = None
    best_params = None
    best_score = -1
    total_combos = 1
    for v in values:
        total_combos *= len(v)
    
    tested = 0
    for combo in product(*values):
        params = dict(zip(keys, combo))
        
        try:
            bt = ElliottICTBacktester(df, params)
            result = bt.run_backtest()
            
            closed = result.wins + result.losses
            
            # Score: Win Rate * signal count bonus (want both high WR and enough signals)
            if closed >= min_signals:
                # Prioritize win rate, but give bonus for more signals
                score = result.win_rate * (1 + min(closed, 50) / 100)
                
                if score > best_score:
                    best_score = score
                    best_result = result
                    best_params = params.copy()
        except:
            pass
        
        tested += 1
        if tested % 100 == 0:
            print(f"  Tested {tested}/{total_combos}...", end='\r')
    
    return best_params, best_result, best_score

def get_tf_from_filename(filename):
    """Extract timeframe from filename"""
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

def get_asset_from_filename(filename):
    """Extract asset name from filename"""
    name = os.path.basename(filename)
    if 'PLTR' in name:
        return 'PLTR'
    elif 'GOOG' in name:
        return 'GOOG'
    elif 'MNQ' in name:
        return 'MNQ'
    elif 'NQ' in name:
        return 'NQ'
    return name.split(',')[0].split('_')[-1]

def main():
    data_dir = r'C:\Users\danie\projects\elliott-wave-indicator\data'
    csv_files = glob.glob(os.path.join(data_dir, '*.csv'))
    
    print("=" * 90)
    print("PARAMETER OPTIMIZER - Finding best settings")
    print("=" * 90)
    print()
    
    # Collect results by timeframe
    tf_results = {}
    all_results = []
    
    for csv_path in sorted(csv_files):
        asset = get_asset_from_filename(csv_path)
        tf = get_tf_from_filename(csv_path)
        
        print(f"Optimizing {asset} {tf}...")
        
        best_params, best_result, best_score = optimize_file(csv_path, QUICK_GRID, min_signals=3)
        
        if best_result:
            wr = best_result.win_rate
            closed = best_result.wins + best_result.losses
            
            all_results.append({
                'asset': asset,
                'tf': tf,
                'params': best_params,
                'wins': best_result.wins,
                'losses': best_result.losses,
                'win_rate': wr
            })
            
            # Track by TF
            if tf not in tf_results:
                tf_results[tf] = []
            tf_results[tf].append({
                'asset': asset,
                'params': best_params,
                'wr': wr,
                'signals': closed
            })
            
            mark = "[OK]" if wr >= 70 else "[--]" if wr >= 50 else "[XX]"
            print(f"  {mark} Best WR: {wr:.1f}% ({best_result.wins}W/{best_result.losses}L)")
            print(f"      Params: zz={best_params.get('zz_depth')}, dev={best_params.get('zz_dev')}, gap={best_params.get('signal_gap')}, fib={best_params.get('fib_entry_level')}, rr={best_params.get('rr_ratio')}, trend={best_params.get('use_trend_filter')}")
        else:
            print(f"  [XX] No valid results")
        print()
    
    # Summary
    print("=" * 90)
    print("OPTIMIZED RESULTS BY TIMEFRAME")
    print("=" * 90)
    
    for tf in ['1D', '4H', '1H', '30m', '15m', '5m']:
        if tf not in tf_results:
            continue
        
        results = tf_results[tf]
        total_wins = sum(r['wr'] * r['signals'] / 100 for r in results)
        total_signals = sum(r['signals'] for r in results)
        avg_wr = (total_wins / total_signals * 100) if total_signals > 0 else 0
        
        print(f"\n{tf}:")
        print(f"  Average WR: {avg_wr:.1f}%")
        
        # Find most common params
        from collections import Counter
        param_counts = {}
        for key in ['zz_depth', 'zz_dev', 'signal_gap', 'fib_entry_level', 'rr_ratio', 'use_trend_filter']:
            vals = [r['params'].get(key) for r in results if r['params']]
            if vals:
                most_common = Counter(vals).most_common(1)[0]
                param_counts[key] = most_common[0]
        
        print(f"  Recommended: {param_counts}")
    
    # Grand total comparison
    print("\n" + "=" * 90)
    print("BEFORE vs AFTER OPTIMIZATION")
    print("=" * 90)
    
    total_wins = sum(r['wins'] for r in all_results)
    total_losses = sum(r['losses'] for r in all_results)
    new_wr = (total_wins / (total_wins + total_losses) * 100) if (total_wins + total_losses) > 0 else 0
    
    print(f"Original WR: 68.6% (baseline)")
    print(f"Optimized WR: {new_wr:.1f}%")
    print(f"Improvement: {new_wr - 68.6:+.1f}%")
    
    # Export best params
    print("\n" + "=" * 90)
    print("RECOMMENDED PARAMETERS FOR PINE SCRIPT")
    print("=" * 90)
    
    for tf in ['1D', '4H', '1H', '30m', '15m', '5m']:
        if tf not in tf_results:
            continue
        
        # Get params from best performing asset in this TF
        best = max(tf_results[tf], key=lambda x: x['wr'])
        p = best['params']
        
        print(f"\n// {tf}")
        print(f"// zz_depth={p.get('zz_depth')}, zz_dev={p.get('zz_dev')}, gap={p.get('signal_gap')}, fib={p.get('fib_entry_level')}, rr={p.get('rr_ratio')}, trend={p.get('use_trend_filter')}")

if __name__ == '__main__':
    main()
