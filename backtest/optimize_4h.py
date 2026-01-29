"""
4H Optimization - Target 85%+ WR
"""
import os
import sys
sys.path.append(os.path.dirname(__file__))

from backtester import ElliottICTBacktester, load_data
from itertools import product
import glob

# Focused parameter grid for 4H
GRID_4H = {
    'zz_depth': [3, 4, 5, 6],
    'zz_dev': [0.05, 0.1, 0.15, 0.2],
    'signal_gap': [3, 5, 8],
    'fib_entry_level': [0.618, 0.70, 0.786, 0.79],
    'rr_ratio': [1.5, 2.0],
    'use_trend_filter': [True, False],
}

def get_4h_files():
    data_dir = r'C:\Users\danie\projects\elliott-wave-indicator\data'
    files = glob.glob(os.path.join(data_dir, '*240*.csv'))
    return files

def get_asset_from_filename(filename):
    name = os.path.basename(filename)
    for asset in ['PLTR', 'GOOG', 'RKLB', 'OSCR', 'MNQ', 'NQ', 'MU']:
        if asset in name:
            return asset
    return 'UNKNOWN'

def test_params_on_all(files, params):
    results = {}
    total_wins = 0
    total_losses = 0
    
    for f in files:
        asset = get_asset_from_filename(f)
        try:
            df = load_data(f)
            bt = ElliottICTBacktester(df, params)
            result = bt.run_backtest()
            
            results[asset] = {
                'wins': result.wins,
                'losses': result.losses,
                'total': result.total,
                'wr': result.win_rate
            }
            total_wins += result.wins
            total_losses += result.losses
        except Exception as e:
            results[asset] = {'error': str(e)}
    
    overall_wr = (total_wins / (total_wins + total_losses) * 100) if (total_wins + total_losses) > 0 else 0
    
    return results, overall_wr, total_wins, total_losses

def main():
    files = get_4h_files()
    print(f"Found {len(files)} 4H files:")
    for f in files:
        print(f"  - {get_asset_from_filename(f)}: {os.path.basename(f)}")
    print()
    
    # First, test current baseline
    print("=" * 80)
    print("CURRENT BASELINE (4H)")
    print("=" * 80)
    
    baseline_params = {
        'zz_depth': 4, 'zz_dev': 0.1, 'signal_gap': 3,
        'fib_entry_level': 0.70, 'rr_ratio': 1.5, 'use_trend_filter': True
    }
    
    results, overall_wr, wins, losses = test_params_on_all(files, baseline_params)
    print(f"\nBaseline WR: {overall_wr:.1f}% ({wins}W/{losses}L)")
    print("\nPer-asset breakdown:")
    for asset, stats in sorted(results.items()):
        if 'error' not in stats:
            mark = "[OK]" if stats['wr'] >= 85 else "[--]" if stats['wr'] >= 70 else "[XX]"
            print(f"  {mark} {asset}: {stats['wr']:.1f}% ({stats['wins']}W/{stats['losses']}L)")
    
    # Now run optimization
    print("\n" + "=" * 80)
    print("OPTIMIZING 4H - Target 85%+")
    print("=" * 80)
    
    keys = list(GRID_4H.keys())
    values = [GRID_4H[k] for k in keys]
    
    total_combos = 1
    for v in values:
        total_combos *= len(v)
    
    print(f"Testing {total_combos} combinations...\n")
    
    best_overall_wr = 0
    best_params = None
    best_results = None
    top_results = []
    
    tested = 0
    for combo in product(*values):
        params = dict(zip(keys, combo))
        
        results, overall_wr, wins, losses = test_params_on_all(files, params)
        
        closed = wins + losses
        if closed >= 5:
            if overall_wr > best_overall_wr:
                best_overall_wr = overall_wr
                best_params = params.copy()
                best_results = results.copy()
                
                top_results.append({
                    'params': params.copy(),
                    'wr': overall_wr,
                    'wins': wins,
                    'losses': losses,
                    'results': results.copy()
                })
                top_results = sorted(top_results, key=lambda x: x['wr'], reverse=True)[:5]
        
        tested += 1
        if tested % 100 == 0:
            print(f"Progress: {tested}/{total_combos} | Best WR: {best_overall_wr:.1f}%")
    
    print(f"\nProgress: {tested}/{total_combos} | Best WR: {best_overall_wr:.1f}%")
    
    # Print top 5 results
    print("\n" + "=" * 80)
    print("TOP 5 PARAMETER COMBINATIONS")
    print("=" * 80)
    
    for i, tr in enumerate(top_results):
        print(f"\n#{i+1}: WR {tr['wr']:.1f}% ({tr['wins']}W/{tr['losses']}L)")
        p = tr['params']
        print(f"    zz={p['zz_depth']}, dev={p['zz_dev']}, gap={p['signal_gap']}, fib={p['fib_entry_level']}, rr={p['rr_ratio']}, trend={p['use_trend_filter']}")
        print("    Per-asset:")
        for asset, stats in sorted(tr['results'].items()):
            if 'error' not in stats and stats['total'] > 0:
                mark = "[OK]" if stats['wr'] >= 85 else "[--]" if stats['wr'] >= 70 else "[XX]"
                print(f"      {mark} {asset}: {stats['wr']:.1f}%")
    
    # Final recommendation
    print("\n" + "=" * 80)
    print("RECOMMENDED 4H PARAMETERS")
    print("=" * 80)
    
    if best_params:
        print(f"\nBest Overall WR: {best_overall_wr:.1f}%")
        print(f"Parameters:")
        for k, v in best_params.items():
            print(f"  {k}: {v}")
        
        print("\nPer-asset results:")
        for asset, stats in sorted(best_results.items()):
            if 'error' not in stats:
                mark = "[OK]" if stats['wr'] >= 85 else "[--]" if stats['wr'] >= 70 else "[XX]"
                print(f"  {mark} {asset}: {stats['wr']:.1f}% ({stats['wins']}W/{stats['losses']}L)")

if __name__ == '__main__':
    main()
