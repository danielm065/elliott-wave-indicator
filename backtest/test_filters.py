"""Test different filters with fib=0.786, RR=1.5"""
import os
import sys
sys.path.append(os.path.dirname(__file__))
from backtester import load_data
import glob
import numpy as np
import pandas as pd

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
    """Calculate RSI"""
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_ema(df, period=50):
    """Calculate EMA"""
    return df['close'].ewm(span=period, adjust=False).mean()

def calculate_zigzag(df, depth=5):
    """Calculate zigzag points"""
    highs = df['high'].values
    lows = df['low'].values
    pivots = []
    
    last_pivot_type = None
    last_pivot_idx = 0
    last_pivot_val = 0
    
    for i in range(depth, len(df) - depth):
        # Check for swing high
        is_high = all(highs[i] >= highs[i-j] and highs[i] >= highs[i+j] for j in range(1, depth+1))
        # Check for swing low
        is_low = all(lows[i] <= lows[i-j] and lows[i] <= lows[i+j] for j in range(1, depth+1))
        
        if is_high and last_pivot_type != 'high':
            pivots.append({'idx': i, 'type': 'high', 'val': highs[i]})
            last_pivot_type = 'high'
        elif is_low and last_pivot_type != 'low':
            pivots.append({'idx': i, 'type': 'low', 'val': lows[i]})
            last_pivot_type = 'low'
    
    return pivots

def backtest_with_filters(df, params):
    """Backtest with configurable filters"""
    zz_depth = params.get('zigzag_depth', 5)
    fib_level = params.get('fib_entry_level', 0.786)
    rr_ratio = params.get('rr_ratio', 1.5)
    
    # Filters
    use_rsi = params.get('use_rsi', False)
    rsi_max = params.get('rsi_max', 70)
    rsi_min = params.get('rsi_min', 30)
    
    use_ema = params.get('use_ema', False)
    ema_period = params.get('ema_period', 50)
    
    use_bullish_candle = params.get('use_bullish_candle', False)
    
    use_volume = params.get('use_volume', False)
    volume_mult = params.get('volume_mult', 1.0)
    
    use_wave_strength = params.get('use_wave_strength', False)
    min_wave_pct = params.get('min_wave_pct', 5.0)
    
    # Calculate indicators
    rsi = calculate_rsi(df) if use_rsi else None
    ema = calculate_ema(df, ema_period) if use_ema else None
    vol_ma = df['volume'].rolling(20).mean() if use_volume and 'volume' in df.columns else None
    
    # Get zigzag
    pivots = calculate_zigzag(df, zz_depth)
    
    signals = []
    
    for i in range(2, len(pivots)):
        p0, p1, p2 = pivots[i-2], pivots[i-1], pivots[i]
        
        # Wave 1 up: low -> high
        if p0['type'] == 'low' and p1['type'] == 'high':
            wave1_low = p0['val']
            wave1_high = p1['val']
            wave1_pct = (wave1_high - wave1_low) / wave1_low * 100
            
            # Wave 2 down: high -> low
            if p2['type'] == 'low':
                wave2_low = p2['val']
                
                # Check fib retracement
                fib_price = wave1_high - (wave1_high - wave1_low) * fib_level
                tolerance = (wave1_high - wave1_low) * 0.05
                
                if abs(wave2_low - fib_price) <= tolerance:
                    bar = p2['idx']
                    
                    # Apply filters
                    if use_rsi and rsi is not None:
                        if rsi.iloc[bar] > rsi_max or rsi.iloc[bar] < rsi_min:
                            continue
                    
                    if use_ema and ema is not None:
                        if df['close'].iloc[bar] < ema.iloc[bar]:  # Price below EMA = no buy
                            continue
                    
                    if use_bullish_candle:
                        if df['close'].iloc[bar] <= df['open'].iloc[bar]:  # Not bullish
                            continue
                    
                    if use_volume and vol_ma is not None:
                        if df['volume'].iloc[bar] < vol_ma.iloc[bar] * volume_mult:
                            continue
                    
                    if use_wave_strength:
                        if wave1_pct < min_wave_pct:
                            continue
                    
                    # Entry
                    entry = df['close'].iloc[bar]
                    sl = wave1_low * 0.99
                    risk = entry - sl
                    tp = entry + risk * rr_ratio
                    
                    signals.append({
                        'bar': bar,
                        'entry': entry,
                        'sl': sl,
                        'tp': tp
                    })
    
    # Process signals
    wins = 0
    losses = 0
    
    for sig in signals:
        result = 0
        for bar in range(sig['bar'] + 1, len(df)):
            if df['low'].iloc[bar] <= sig['sl']:
                result = -1
                break
            if df['high'].iloc[bar] >= sig['tp']:
                result = 1
                break
        
        if result == 1:
            wins += 1
        elif result == -1:
            losses += 1
    
    return {'wins': wins, 'losses': losses, 'total': len(signals)}


print("="*60)
print("TESTING FILTERS (fib=0.786, RR=1.5)")
print("="*60)

# Base params
base = {'zigzag_depth': 5, 'fib_entry_level': 0.786, 'rr_ratio': 1.5}

# Test different filter combinations
filters = [
    {'name': 'No filters', 'params': {}},
    {'name': 'RSI 30-70', 'params': {'use_rsi': True, 'rsi_min': 30, 'rsi_max': 70}},
    {'name': 'RSI 20-60', 'params': {'use_rsi': True, 'rsi_min': 20, 'rsi_max': 60}},
    {'name': 'RSI 25-55', 'params': {'use_rsi': True, 'rsi_min': 25, 'rsi_max': 55}},
    {'name': 'Bullish candle', 'params': {'use_bullish_candle': True}},
    {'name': 'EMA 50', 'params': {'use_ema': True, 'ema_period': 50}},
    {'name': 'EMA 20', 'params': {'use_ema': True, 'ema_period': 20}},
    {'name': 'Wave 5%', 'params': {'use_wave_strength': True, 'min_wave_pct': 5}},
    {'name': 'Wave 10%', 'params': {'use_wave_strength': True, 'min_wave_pct': 10}},
    {'name': 'RSI + Bullish', 'params': {'use_rsi': True, 'rsi_min': 25, 'rsi_max': 60, 'use_bullish_candle': True}},
    {'name': 'RSI + EMA', 'params': {'use_rsi': True, 'rsi_min': 25, 'rsi_max': 60, 'use_ema': True}},
    {'name': 'RSI + Wave', 'params': {'use_rsi': True, 'rsi_min': 25, 'rsi_max': 60, 'use_wave_strength': True, 'min_wave_pct': 5}},
    {'name': 'All filters', 'params': {'use_rsi': True, 'rsi_min': 25, 'rsi_max': 60, 'use_bullish_candle': True, 'use_wave_strength': True, 'min_wave_pct': 5}},
]

best_cov = 0
best_filter = None

for f in filters:
    params = {**base, **f['params']}
    
    ok, valid = 0, 0
    ok_list = []
    
    for asset, df in data.items():
        try:
            r = backtest_with_filters(df, params)
            if r['wins'] + r['losses'] >= 2:
                valid += 1
                wr = r['wins'] / (r['wins'] + r['losses']) * 100
                if wr >= 85:
                    ok += 1
                    ok_list.append(asset)
        except:
            pass
    
    cov = ok/valid*100 if valid > 0 else 0
    print(f"{f['name']:20s}: {ok}/{valid} = {cov:.0f}%")
    if ok_list:
        print(f"  OK: {ok_list}")
    
    if cov > best_cov:
        best_cov = cov
        best_filter = f['name']

print()
print(f"Best: {best_filter} with {best_cov:.0f}%")
