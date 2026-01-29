"""
Elliott Wave Optimizer - Daily Timeframe
"""

import yfinance as yf
import pandas as pd
import numpy as np
from itertools import product
import warnings
warnings.filterwarnings('ignore')

print("Downloading NQ Daily data...")
ticker = yf.Ticker("NQ=F")
df = ticker.history(period="5y", interval="1d")
print(f"Downloaded {len(df)} bars")

opens = df['Open'].values
highs = df['High'].values
lows = df['Low'].values
closes = df['Close'].values

def find_zigzag(highs, lows, depth=10, deviation=2.0):
    pivots = []
    direction = 0
    last_price = 0
    
    for i in range(depth, len(highs) - depth):
        is_ph = True
        for j in range(1, depth + 1):
            if highs[i] <= highs[i-j] or highs[i] <= highs[i+j]:
                is_ph = False
                break
        
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
    min_strength = params['min_strength']
    sl_pct = params['sl_pct']
    tp_fib = params['tp_fib']
    zz_depth = params['zz_depth']
    wave_retrace_min = params['wave_retrace_min']
    wave_retrace_max = params['wave_retrace_max']
    signal_gap = params['signal_gap']
    
    pivots = find_zigzag(highs, lows, zz_depth, 3.0)  # Higher deviation for daily
    
    signals = []
    last_signal_idx = -signal_gap - 1
    
    for i in range(50, len(closes)):
        recent_pivots = [p for p in pivots if p[0] < i]
        if len(recent_pivots) < 3:
            continue
        
        p0 = recent_pivots[-1]
        p1 = recent_pivots[-2]
        p2 = recent_pivots[-3]
        
        swing_high = max(p0[1], p1[1])
        swing_low = min(p0[1], p1[1])
        equilibrium = (swing_high + swing_low) / 2
        
        in_discount = closes[i] < equilibrium
        
        wave2_setup = False
        wave1_size = 0
        if p2[2] == -1 and p1[2] == 1 and p0[2] == -1:
            wave1_size = p1[1] - p2[1]
            if wave1_size > 0:
                retrace = (p1[1] - p0[1]) / wave1_size
                wave2_setup = wave_retrace_min <= retrace <= wave_retrace_max
        
        score = 0
        if in_discount:
            score += 2
        if wave2_setup:
            score += 3
        if closes[i] > opens[i]:
            score += 1
        
        ote_price = swing_high - (swing_high - swing_low) * 0.618
        if swing_low <= closes[i] <= ote_price:
            score += 3
        
        recent_low = min(lows[max(0,i-10):i]) if i > 10 else lows[i]
        if lows[i] < recent_low and closes[i] > recent_low:
            score += 2
        
        if score >= min_strength and in_discount and closes[i] > opens[i]:
            if i - last_signal_idx > signal_gap:
                entry = closes[i]
                tp = entry + (wave1_size * tp_fib if wave1_size > 0 else entry * 0.03)
                sl = entry * (1 - sl_pct / 100)
                signals.append({
                    'idx': i,
                    'entry': entry,
                    'tp': tp,
                    'sl': sl,
                    'result': None
                })
                last_signal_idx = i
    
    wins = 0
    losses = 0
    
    for sig in signals:
        idx = sig['idx']
        for j in range(idx + 1, min(idx + 50, len(closes))):
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

# Parameter grid for Daily
param_grid = {
    'min_strength': [5, 6, 7, 8],
    'sl_pct': [3.0, 4.0, 5.0, 6.0],
    'tp_fib': [0.382, 0.5, 0.618, 1.0],
    'zz_depth': [5, 8, 10],
    'wave_retrace_min': [0.5],
    'wave_retrace_max': [0.786],
    'signal_gap': [3, 5, 7]
}

keys = param_grid.keys()
values = param_grid.values()
combinations = [dict(zip(keys, v)) for v in product(*values)]

print(f"\nTesting {len(combinations)} combinations for DAILY...\n")

results = []
best_result = None
best_win_rate = 0

for i, params in enumerate(combinations):
    result = backtest(params)
    results.append(result)
    
    if result['win_rate'] > best_win_rate and result['signals'] >= 5:
        best_win_rate = result['win_rate']
        best_result = result
    
    if (i + 1) % 50 == 0:
        print(f"Progress: {i+1}/{len(combinations)}")

results.sort(key=lambda x: x['win_rate'], reverse=True)

print("\n" + "="*60)
print("TOP 10 FOR DAILY TIMEFRAME")
print("="*60)

for i, r in enumerate(results[:10]):
    if r['signals'] >= 3:
        print(f"\n#{i+1} - Win Rate: {r['win_rate']:.1f}% ({r['wins']}/{r['wins']+r['losses']})")
        print(f"   Signals: {r['signals']}")
        print(f"   Params: min_str={r['params']['min_strength']}, SL={r['params']['sl_pct']}%, TP={r['params']['tp_fib']}")
        print(f"           zz_depth={r['params']['zz_depth']}, gap={r['params']['signal_gap']}")

print("\n" + "="*60)
print("BEST DAILY RESULT")
print("="*60)
if best_result:
    print(f"Win Rate: {best_result['win_rate']:.1f}%")
    print(f"Signals: {best_result['signals']} ({best_result['wins']} wins, {best_result['losses']} losses)")
    print(f"\nOptimal Daily Parameters:")
    for k, v in best_result['params'].items():
        print(f"  {k}: {v}")
