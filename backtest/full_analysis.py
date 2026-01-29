"""
Full Analysis - Test ALL assets on ALL timeframes
"""
import os
import sys
sys.path.append(os.path.dirname(__file__))

from backtester import ElliottICTBacktester, load_data
import glob
import json

DATA_DIR = r'C:\Users\danie\projects\elliott-wave-indicator\data'

BASELINE_PARAMS = {
    'zz_depth': 5,
    'zz_dev': 0.5,
    'signal_gap': 10,
    'fib_entry_level': 0.79,
    'rr_ratio': 2.0,
    'use_trend_filter': True,
    'use_rsi_filter': True,
    'use_volume_filter': True,
    'ema_period': 200,
    'rsi_threshold': 50,
    'wave_retrace_min': 0.5,
    'wave_retrace_max': 0.786,
}

TF_MAP = {
    '1D': 'Daily',
    '240': '4H',
    '60': '1H', 
    '30': '30m',
    '15': '15m',
    '5': '5m',
    '1': '1m',
}

def parse_filename(filename):
    name = os.path.basename(filename).replace('.csv', '')
    
    if name.startswith('MNQ_') or name.startswith('NQ_'):
        parts = name.split('_')
        asset = parts[0]
        tf = parts[1].replace('m', '').replace('H', '').upper()
        if tf == '1D':
            tf = '1D'
        elif tf == '4':
            tf = '240'
        elif tf == '1':
            tf = '60'
        return asset, tf
    
    if 'BATS_' in name:
        parts = name.split(', ')
        asset = parts[0].replace('BATS_', '')
        tf = parts[1].split('_')[0]
        return asset, tf
    
    return 'UNKNOWN', 'UNKNOWN'

def run_backtest_on_file(filepath, params):
    try:
        df = load_data(filepath)
        bt = ElliottICTBacktester(df, params)
        result = bt.run_backtest()
        return {
            'wins': result.wins,
            'losses': result.losses,
            'total': result.total,
            'win_rate': result.win_rate,
            'open': result.open_trades
        }
    except Exception as e:
        return {'error': str(e)}

def main():
    files = glob.glob(os.path.join(DATA_DIR, '*.csv'))
    
    print("="*80)
    print("FULL ANALYSIS - ALL ASSETS, ALL TIMEFRAMES")
    print("="*80)
    print(f"Found {len(files)} data files")
    print()
    
    results = {}
    
    for f in sorted(files):
        asset, tf = parse_filename(f)
        tf_name = TF_MAP.get(tf, tf)
        
        if asset not in results:
            results[asset] = {}
        
        print(f"Testing {asset} {tf_name}...", end=" ")
        sys.stdout.flush()
        res = run_backtest_on_file(f, BASELINE_PARAMS)
        
        if 'error' in res:
            print(f"ERROR: {res['error']}")
            results[asset][tf_name] = {'error': res['error']}
        else:
            wr = res['win_rate']
            status = "[OK]" if wr >= 60 else "[--]"
            print(f"{res['wins']}W/{res['losses']}L = {wr:.1f}% {status}")
            results[asset][tf_name] = res
    
    print()
    print("="*80)
    print("SUMMARY BY ASSET")
    print("="*80)
    
    for asset in sorted(results.keys()):
        print(f"\n{asset}:")
        total_w, total_l = 0, 0
        for tf in ['Daily', '4H', '1H', '30m', '15m', '5m', '1m']:
            if tf in results[asset]:
                r = results[asset][tf]
                if 'error' not in r:
                    wr = r['win_rate']
                    status = "[OK]" if wr >= 60 else "[--]"
                    print(f"  {tf:6s}: {r['wins']:2d}W/{r['losses']:2d}L = {wr:5.1f}% {status}")
                    total_w += r['wins']
                    total_l += r['losses']
        if total_w + total_l > 0:
            overall = total_w / (total_w + total_l) * 100
            print(f"  {'TOTAL':6s}: {total_w:2d}W/{total_l:2d}L = {overall:5.1f}%")
    
    print()
    print("="*80)
    print("SUMMARY BY TIMEFRAME")
    print("="*80)
    
    tf_totals = {}
    for tf in ['Daily', '4H', '1H', '30m', '15m', '5m', '1m']:
        w, l = 0, 0
        for asset in results:
            if tf in results[asset] and 'error' not in results[asset][tf]:
                w += results[asset][tf]['wins']
                l += results[asset][tf]['losses']
        if w + l > 0:
            wr = w / (w + l) * 100
            status = "[OK]" if wr >= 60 else "[--]"
            print(f"{tf:6s}: {w:2d}W/{l:2d}L = {wr:5.1f}% {status}")
            tf_totals[tf] = {'wins': w, 'losses': l, 'win_rate': wr}
    
    print()
    total_w = sum(tf_totals[tf]['wins'] for tf in tf_totals)
    total_l = sum(tf_totals[tf]['losses'] for tf in tf_totals)
    if total_w + total_l > 0:
        overall_wr = total_w / (total_w + total_l) * 100
        print(f"{'OVERALL':6s}: {total_w:2d}W/{total_l:2d}L = {overall_wr:5.1f}%")
    
    output_path = os.path.join(os.path.dirname(__file__), 'full_analysis_results.json')
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to: {output_path}")

if __name__ == '__main__':
    main()
