"""
Test specific params on all assets
"""
import os
import sys
sys.path.append(os.path.dirname(__file__))

from backtester import ElliottICTBacktester, load_data
import glob

DATA_DIR = r'C:\Users\danie\projects\elliott-wave-indicator\data'

ASSETS = ['GOOG', 'PLTR', 'MU', 'OSCR', 'RKLB', 'MNQ']

TF_MAP = {
    '1D': ['1D'],
    '4H': ['240', '4H'],
    '1H': ['60', '1H'],
    '30m': [', 30_', '30m'],
    '15m': [', 15_', '15m'],
    '5m': [', 5_', '5m'],
}

def find_file(asset, tf):
    patterns = TF_MAP.get(tf, [tf])
    for f in glob.glob(os.path.join(DATA_DIR, '*.csv')):
        fname = os.path.basename(f).upper()
        if asset.upper() in fname and any(p.upper() in fname for p in patterns):
            return f
    return None

def test_all(tf, params):
    print(f"\n{'='*60}")
    print(f"{tf} - Params: zz={params['zz_depth']}, fib={params['fib_entry_level']}, rr={params['rr_ratio']}")
    print(f"{'='*60}")
    
    ok = 0
    total = 0
    
    for asset in ASSETS:
        f = find_file(asset, tf)
        if not f:
            print(f"  {asset}: No file")
            continue
        
        df = load_data(f)
        bt = ElliottICTBacktester(df, params)
        result = bt.run_backtest()
        
        total += 1
        wr = result.win_rate
        status = "OK" if wr >= 85 else "FAIL"
        if wr >= 85:
            ok += 1
        
        print(f"  {asset}: {result.wins}W/{result.losses}L = {wr:.1f}% [{status}]")
    
    coverage = ok / total * 100 if total > 0 else 0
    target = "[TARGET MET!]" if coverage >= 90 else f"[{coverage:.0f}% - need 90%]"
    print(f"\nCoverage: {ok}/{total} = {coverage:.0f}% {target}")
    return coverage

if __name__ == '__main__':
    tf = sys.argv[1] if len(sys.argv) > 1 else '1D'
    
    # Test the OSCR-optimal params
    params = {
        'zz_depth': 3,
        'zz_dev': 0.5,
        'signal_gap': 10,
        'fib_entry_level': 0.618,
        'rr_ratio': 0.5,
        'use_trend_filter': True,
        'use_rsi_filter': True,
        'use_volume_filter': True,
        'ema_period': 200,
        'rsi_threshold': 50,
        'wave_retrace_min': 0.5,
        'wave_retrace_max': 0.786,
    }
    
    test_all(tf, params)
