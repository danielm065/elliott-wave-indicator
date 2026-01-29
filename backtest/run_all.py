"""
Run backtest on all timeframes with optimized parameters
"""
import sys
sys.path.insert(0, r'C:\Users\danie\projects\elliott-wave-indicator\backtest')

from backtester import ElliottICTBacktester, load_data
import os

DATA_DIR = r'C:\Users\danie\projects\elliott-wave-indicator\data'

# Parameters per timeframe (v20 - 0.79 Fib Entry)
TF_PARAMS = {
    '1D': {
        'sl_pct': 6.0,
        'tp_fib': 1.0,
        'zz_depth': 5,
        'zz_dev': 1.0,
        'signal_gap': 3,
        'fib_entry_level': 0.79,
        'fib_tolerance': 0.02,
        'use_trend_filter': True,
    },
    '4H': {
        'sl_pct': 2.5,
        'tp_fib': 1.0,
        'zz_depth': 6,
        'zz_dev': 0.5,
        'signal_gap': 8,
        'fib_entry_level': 0.79,
        'fib_tolerance': 0.02,
        'use_trend_filter': True,
    },
    '1H': {
        'sl_pct': 1.5,
        'tp_fib': 1.0,
        'zz_depth': 5,
        'zz_dev': 0.3,
        'signal_gap': 10,
        'fib_entry_level': 0.79,
        'fib_tolerance': 0.02,
        'use_trend_filter': False,
    },
    '30m': {
        'sl_pct': 1.2,
        'tp_fib': 0.786,
        'zz_depth': 4,
        'zz_dev': 0.2,
        'signal_gap': 15,
        'fib_entry_level': 0.79,
        'fib_tolerance': 0.03,
        'use_trend_filter': False,
    },
    '15m': {
        'sl_pct': 1.0,
        'tp_fib': 0.786,
        'zz_depth': 4,
        'zz_dev': 0.15,
        'signal_gap': 20,
        'fib_entry_level': 0.79,
        'fib_tolerance': 0.03,
        'use_trend_filter': False,
    },
    '5m': {
        'sl_pct': 0.8,
        'tp_fib': 0.618,
        'zz_depth': 3,
        'zz_dev': 0.1,
        'signal_gap': 30,
        'fib_entry_level': 0.79,
        'fib_tolerance': 0.04,
        'use_trend_filter': False,
    },
}

def run_all():
    results = {}
    
    files = {
        '1D': 'MNQ_1D.csv',
        '4H': 'MNQ_4H.csv',
        '1H': 'MNQ_1H.csv',
        '30m': 'MNQ_30m.csv',
        '15m': 'MNQ_15m.csv',
        '5m': 'MNQ_5m.csv',
    }
    
    for tf, filename in files.items():
        path = os.path.join(DATA_DIR, filename)
        if not os.path.exists(path):
            print(f"[WARN] {tf}: File not found - {filename}")
            continue
        
        df = load_data(path)
        params = TF_PARAMS.get(tf, {})
        
        bt = ElliottICTBacktester(df, params)
        result = bt.run_backtest()
        
        results[tf] = {
            'total': result.total,
            'wins': result.wins,
            'losses': result.losses,
            'open': result.open_trades,
            'win_rate': result.win_rate,
            'bars': len(df),
        }
        
        print(f"\n{'='*50}")
        print(f"[{tf}] TIMEFRAME ({len(df)} bars)")
        print(f"{'='*50}")
        print(f"Parameters: SL={params.get('sl_pct')}%, TP={params.get('tp_fib')}, ZZ={params.get('zz_depth')}, Gap={params.get('signal_gap')}")
        print(f"Signals: {result.total}")
        print(f"Wins: {result.wins} | Losses: {result.losses} | Open: {result.open_trades}")
        print(f"WIN RATE: {result.win_rate:.1f}%")
        
        if result.signals:
            print(f"\nLast signal: {df.index[result.signals[-1].bar]}")
    
    # Summary
    print(f"\n{'='*50}")
    print("SUMMARY")
    print(f"{'='*50}")
    for tf, r in results.items():
        print(f"{tf}: {r['win_rate']:.1f}% ({r['wins']}/{r['wins']+r['losses']}) - {r['total']} signals")

if __name__ == '__main__':
    run_all()
