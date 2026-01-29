"""
Test ALL Daily assets with RR=2.0
"""
import os
import sys
sys.path.append(os.path.dirname(__file__))

from backtester import ElliottICTBacktester, load_data
import glob

DATA_DIR = r'C:\Users\danie\projects\elliott-wave-indicator\data'

# Best params from previous search
PARAMS = {
    'zz_depth': 4,
    'zz_dev': 0.05,
    'signal_gap': 5,
    'fib_entry_level': 0.786,
    'rr_ratio': 2.0,
    'use_trend_filter': True,
    'use_rsi_filter': True,
    'use_volume_filter': True,
    'ema_period': 200,
    'rsi_threshold': 50,
    'wave_retrace_min': 0.5,
    'wave_retrace_max': 0.786,
}

def get_asset_name(filepath):
    """Extract asset name from filepath"""
    fname = os.path.basename(filepath)
    if fname.startswith('BATS_'):
        return fname.split(',')[0].replace('BATS_', '')
    elif fname.startswith('BINANCE_'):
        return fname.split(',')[0].replace('BINANCE_', '')
    elif fname.startswith('COINBASE_'):
        return fname.split(',')[0].replace('COINBASE_', '')
    elif fname.startswith('FOREXCOM_'):
        return fname.split(',')[0].replace('FOREXCOM_', '')
    elif fname.startswith('MNQ'):
        return 'MNQ'
    elif fname.startswith('NQ'):
        return 'NQ'
    return fname.split('_')[0]

print("="*70)
print("TESTING ALL DAILY ASSETS WITH RR=2.0")
print("="*70)
print(f"Params: zz={PARAMS['zz_depth']}, fib={PARAMS['fib_entry_level']}, rr={PARAMS['rr_ratio']}")
print()

# Find all Daily files
files = glob.glob(os.path.join(DATA_DIR, '*1D*.csv'))
files += glob.glob(os.path.join(DATA_DIR, '*_1D_*.csv'))
files = list(set(files))

results = []
ok_count = 0

for f in sorted(files):
    asset = get_asset_name(f)
    
    try:
        df = load_data(f)
        bt = ElliottICTBacktester(df, PARAMS)
        result = bt.run_backtest()
        
        trades = result.wins + result.losses
        wr = result.win_rate if trades >= 2 else 0
        status = "OK" if wr >= 85 else "FAIL" if trades >= 2 else "FEW"
        
        if wr >= 85:
            ok_count += 1
        
        results.append({
            'asset': asset,
            'wins': result.wins,
            'losses': result.losses,
            'wr': wr,
            'status': status
        })
        
        print(f"  {asset:12s}: {result.wins:2d}W/{result.losses:2d}L = {wr:5.1f}% [{status}]")
        
    except Exception as e:
        print(f"  {asset:12s}: ERROR - {e}")
        results.append({'asset': asset, 'error': str(e)})

# Summary
valid = [r for r in results if 'error' not in r and r['status'] != 'FEW']
total_valid = len(valid)
coverage = ok_count / total_valid * 100 if total_valid > 0 else 0

print()
print("="*70)
print(f"SUMMARY")
print("="*70)
print(f"Total assets: {len(results)}")
print(f"Valid (2+ trades): {total_valid}")
print(f"Passing (85%+): {ok_count}")
print(f"Coverage: {coverage:.0f}%")
print()

target = "[TARGET MET!]" if coverage >= 90 else f"[NEED {90-coverage:.0f}% MORE]"
print(f"Status: {target}")

# List failures
failures = [r for r in results if 'error' not in r and r['status'] == 'FAIL']
if failures:
    print(f"\nFailing assets ({len(failures)}):")
    for r in failures:
        print(f"  {r['asset']}: {r['wr']:.1f}%")
