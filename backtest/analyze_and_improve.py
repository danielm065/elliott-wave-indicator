"""
Analyze problems and test improvements
"""
import os
import sys
sys.path.append(os.path.dirname(__file__))

from backtester import ElliottICTBacktester, load_data
from itertools import product
import glob

def get_asset(filename):
    name = os.path.basename(filename)
    for asset in ['PLTR', 'GOOG', 'RKLB', 'OSCR', 'MNQ', 'NQ', 'MU']:
        if asset in name:
            return asset
    return 'UNKNOWN'

def get_tf(filename):
    name = os.path.basename(filename).upper()
    if '1D' in name: return '1D'
    elif '240' in name: return '4H'
    elif ', 60' in name.lower() or '60_' in name.lower(): return '1H'
    elif ', 30' in name.lower() or '30_' in name.lower(): return '30m'
    elif ', 15' in name.lower() or '15_' in name.lower(): return '15m'
    elif ', 5_' in name.lower(): return '5m'
    return 'UNK'

def analyze_current_results():
    """Analyze what's working and what's not"""
    data_dir = r'C:\Users\danie\projects\elliott-wave-indicator\data'
    files = glob.glob(os.path.join(data_dir, '*.csv'))
    
    # Current best params per TF
    params_by_tf = {
        '1D': {'zz_depth': 4, 'zz_dev': 0.03, 'signal_gap': 8, 'fib_entry_level': 0.79, 'rr_ratio': 1.5, 'use_trend_filter': True},
        '4H': {'zz_depth': 3, 'zz_dev': 0.03, 'signal_gap': 5, 'fib_entry_level': 0.70, 'rr_ratio': 1.5, 'use_trend_filter': True},
        '1H': {'zz_depth': 3, 'zz_dev': 0.03, 'signal_gap': 5, 'fib_entry_level': 0.786, 'rr_ratio': 1.5, 'use_trend_filter': False},
        '30m': {'zz_depth': 5, 'zz_dev': 0.03, 'signal_gap': 5, 'fib_entry_level': 0.786, 'rr_ratio': 1.5, 'use_trend_filter': True},
    }
    
    print("=" * 70)
    print("CURRENT RESULTS BY ASSET AND TIMEFRAME")
    print("=" * 70)
    
    results_matrix = {}
    
    for f in files:
        asset = get_asset(f)
        tf = get_tf(f)
        
        if tf not in params_by_tf:
            continue
            
        params = params_by_tf[tf]
        
        try:
            df = load_data(f)
            bt = ElliottICTBacktester(df, params)
            result = bt.run_backtest()
            
            key = f"{asset}_{tf}"
            results_matrix[key] = {
                'asset': asset,
                'tf': tf,
                'wr': result.win_rate,
                'wins': result.wins,
                'losses': result.losses,
                'total': result.total
            }
        except:
            pass
    
    # Print matrix
    tfs = ['1D', '4H', '1H', '30m']
    assets = sorted(set(r['asset'] for r in results_matrix.values()))
    
    print("\n{:8}".format("Asset"), end="")
    for tf in tfs:
        print(f"{tf:>10}", end="")
    print()
    print("-" * 50)
    
    for asset in assets:
        print(f"{asset:8}", end="")
        for tf in tfs:
            key = f"{asset}_{tf}"
            if key in results_matrix:
                wr = results_matrix[key]['wr']
                mark = "*" if wr >= 85 else "" if wr >= 70 else "!"
                print(f"{wr:>8.1f}%{mark}", end="")
            else:
                print(f"{'--':>10}", end="")
        print()
    
    # Find problematic combinations
    print("\n" + "=" * 70)
    print("PROBLEMATIC COMBINATIONS (below 70%)")
    print("=" * 70)
    
    for key, data in sorted(results_matrix.items(), key=lambda x: x[1]['wr']):
        if data['wr'] < 70 and data['total'] >= 3:
            print(f"  {data['asset']} {data['tf']}: {data['wr']:.1f}% ({data['wins']}W/{data['losses']}L)")
    
    return results_matrix

def test_improvements(results_matrix):
    """Test potential improvements"""
    data_dir = r'C:\Users\danie\projects\elliott-wave-indicator\data'
    
    print("\n" + "=" * 70)
    print("TESTING IMPROVEMENTS")
    print("=" * 70)
    
    # Improvement ideas to test
    improvements = [
        {'name': 'Lower fib (0.618)', 'fib_entry_level': 0.618},
        {'name': 'Higher fib (0.70)', 'fib_entry_level': 0.70},
        {'name': 'Stricter dev (0.02)', 'zz_dev': 0.02},
        {'name': 'Looser dev (0.05)', 'zz_dev': 0.05},
        {'name': 'Larger gap (10)', 'signal_gap': 10},
        {'name': 'Smaller gap (3)', 'signal_gap': 3},
        {'name': 'R:R 1:1', 'rr_ratio': 1.0},
        {'name': 'R:R 1:2', 'rr_ratio': 2.0},
        {'name': 'Deeper ZZ (6)', 'zz_depth': 6},
        {'name': 'Shallower ZZ (2)', 'zz_depth': 2},
        {'name': 'Trend ON', 'use_trend_filter': True},
        {'name': 'Trend OFF', 'use_trend_filter': False},
    ]
    
    # Test on 4H (currently 76.9%)
    print("\n4H IMPROVEMENTS:")
    base_params = {'zz_depth': 3, 'zz_dev': 0.03, 'signal_gap': 5, 'fib_entry_level': 0.70, 'rr_ratio': 1.5, 'use_trend_filter': True}
    files_4h = glob.glob(os.path.join(data_dir, '*240*.csv'))
    
    for imp in improvements:
        test_params = base_params.copy()
        for k, v in imp.items():
            if k != 'name':
                test_params[k] = v
        
        total_w, total_l = 0, 0
        for f in files_4h:
            try:
                df = load_data(f)
                bt = ElliottICTBacktester(df, test_params)
                result = bt.run_backtest()
                total_w += result.wins
                total_l += result.losses
            except:
                pass
        
        if total_w + total_l >= 5:
            wr = total_w / (total_w + total_l) * 100
            mark = "[OK]" if wr >= 85 else "[--]" if wr > 76.9 else "[XX]"
            print(f"  {mark} {imp['name']:20} -> {wr:.1f}% ({total_w}W/{total_l}L)")
    
    # Test on 1H (currently 72.1%)
    print("\n1H IMPROVEMENTS:")
    base_params = {'zz_depth': 3, 'zz_dev': 0.03, 'signal_gap': 5, 'fib_entry_level': 0.786, 'rr_ratio': 1.5, 'use_trend_filter': False}
    files_1h = glob.glob(os.path.join(data_dir, '*60*.csv'))
    
    for imp in improvements:
        test_params = base_params.copy()
        for k, v in imp.items():
            if k != 'name':
                test_params[k] = v
        
        total_w, total_l = 0, 0
        for f in files_1h:
            try:
                df = load_data(f)
                bt = ElliottICTBacktester(df, test_params)
                result = bt.run_backtest()
                total_w += result.wins
                total_l += result.losses
            except:
                pass
        
        if total_w + total_l >= 5:
            wr = total_w / (total_w + total_l) * 100
            mark = "[OK]" if wr >= 85 else "[--]" if wr > 72.1 else "[XX]"
            print(f"  {mark} {imp['name']:20} -> {wr:.1f}% ({total_w}W/{total_l}L)")

def find_best_combo():
    """Find best parameter combination for weak TFs"""
    data_dir = r'C:\Users\danie\projects\elliott-wave-indicator\data'
    
    print("\n" + "=" * 70)
    print("SEARCHING FOR BEST COMBO ON WEAK TFs")
    print("=" * 70)
    
    # Focused grid
    grid = {
        'zz_depth': [2, 3, 4, 5],
        'zz_dev': [0.02, 0.03, 0.05],
        'signal_gap': [3, 5, 8, 10],
        'fib_entry_level': [0.618, 0.70, 0.786, 0.79],
        'rr_ratio': [1.0, 1.5, 2.0],
        'use_trend_filter': [True, False],
    }
    
    # 4H
    print("\n4H - Finding best...")
    files_4h = glob.glob(os.path.join(data_dir, '*240*.csv'))
    best_4h_wr, best_4h_params = 0, None
    
    for combo in product(*grid.values()):
        params = dict(zip(grid.keys(), combo))
        total_w, total_l = 0, 0
        for f in files_4h:
            try:
                df = load_data(f)
                bt = ElliottICTBacktester(df, params)
                result = bt.run_backtest()
                total_w += result.wins
                total_l += result.losses
            except:
                pass
        
        if total_w + total_l >= 5:
            wr = total_w / (total_w + total_l) * 100
            if wr > best_4h_wr:
                best_4h_wr = wr
                best_4h_params = params.copy()
    
    print(f"  Best 4H: {best_4h_wr:.1f}%")
    if best_4h_params:
        print(f"  Params: {best_4h_params}")
    
    # 1H
    print("\n1H - Finding best...")
    files_1h = glob.glob(os.path.join(data_dir, '*60*.csv'))
    best_1h_wr, best_1h_params = 0, None
    
    for combo in product(*grid.values()):
        params = dict(zip(grid.keys(), combo))
        total_w, total_l = 0, 0
        for f in files_1h:
            try:
                df = load_data(f)
                bt = ElliottICTBacktester(df, params)
                result = bt.run_backtest()
                total_w += result.wins
                total_l += result.losses
            except:
                pass
        
        if total_w + total_l >= 5:
            wr = total_w / (total_w + total_l) * 100
            if wr > best_1h_wr:
                best_1h_wr = wr
                best_1h_params = params.copy()
    
    print(f"  Best 1H: {best_1h_wr:.1f}%")
    if best_1h_params:
        print(f"  Params: {best_1h_params}")
    
    return best_4h_params, best_1h_params

def main():
    results = analyze_current_results()
    test_improvements(results)
    best_4h, best_1h = find_best_combo()
    
    print("\n" + "=" * 70)
    print("SUMMARY - RECOMMENDED NEXT STEPS")
    print("=" * 70)
    print("1. Use found best params for 4H and 1H")
    print("2. Consider excluding problematic assets (MU, RKLB)")
    print("3. Add more confirmation filters (RSI oversold, Volume spike)")
    print("4. Test higher R:R with stricter entry")

if __name__ == '__main__':
    main()
