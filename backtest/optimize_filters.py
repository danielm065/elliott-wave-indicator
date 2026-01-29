"""Optimize filters with different zz values"""
import os
import sys
sys.path.append(os.path.dirname(__file__))
from backtester import load_data
import glob
import numpy as np

DATA_DIR = r'C:\Users\danie\projects\elliott-wave-indicator\data'

def get_asset_name(filepath):
    fname = os.path.basename(filepath)
    for prefix in ['BATS_', 'BINANCE_', 'COINBASE_', 'FOREXCOM_']:
        if fname.startswith(prefix):
            return fname.split(',')[0].replace(prefix, '')
    if 'MNQ' in fname: return 'MNQ'
    if 'NQ' in fname: return 'NQ'
    return fname.split('_')[0]

files = glob.glob(os.path.join(DATA_DIR, '*1D*.csv'))
data = {}
for f in list(set(files)):
    asset = get_asset_name(f)
    try:
        data[asset] = load_data(f)
    except:
        pass

def calculate_rsi(df, period=14):
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_zigzag(df, depth=5):
    highs = df['high'].values
    lows = df['low'].values
    pivots = []
    last_pivot_type = None
    
    for i in range(depth, len(df) - depth):
        is_high = all(highs[i] >= highs[i-j] and highs[i] >= highs[i+j] for j in range(1, depth+1))
        is_low = all(lows[i] <= lows[i-j] and lows[i] <= lows[i+j] for j in range(1, depth+1))
        
        if is_high and last_pivot_type != 'high':
            pivots.append({'idx': i, 'type': 'high', 'val': highs[i]})
            last_pivot_type = 'high'
        elif is_low and last_pivot_type != 'low':
            pivots.append({'idx': i, 'type': 'low', 'val': lows[i]})
            last_pivot_type = 'low'
    
    return pivots

def backtest_filtered(df, params):
    zz_depth = params.get('zigzag_depth', 5)
    fib_level = params.get('fib_entry_level', 0.786)
    rr_ratio = params.get('rr_ratio', 1.5)
    min_wave_pct = params.get('min_wave_pct', 0)
    rsi_max = params.get('rsi_max', 100)
    
    rsi = calculate_rsi(df)
    pivots = calculate_zigzag(df, zz_depth)
    
    signals = []
    
    for i in range(2, len(pivots)):
        p0, p1, p2 = pivots[i-2], pivots[i-1], pivots[i]
        
        if p0['type'] == 'low' and p1['type'] == 'high' and p2['type'] == 'low':
            wave1_low = p0['val']
            wave1_high = p1['val']
            wave1_pct = (wave1_high - wave1_low) / wave1_low * 100
            
            if wave1_pct < min_wave_pct:
                continue
            
            wave2_low = p2['val']
            fib_price = wave1_high - (wave1_high - wave1_low) * fib_level
            tolerance = (wave1_high - wave1_low) * 0.05
            
            if abs(wave2_low - fib_price) <= tolerance:
                bar = p2['idx']
                
                if rsi.iloc[bar] > rsi_max:
                    continue
                
                entry = df['close'].iloc[bar]
                sl = wave1_low * 0.99
                risk = entry - sl
                tp = entry + risk * rr_ratio
                
                signals.append({'bar': bar, 'entry': entry, 'sl': sl, 'tp': tp})
    
    wins, losses = 0, 0
    for sig in signals:
        for bar in range(sig['bar'] + 1, len(df)):
            if df['low'].iloc[bar] <= sig['sl']:
                losses += 1
                break
            if df['high'].iloc[bar] >= sig['tp']:
                wins += 1
                break
    
    return wins, losses

print("="*60)
print("OPTIMIZING FILTERS (fib=0.786, RR=1.5)")
print("="*60)

best_cov = 0
best_params = None
best_results = None

for zz in [2, 3, 4, 5, 6]:
    for min_wave in [0, 3, 5, 8, 10]:
        for rsi_max in [50, 55, 60, 65, 70, 100]:
            params = {
                'zigzag_depth': zz,
                'fib_entry_level': 0.786,
                'rr_ratio': 1.5,
                'min_wave_pct': min_wave,
                'rsi_max': rsi_max
            }
            
            ok, valid = 0, 0
            results = {}
            
            for asset, df in data.items():
                try:
                    w, l = backtest_filtered(df, params)
                    if w + l >= 2:
                        valid += 1
                        wr = w / (w + l) * 100
                        results[asset] = wr
                        if wr >= 85:
                            ok += 1
                except:
                    pass
            
            if valid >= 5:
                cov = ok / valid * 100
                if cov > best_cov:
                    best_cov = cov
                    best_params = params.copy()
                    best_results = results.copy()
                    ok_list = [a for a, wr in results.items() if wr >= 85]
                    print(f"NEW: zz={zz}, wave={min_wave}%, rsi<{rsi_max} -> {cov:.0f}% ({ok}/{valid})")
                    print(f"  OK: {ok_list}")

print()
print("="*60)
if best_params:
    print(f"BEST: {best_cov:.0f}%")
    print(f"Params: zz={best_params['zigzag_depth']}, wave>{best_params['min_wave_pct']}%, rsi<{best_params['rsi_max']}")
    print()
    print("All results:")
    for a in sorted(best_results.keys()):
        s = "OK" if best_results[a] >= 85 else "FAIL"
        print(f"  {a:12s}: {best_results[a]:.0f}% [{s}]")
else:
    print("No valid combination found")
