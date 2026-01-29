"""
Realistic Backtest - Entry must be touched before TP/SL
"""

import yfinance as yf
import pandas as pd
import numpy as np
from itertools import product
import warnings
warnings.filterwarnings('ignore')

print("Downloading NQ 4H data...")
ticker = yf.Ticker("NQ=F")
df = ticker.history(period="2y", interval="4h")
print(f"Downloaded {len(df)} bars")

opens = df['Open'].values
highs = df['High'].values
lows = df['Low'].values
closes = df['Close'].values

def find_zigzag(highs, lows, depth=12, deviation=2.0):
    pivots = []
    direction = 0
    last_price = 0
    
    for i in range(depth, len(highs) - depth):
        is_ph = all(highs[i] > highs[i-j] and highs[i] > highs[i+j] for j in range(1, depth + 1))
        is_pl = all(lows[i] < lows[i-j] and lows[i] < lows[i+j] for j in range(1, depth + 1))
        
        if is_ph and (direction == -1 or not pivots):
            if not pivots or abs(highs[i] - last_price) / last_price * 100 >= deviation:
                pivots.append((i, highs[i], 1))
                direction, last_price = 1, highs[i]
        
        if is_pl and (direction == 1 or not pivots):
            if not pivots or abs(lows[i] - last_price) / last_price * 100 >= deviation:
                pivots.append((i, lows[i], -1))
                direction, last_price = -1, lows[i]
    
    return pivots

pivots = find_zigzag(highs, lows, 12, 2.0)

def backtest(params):
    min_strength = params['min_strength']
    sl_pct = params['sl_pct']
    tp_fib = params['tp_fib']
    signal_gap = params['signal_gap']
    
    signals = []
    last_signal_idx = -signal_gap - 1
    
    for i in range(60, len(closes)):
        recent_pivots = [p for p in pivots if p[0] < i]
        if len(recent_pivots) < 3:
            continue
        
        p0, p1, p2 = recent_pivots[-1], recent_pivots[-2], recent_pivots[-3]
        
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
                wave2_setup = 0.5 <= retrace <= 0.786
        
        score = 0
        if in_discount: score += 2
        if wave2_setup: score += 3
        if closes[i] > opens[i]: score += 1
        
        ote_price = swing_high - (swing_high - swing_low) * 0.618
        if swing_low <= closes[i] <= ote_price: score += 3
        
        recent_low = min(lows[max(0,i-10):i]) if i > 10 else lows[i]
        if lows[i] < recent_low and closes[i] > recent_low: score += 2
        
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
                    'filled': False,
                    'result': None
                })
                last_signal_idx = i
    
    wins, losses, not_filled = 0, 0, 0
    
    for sig in signals:
        idx = sig['idx']
        entry = sig['entry']
        tp = sig['tp']
        sl = sig['sl']
        filled = False
        
        # Check bars after signal
        for j in range(idx + 1, min(idx + 100, len(closes))):
            # First, check if entry was touched
            if not filled:
                if lows[j] <= entry:
                    filled = True
                    # Now entry is filled, check from this bar onwards
            
            if filled:
                # Check SL first (conservative)
                if lows[j] <= sl:
                    losses += 1
                    sig['result'] = 'loss'
                    break
                elif highs[j] >= tp:
                    wins += 1
                    sig['result'] = 'win'
                    break
        
        if sig['result'] is None:
            if filled:
                not_filled += 1  # Still open
            else:
                not_filled += 1  # Never filled
    
    total = wins + losses
    return {
        'params': params,
        'signals': len(signals),
        'wins': wins,
        'losses': losses,
        'not_filled': not_filled,
        'win_rate': (wins / total * 100) if total > 0 else 0
    }

# Parameter grid
param_grid = {
    'min_strength': [5, 6, 7, 8],
    'sl_pct': [2.0, 2.5, 3.0, 3.5, 4.0],
    'tp_fib': [0.382, 0.5, 0.618, 0.786, 1.0],
    'signal_gap': [8, 10, 12, 15]
}

combinations = [dict(zip(param_grid.keys(), v)) for v in product(*param_grid.values())]
print(f"\nTesting {len(combinations)} combinations with REALISTIC backtest...\n")

results = []
best = None

for i, params in enumerate(combinations):
    result = backtest(params)
    results.append(result)
    if result['win_rate'] > (best['win_rate'] if best else 0) and result['wins'] + result['losses'] >= 10:
        best = result
    if (i + 1) % 100 == 0:
        print(f"Progress: {i+1}/{len(combinations)}")

results.sort(key=lambda x: (x['win_rate'], x['wins']), reverse=True)

print("\n" + "="*70)
print("TOP 10 - REALISTIC BACKTEST (Entry must be touched)")
print("="*70)

for i, r in enumerate(results[:10]):
    if r['wins'] + r['losses'] >= 5:
        p = r['params']
        print(f"\n#{i+1} Win Rate: {r['win_rate']:.1f}% ({r['wins']}W / {r['losses']}L)")
        print(f"   Signals: {r['signals']}, Not filled/open: {r['not_filled']}")
        print(f"   min_str={p['min_strength']}, SL={p['sl_pct']}%, TP={p['tp_fib']}, gap={p['signal_gap']}")

print("\n" + "="*70)
print("BEST REALISTIC CONFIGURATION")
print("="*70)
if best:
    print(f"\nWin Rate: {best['win_rate']:.1f}%")
    print(f"Trades: {best['wins']}W / {best['losses']}L (total: {best['wins']+best['losses']})")
    print(f"Signals: {best['signals']}, Not executed: {best['not_filled']}")
    print(f"\nOptimal Parameters:")
    for k, v in best['params'].items():
        print(f"  {k}: {v}")
