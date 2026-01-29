"""
Elliott Wave + ICT Parameter Optimizer
Downloads historical data and tests different parameter combinations
"""

import yfinance as yf
import pandas as pd
import numpy as np
from itertools import product
import warnings
warnings.filterwarnings('ignore')

# Download data
print("Downloading NQ data...")
ticker = yf.Ticker("NQ=F")  # Nasdaq futures
df = ticker.history(period="2y", interval="4h")
print(f"Downloaded {len(df)} bars")

# Convert to simple arrays for speed
opens = df['Open'].values
highs = df['High'].values
lows = df['Low'].values
closes = df['Close'].values

def find_zigzag(highs, lows, depth=10, deviation=2.0):
    """Find zigzag pivots"""
    pivots = []  # (index, price, type: 1=high, -1=low)
    direction = 0
    last_price = 0
    
    for i in range(depth, len(highs) - depth):
        # Check for pivot high
        is_ph = True
        for j in range(1, depth + 1):
            if highs[i] <= highs[i-j] or highs[i] <= highs[i+j]:
                is_ph = False
                break
        
        # Check for pivot low
        is_pl = True
        for j in range(1, depth + 1):
            if lows[i] >= lows[i-j] or lows[i] >= lows[i+j]:
                is_pl = False
                break
        
        if is_ph:
            if direction == -1 and last_price > 0:
                if abs(highs[i] - last_price) / last_price * 100 >= deviation:
                    pivots.append((i, highs[i], 1))
                    direction = 1
                    last_price = highs[i]
            elif direction == 1 and highs[i] > last_price:
                pivots[-1] = (i, highs[i], 1)
                last_price = highs[i]
            elif len(pivots) == 0:
                pivots.append((i, highs[i], 1))
                direction = 1
                last_price = highs[i]
        
        if is_pl:
            if direction == 1 and last_price > 0:
                if abs(lows[i] - last_price) / last_price * 100 >= deviation:
                    pivots.append((i, lows[i], -1))
                    direction = -1
                    last_price = lows[i]
            elif direction == -1 and lows[i] < last_price:
                pivots[-1] = (i, lows[i], -1)
                last_price = lows[i]
            elif len(pivots) == 0:
                pivots.append((i, lows[i], -1))
                direction = -1
                last_price = lows[i]
    
    return pivots

def backtest(params):
    """Run backtest with given parameters"""
    min_strength = params['min_strength']
    sl_pct = params['sl_pct']
    tp_fib = params['tp_fib']
    zz_depth = params['zz_depth']
    wave_retrace_min = params['wave_retrace_min']
    wave_retrace_max = params['wave_retrace_max']
    signal_gap = params['signal_gap']
    
    pivots = find_zigzag(highs, lows, zz_depth, 2.0)
    
    signals = []
    last_signal_idx = -signal_gap - 1
    
    for i in range(50, len(closes)):
        # Get recent pivots
        recent_pivots = [p for p in pivots if p[0] < i]
        if len(recent_pivots) < 3:
            continue
        
        p0 = recent_pivots[-1]  # Most recent
        p1 = recent_pivots[-2]
        p2 = recent_pivots[-3]
        
        # Calculate discount zone
        swing_high = max(p0[1], p1[1])
        swing_low = min(p0[1], p1[1])
        equilibrium = (swing_high + swing_low) / 2
        
        in_discount = closes[i] < equilibrium
        
        # Wave 2 setup: down-up-down pattern
        wave2_setup = False
        wave1_size = 0
        if p2[2] == -1 and p1[2] == 1 and p0[2] == -1:
            wave1_size = p1[1] - p2[1]
            if wave1_size > 0:
                retrace = (p1[1] - p0[1]) / wave1_size
                wave2_setup = wave_retrace_min <= retrace <= wave_retrace_max
        
        # Simple scoring
        score = 0
        if in_discount:
            score += 2
        if wave2_setup:
            score += 3
        if closes[i] > opens[i]:  # Bullish candle
            score += 1
        
        # OTE zone check
        ote_price = swing_high - (swing_high - swing_low) * 0.618
        if swing_low <= closes[i] <= ote_price:
            score += 3
        
        # Check for sweep (low below recent lows)
        recent_low = min(lows[i-10:i])
        if lows[i] < recent_low and closes[i] > recent_low:
            score += 2
        
        # Generate signal
        if score >= min_strength and in_discount and closes[i] > opens[i]:
            if i - last_signal_idx > signal_gap:
                entry = closes[i]
                tp = entry + (wave1_size * tp_fib if wave1_size > 0 else entry * 0.02)
                sl = entry * (1 - sl_pct / 100)
                signals.append({
                    'idx': i,
                    'entry': entry,
                    'tp': tp,
                    'sl': sl,
                    'result': None
                })
                last_signal_idx = i
    
    # Evaluate signals
    wins = 0
    losses = 0
    
    for sig in signals:
        idx = sig['idx']
        for j in range(idx + 1, min(idx + 100, len(closes))):
            if highs[j] >= sig['tp']:
                sig['result'] = 'win'
                wins += 1
                break
            elif lows[j] <= sig['sl']:
                sig['result'] = 'loss'
                losses += 1
                break
    
    total = wins + losses
    win_rate = (wins / total * 100) if total > 0 else 0
    
    return {
        'params': params,
        'signals': len(signals),
        'wins': wins,
        'losses': losses,
        'win_rate': win_rate
    }

# Parameter grid
param_grid = {
    'min_strength': [6, 7, 8, 9, 10],
    'sl_pct': [1.5, 2.0, 2.5, 3.0],
    'tp_fib': [0.618, 1.0, 1.272, 1.618],
    'zz_depth': [8, 10, 12],
    'wave_retrace_min': [0.5],
    'wave_retrace_max': [0.786],
    'signal_gap': [10, 15, 20]
}

# Generate all combinations
keys = param_grid.keys()
values = param_grid.values()
combinations = [dict(zip(keys, v)) for v in product(*values)]

print(f"\nTesting {len(combinations)} parameter combinations...\n")

results = []
best_result = None
best_win_rate = 0

for i, params in enumerate(combinations):
    result = backtest(params)
    results.append(result)
    
    # Track best
    if result['win_rate'] > best_win_rate and result['signals'] >= 10:
        best_win_rate = result['win_rate']
        best_result = result
    
    # Progress
    if (i + 1) % 50 == 0:
        print(f"Progress: {i+1}/{len(combinations)}")

# Sort by win rate
results.sort(key=lambda x: x['win_rate'], reverse=True)

# Print top 10
print("\n" + "="*60)
print("TOP 10 PARAMETER COMBINATIONS")
print("="*60)

for i, r in enumerate(results[:10]):
    if r['signals'] >= 5:  # Only show if enough signals
        print(f"\n#{i+1} - Win Rate: {r['win_rate']:.1f}% ({r['wins']}/{r['wins']+r['losses']})")
        print(f"   Signals: {r['signals']}")
        print(f"   Params: min_str={r['params']['min_strength']}, SL={r['params']['sl_pct']}%, TP={r['params']['tp_fib']}")
        print(f"           zz_depth={r['params']['zz_depth']}, gap={r['params']['signal_gap']}")

# Best overall
print("\n" + "="*60)
print("BEST RESULT (min 10 signals)")
print("="*60)
if best_result:
    print(f"Win Rate: {best_result['win_rate']:.1f}%")
    print(f"Signals: {best_result['signals']} ({best_result['wins']} wins, {best_result['losses']} losses)")
    print(f"\nOptimal Parameters:")
    for k, v in best_result['params'].items():
        print(f"  {k}: {v}")
