"""
Diagnose why no signals on lower timeframes
"""
import sys
sys.path.insert(0, r'C:\Users\danie\projects\elliott-wave-indicator\backtest')

from backtester import ElliottICTBacktester, load_data
import pandas as pd

DATA_DIR = r'C:\Users\danie\projects\elliott-wave-indicator\data'

def diagnose(filename, tf_name, params):
    path = f"{DATA_DIR}/{filename}"
    df = load_data(path)
    
    print(f"\n{'='*60}")
    print(f"DIAGNOSE: {tf_name} ({len(df)} bars)")
    print(f"Date range: {df.index[0]} to {df.index[-1]}")
    print(f"Params: {params}")
    print(f"{'='*60}")
    
    bt = ElliottICTBacktester(df, params)
    bt.calculate_zigzag()
    
    print(f"\nZigzag points detected: {len(bt.zigzag_points)}")
    
    if bt.zigzag_points:
        print("\nLast 10 zigzag points:")
        for p in bt.zigzag_points[-10:]:
            bar, price, direction = p
            dir_str = "HIGH" if direction == 1 else "LOW"
            date = df.index[bar] if bar < len(df) else "N/A"
            print(f"  Bar {bar} ({date}): {price:.2f} [{dir_str}]")
    
    # Check for bullish patterns
    bullish_patterns = 0
    fib_touches = 0
    
    for bar in range(params.get('zz_depth', 8) + 1, len(df) - 1):
        at_fib, fib_price, swing_high, swing_low = bt.check_fib_entry(bar)
        
        if swing_high > swing_low:
            bullish_patterns += 1
            
            if at_fib:
                fib_touches += 1
                close = df['close'].iloc[bar]
                print(f"\n>>> Fib touch at bar {bar} ({df.index[bar]})")
                print(f"    Fib price: {fib_price:.2f}, Close: {close:.2f}")
                print(f"    Swing: {swing_low:.2f} -> {swing_high:.2f}")
    
    print(f"\nBullish patterns found: {bullish_patterns}")
    print(f"Fib touches: {fib_touches}")
    
    # Check if there are any signals without the bullish candle/trend requirements
    signals_without_filters = 0
    for bar in range(params.get('zz_depth', 8) + 1, len(df) - 1):
        at_fib, fib_price, swing_high, swing_low = bt.check_fib_entry(bar)
        if at_fib:
            signals_without_filters += 1
    
    print(f"Potential signals (no filters): {signals_without_filters}")


if __name__ == '__main__':
    # Diagnose lower timeframes with reduced zz_dev
    diagnose("MNQ_5m.csv", "5m", {'zz_depth': 3, 'zz_dev': 0.1, 'fib_entry_level': 0.79, 'fib_tolerance': 0.04})
    diagnose("MNQ_15m.csv", "15m", {'zz_depth': 4, 'zz_dev': 0.15, 'fib_entry_level': 0.79, 'fib_tolerance': 0.03})
    diagnose("MNQ_30m.csv", "30m", {'zz_depth': 4, 'zz_dev': 0.2, 'fib_entry_level': 0.79, 'fib_tolerance': 0.03})
