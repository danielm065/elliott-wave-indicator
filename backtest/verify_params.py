"""
Verify optimized parameters work correctly
"""
import os
import sys
sys.path.append(os.path.dirname(__file__))

from backtester import ElliottICTBacktester, load_data
import glob

def verify_tf(tf_name, pattern, expected_params):
    data_dir = r'C:\Users\danie\projects\elliott-wave-indicator\data'
    files = glob.glob(os.path.join(data_dir, pattern))
    
    if not files:
        print(f"No files for {tf_name}")
        return
    
    print(f"\n{tf_name} - Testing {len(files)} files with optimized params:")
    print(f"  Params: {expected_params}")
    
    total_w, total_l = 0, 0
    for f in files:
        try:
            df = load_data(f)
            bt = ElliottICTBacktester(df, expected_params)
            result = bt.run_backtest()
            total_w += result.wins
            total_l += result.losses
            print(f"  {os.path.basename(f)}: {result.wins}W/{result.losses}L ({result.win_rate:.1f}%)")
        except Exception as e:
            print(f"  {os.path.basename(f)}: ERROR - {e}")
    
    if total_w + total_l > 0:
        wr = total_w / (total_w + total_l) * 100
        print(f"  TOTAL: {total_w}W/{total_l}L = {wr:.1f}%")

if __name__ == '__main__':
    # 30m optimized
    verify_tf('30m', '*30*.csv', {
        'zz_depth': 4,
        'zz_dev': 0.01,
        'signal_gap': 8,
        'fib_entry_level': 0.618,
        'rr_ratio': 0.8,
        'use_trend_filter': True,
        'use_rsi_filter': True,
    })
    
    # 15m optimized
    verify_tf('15m', '*15*.csv', {
        'zz_depth': 5,
        'zz_dev': 0.01,
        'signal_gap': 8,
        'fib_entry_level': 0.786,
        'rr_ratio': 0.8,
        'use_trend_filter': True,
        'use_rsi_filter': True,
    })
    
    # 5m optimized  
    verify_tf('5m', '*5_*.csv', {
        'zz_depth': 4,
        'zz_dev': 0.01,
        'signal_gap': 10,
        'fib_entry_level': 0.75,
        'rr_ratio': 0.8,
        'use_trend_filter': True,
        'use_rsi_filter': True,
    })
    
    # Also test 5m with MNQ_5m.csv specifically
    verify_tf('5m-MNQ', 'MNQ_5m.csv', {
        'zz_depth': 4,
        'zz_dev': 0.01,
        'signal_gap': 10,
        'fib_entry_level': 0.75,
        'rr_ratio': 0.8,
        'use_trend_filter': True,
        'use_rsi_filter': True,
    })
