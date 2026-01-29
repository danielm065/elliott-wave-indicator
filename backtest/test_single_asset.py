"""
Test single asset on single timeframe
Usage: python test_single_asset.py GOOG 1D
"""
import os
import sys
sys.path.append(os.path.dirname(__file__))

from backtester import ElliottICTBacktester, load_data
import glob

DATA_DIR = r'C:\Users\danie\projects\elliott-wave-indicator\data'

# Current params (will be updated as we learn)
PARAMS = {
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
    '1D': ['1D', '1D_'],
    '4H': ['240', '4H'],
    '1H': ['60', '1H'],
    '30m': [', 30_', '30m'],
    '15m': [', 15_', '15m'],
    '5m': [', 5_', '5m'],
}

def find_file(asset, tf):
    """Find data file for asset/tf combination"""
    patterns = TF_MAP.get(tf, [tf])
    
    for f in glob.glob(os.path.join(DATA_DIR, '*.csv')):
        fname = os.path.basename(f).upper()
        asset_match = asset.upper() in fname
        tf_match = any(p.upper() in fname for p in patterns)
        if asset_match and tf_match:
            return f
    return None

def test_asset(asset, tf, params=None):
    """Test single asset and return detailed results"""
    if params is None:
        params = PARAMS.copy()
    
    filepath = find_file(asset, tf)
    if not filepath:
        return {'error': f'No data file found for {asset} {tf}'}
    
    try:
        df = load_data(filepath)
        bt = ElliottICTBacktester(df, params)
        result = bt.run_backtest()
        
        return {
            'asset': asset,
            'tf': tf,
            'file': os.path.basename(filepath),
            'bars': len(df),
            'total': result.total,
            'wins': result.wins,
            'losses': result.losses,
            'open': result.open_trades,
            'win_rate': result.win_rate,
            'signals': result.signals,
            'params': params,
        }
    except Exception as e:
        return {'error': str(e)}

def print_results(res):
    """Pretty print results"""
    if 'error' in res:
        print(f"ERROR: {res['error']}")
        return
    
    print(f"\n{'='*60}")
    print(f"{res['asset']} - {res['tf']}")
    print(f"{'='*60}")
    print(f"File: {res['file']}")
    print(f"Bars: {res['bars']}")
    print(f"\nRESULTS:")
    print(f"  Total Signals: {res['total']}")
    print(f"  Wins: {res['wins']}")
    print(f"  Losses: {res['losses']}")
    print(f"  Open: {res['open']}")
    print(f"  Win Rate: {res['win_rate']:.1f}%")
    
    status = "[OK]" if res['win_rate'] >= 85 else "[FAIL]"
    print(f"\nSTATUS: {status}")
    
    if res['win_rate'] < 85:
        print(f"  Need: 85%")
        print(f"  Gap: {85 - res['win_rate']:.1f}%")

def main():
    if len(sys.argv) < 3:
        print("Usage: python test_single_asset.py ASSET TF")
        print("Example: python test_single_asset.py GOOG 1D")
        print("\nAssets: GOOG, PLTR, MU, OSCR, RKLB, MNQ, NQ")
        print("Timeframes: 1D, 4H, 1H, 30m, 15m, 5m")
        return
    
    asset = sys.argv[1].upper()
    tf = sys.argv[2]
    
    res = test_asset(asset, tf)
    print_results(res)

if __name__ == '__main__':
    main()
