"""
Run backtest on ALL assets and timeframes
"""
import os
import sys
sys.path.append(os.path.dirname(__file__))

from backtester import ElliottICTBacktester, load_data
import glob

# Timeframe-specific parameters (OPTIMIZED v21.2 - from deep optimization)
TF_PARAMS = {
    '1D': {'zz_depth': 4, 'zz_dev': 0.1, 'signal_gap': 3, 'fib_entry_level': 0.79, 'use_trend_filter': False, 'rr_ratio': 1.5},
    '240': {'zz_depth': 4, 'zz_dev': 0.1, 'signal_gap': 3, 'fib_entry_level': 0.70, 'use_trend_filter': True, 'rr_ratio': 1.5},  # 4H
    '60': {'zz_depth': 4, 'zz_dev': 0.1, 'signal_gap': 3, 'fib_entry_level': 0.79, 'use_trend_filter': False, 'rr_ratio': 1.5},  # 1H
    '30': {'zz_depth': 4, 'zz_dev': 0.1, 'signal_gap': 3, 'fib_entry_level': 0.79, 'use_trend_filter': False, 'rr_ratio': 1.5},
    '15': {'zz_depth': 4, 'zz_dev': 0.1, 'signal_gap': 3, 'fib_entry_level': 0.79, 'use_trend_filter': False, 'rr_ratio': 1.5},
    '5': {'zz_depth': 4, 'zz_dev': 0.1, 'signal_gap': 3, 'fib_entry_level': 0.79, 'use_trend_filter': False, 'rr_ratio': 1.5},
    '1': {'zz_depth': 3, 'zz_dev': 0.1, 'signal_gap': 5, 'fib_entry_level': 0.79, 'use_trend_filter': False, 'rr_ratio': 1.5},  # 1m
}

def get_tf_from_filename(filename):
    """Extract timeframe from filename"""
    name = os.path.basename(filename).upper()
    if '1D' in name:
        return '1D'
    elif '240' in name or '4H' in name:
        return '240'
    elif '60' in name or '1H' in name:
        return '60'
    elif '30' in name or '30M' in name:
        return '30'
    elif '15' in name or '15M' in name:
        return '15'
    elif ', 5_' in name.lower() or '5M' in name:
        return '5'
    elif ', 1_' in name.lower() or '1M' in name:
        return '1'
    return '1D'  # Default

def get_asset_from_filename(filename):
    """Extract asset name from filename"""
    name = os.path.basename(filename)
    if 'PLTR' in name:
        return 'PLTR'
    elif 'GOOG' in name:
        return 'GOOG'
    elif 'RKLB' in name:
        return 'RKLB'
    elif 'OSCR' in name:
        return 'OSCR'
    elif 'MU,' in name or 'MU_' in name:
        return 'MU'
    elif 'MNQ' in name:
        return 'MNQ'
    elif 'NQ' in name:
        return 'NQ'
    return name.split(',')[0].split('_')[-1]

def main():
    data_dir = r'C:\Users\danie\projects\elliott-wave-indicator\data'
    csv_files = glob.glob(os.path.join(data_dir, '*.csv'))
    
    print("=" * 80)
    print("ELLIOTT + ICT BACKTEST - ALL ASSETS")
    print("=" * 80)
    print()
    
    results = []
    
    for csv_path in sorted(csv_files):
        asset = get_asset_from_filename(csv_path)
        tf = get_tf_from_filename(csv_path)
        params = TF_PARAMS.get(tf, TF_PARAMS['1D']).copy()
        
        try:
            df = load_data(csv_path)
            bt = ElliottICTBacktester(df, params)
            result = bt.run_backtest()
            
            closed = result.wins + result.losses
            
            results.append({
                'asset': asset,
                'tf': tf,
                'total': result.total,
                'wins': result.wins,
                'losses': result.losses,
                'open': result.open_trades,
                'win_rate': result.win_rate,
                'bars': len(df)
            })
            
            # Color coding
            wr = result.win_rate
            wr_mark = "[OK]" if wr >= 70 else "[--]" if wr >= 50 else "[XX]"
            
            print(f"{wr_mark} {asset:6} {tf:4} | Signals: {result.total:3} | W:{result.wins:2} L:{result.losses:2} O:{result.open_trades:2} | WR: {wr:5.1f}% | Bars: {len(df)}")
            
        except Exception as e:
            print(f"[ERR] {asset:6} {tf:4} | ERROR: {e}")
    
    print()
    print("=" * 80)
    print("SUMMARY BY ASSET")
    print("=" * 80)
    
    # Group by asset
    assets = set(r['asset'] for r in results)
    for asset in sorted(assets):
        asset_results = [r for r in results if r['asset'] == asset]
        total_wins = sum(r['wins'] for r in asset_results)
        total_losses = sum(r['losses'] for r in asset_results)
        total_signals = sum(r['total'] for r in asset_results)
        overall_wr = (total_wins / (total_wins + total_losses) * 100) if (total_wins + total_losses) > 0 else 0
        
        wr_mark = "[OK]" if overall_wr >= 70 else "[--]" if overall_wr >= 50 else "[XX]"
        print(f"{wr_mark} {asset:6} | Signals: {total_signals:3} | W:{total_wins:3} L:{total_losses:3} | Overall WR: {overall_wr:5.1f}%")
    
    print()
    print("=" * 80)
    print("SUMMARY BY TIMEFRAME")
    print("=" * 80)
    
    # Group by timeframe
    tfs = set(r['tf'] for r in results)
    for tf in ['1D', '240', '60', '30', '15', '5']:
        if tf not in tfs:
            continue
        tf_results = [r for r in results if r['tf'] == tf]
        total_wins = sum(r['wins'] for r in tf_results)
        total_losses = sum(r['losses'] for r in tf_results)
        total_signals = sum(r['total'] for r in tf_results)
        overall_wr = (total_wins / (total_wins + total_losses) * 100) if (total_wins + total_losses) > 0 else 0
        
        wr_mark = "[OK]" if overall_wr >= 70 else "[--]" if overall_wr >= 50 else "[XX]"
        print(f"{wr_mark} {tf:4} | Signals: {total_signals:3} | W:{total_wins:3} L:{total_losses:3} | Overall WR: {overall_wr:5.1f}%")
    
    # Grand total
    print()
    total_wins = sum(r['wins'] for r in results)
    total_losses = sum(r['losses'] for r in results)
    total_signals = sum(r['total'] for r in results)
    grand_wr = (total_wins / (total_wins + total_losses) * 100) if (total_wins + total_losses) > 0 else 0
    
    print("=" * 80)
    print(f"GRAND TOTAL | Signals: {total_signals} | W:{total_wins} L:{total_losses} | WR: {grand_wr:.1f}%")
    print("=" * 80)

if __name__ == '__main__':
    main()
