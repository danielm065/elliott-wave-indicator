"""
Test specific params on all assets for a timeframe
"""
import os
import sys
sys.path.append(os.path.dirname(__file__))

from backtester import ElliottICTBacktester, load_data
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

ASSETS = ['GOOG', 'PLTR', 'MU', 'OSCR', 'RKLB', 'MNQ']

def find_files_for_tf(tf):
    """Find all data files for a timeframe"""
    patterns = TF_MAP.get(tf, [tf])
    files = {}
    
    for f in glob.glob(os.path.join(DATA_DIR, '*.csv')):
        fname = os.path.basename(f).upper()
        tf_match = any(p.upper() in fname for p in patterns)
        if tf_match:
            for asset in ASSETS:
                if asset in fname:
                    files[asset] = f
                    break
    return files

def test_params_on_tf(tf, params):
    """Test params on all assets for a TF"""
    files = find_files_for_tf(tf)
    results = []
    
    for asset in ASSETS:
        if asset not in files:
            results.append({'asset': asset, 'error': 'No file'})
            continue
        
        try:
            df = load_data(files[asset])
            bt = ElliottICTBacktester(df, params)
            result = bt.run_backtest()
            
            wr = result.win_rate
            status = "OK" if wr >= 85 else "FAIL"
            
            results.append({
                'asset': asset,
                'wins': result.wins,
                'losses': result.losses,
                'win_rate': wr,
                'status': status
            })
        except Exception as e:
            results.append({'asset': asset, 'error': str(e)})
    
    return results

def print_results(tf, results, params):
    """Print results table"""
    print(f"\n{'='*60}")
    print(f"{tf} - Testing params:")
    print(f"  rr={params['rr_ratio']}, fib={params['fib_entry_level']}, zz={params['zz_depth']}")
    print(f"{'='*60}")
    
    ok_count = 0
    total = 0
    
    for r in results:
        if 'error' in r:
            print(f"  {r['asset']}: ERROR - {r['error']}")
        else:
            total += 1
            if r['status'] == 'OK':
                ok_count += 1
            print(f"  {r['asset']}: {r['wins']}W/{r['losses']}L = {r['win_rate']:.1f}% [{r['status']}]")
    
    coverage = ok_count / total * 100 if total > 0 else 0
    target_met = "[TARGET MET]" if coverage >= 90 else "[NEED MORE]"
    print(f"\nCoverage: {ok_count}/{total} = {coverage:.0f}% {target_met}")
    
    return coverage

if __name__ == '__main__':
    tf = sys.argv[1] if len(sys.argv) > 1 else '1D'
    
    # Test different RR ratios
    base_params = {
        'zz_depth': 5,
        'zz_dev': 0.5,
        'signal_gap': 10,
        'fib_entry_level': 0.79,
        'use_trend_filter': True,
        'use_rsi_filter': True,
        'use_volume_filter': True,
        'ema_period': 200,
        'rsi_threshold': 50,
        'wave_retrace_min': 0.5,
        'wave_retrace_max': 0.786,
    }
    
    best_coverage = 0
    best_params = None
    
    for rr in [0.5, 0.8, 1.0, 1.5, 2.0]:
        params = base_params.copy()
        params['rr_ratio'] = rr
        results = test_params_on_tf(tf, params)
        coverage = print_results(tf, results, params)
        
        if coverage > best_coverage:
            best_coverage = coverage
            best_params = params.copy()
    
    print(f"\n{'='*60}")
    print(f"BEST: RR={best_params['rr_ratio']} with {best_coverage:.0f}% coverage")
    print(f"{'='*60}")
