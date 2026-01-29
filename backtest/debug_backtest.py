"""
Debug backtest - detailed output for each signal
"""
import sys
sys.path.insert(0, r'C:\Users\danie\projects\elliott-wave-indicator\backtest')

from backtester import ElliottICTBacktester, load_data
import pandas as pd

def debug_backtest(data_path: str, tf_name: str, params: dict):
    """Run backtest with detailed debug output"""
    
    df = load_data(data_path)
    print(f"\n{'='*70}")
    print(f"DEBUG BACKTEST: {tf_name}")
    print(f"Data: {len(df)} bars from {df.index[0]} to {df.index[-1]}")
    print(f"Params: {params}")
    print(f"{'='*70}\n")
    
    bt = ElliottICTBacktester(df, params)
    result = bt.run_backtest()
    
    print(f"Total signals: {result.total}")
    print(f"Wins: {result.wins}, Losses: {result.losses}, Open: {result.open_trades}")
    print(f"Win Rate: {result.win_rate:.1f}%")
    print()
    
    # Detailed signal analysis
    print("DETAILED SIGNAL ANALYSIS:")
    print("-" * 70)
    
    for i, sig in enumerate(result.signals):
        date = df.index[sig.bar]
        entry_bar = df.iloc[sig.bar]
        
        print(f"\n[Signal {i+1}] {date}")
        print(f"  Entry: {sig.entry:.2f} (close of signal bar)")
        print(f"  TP: {sig.tp:.2f} ({((sig.tp/sig.entry)-1)*100:.2f}% above entry)")
        print(f"  SL: {sig.sl:.2f} ({((sig.entry/sig.sl)-1)*100:.2f}% below entry)")
        print(f"  Signal bar OHLC: O={entry_bar['open']:.2f} H={entry_bar['high']:.2f} L={entry_bar['low']:.2f} C={entry_bar['close']:.2f}")
        
        # Show what happened after
        if sig.result != 0:
            status = "WIN" if sig.result == 1 else "LOSS"
            print(f"  Result: {status}")
            
            # Find which bar hit TP/SL
            for bar_idx in range(sig.bar + 1, len(df)):
                bar_data = df.iloc[bar_idx]
                hit_sl = bar_data['low'] <= sig.sl
                hit_tp = bar_data['high'] >= sig.tp
                
                if hit_sl or hit_tp:
                    exit_date = df.index[bar_idx]
                    bars_held = bar_idx - sig.bar
                    print(f"  Exit bar: {exit_date} (held {bars_held} bars)")
                    print(f"  Exit bar OHLC: O={bar_data['open']:.2f} H={bar_data['high']:.2f} L={bar_data['low']:.2f} C={bar_data['close']:.2f}")
                    
                    if hit_sl:
                        print(f"  >>> SL HIT: Low {bar_data['low']:.2f} <= SL {sig.sl:.2f}")
                    if hit_tp:
                        print(f"  >>> TP HIT: High {bar_data['high']:.2f} >= TP {sig.tp:.2f}")
                    break
        else:
            print(f"  Result: OPEN (not yet resolved)")
    
    # Check for potential issues
    print("\n" + "=" * 70)
    print("SANITY CHECKS:")
    print("-" * 70)
    
    # Check 1: Are TP targets too easy?
    avg_tp_pct = sum((s.tp/s.entry - 1)*100 for s in result.signals) / len(result.signals) if result.signals else 0
    avg_sl_pct = sum((1 - s.sl/s.entry)*100 for s in result.signals) / len(result.signals) if result.signals else 0
    print(f"Average TP target: +{avg_tp_pct:.2f}%")
    print(f"Average SL risk: -{avg_sl_pct:.2f}%")
    print(f"Risk/Reward ratio: 1:{avg_tp_pct/avg_sl_pct:.2f}" if avg_sl_pct > 0 else "N/A")
    
    # Check 2: How quickly do trades close?
    bars_to_close = []
    for sig in result.signals:
        if sig.result != 0:
            for bar_idx in range(sig.bar + 1, len(df)):
                bar_data = df.iloc[bar_idx]
                if bar_data['low'] <= sig.sl or bar_data['high'] >= sig.tp:
                    bars_to_close.append(bar_idx - sig.bar)
                    break
    
    if bars_to_close:
        print(f"Average bars to close: {sum(bars_to_close)/len(bars_to_close):.1f}")
        print(f"Min bars to close: {min(bars_to_close)}")
        print(f"Max bars to close: {max(bars_to_close)}")
    
    return result


if __name__ == '__main__':
    DATA_DIR = r'C:\Users\danie\projects\elliott-wave-indicator\data'
    
    # Test all timeframes
    for tf, filename, params in [
        ("1D", "MNQ_1D.csv", {'sl_pct': 6.0, 'tp_fib': 1.0, 'zz_depth': 5, 'signal_gap': 3, 'fib_entry_level': 0.79}),
        ("4H", "MNQ_4H.csv", {'sl_pct': 2.5, 'tp_fib': 1.0, 'zz_depth': 8, 'signal_gap': 8, 'fib_entry_level': 0.79}),
        ("1H", "MNQ_1H.csv", {'sl_pct': 1.5, 'tp_fib': 1.0, 'zz_depth': 12, 'signal_gap': 15, 'fib_entry_level': 0.79}),
    ]:
        debug_backtest(f"{DATA_DIR}/{filename}", tf, params)
