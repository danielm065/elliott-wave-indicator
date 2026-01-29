"""
Advanced Elliott Wave Optimizer
Tests logic variations, not just parameters
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
volumes = df['Volume'].values

# Calculate indicators
def calc_ema(data, period):
    ema = np.zeros(len(data))
    ema[0] = data[0]
    mult = 2 / (period + 1)
    for i in range(1, len(data)):
        ema[i] = (data[i] * mult) + (ema[i-1] * (1 - mult))
    return ema

def calc_rsi(data, period=14):
    rsi = np.zeros(len(data))
    for i in range(period, len(data)):
        gains = 0
        losses = 0
        for j in range(i - period, i):
            change = data[j+1] - data[j]
            if change > 0:
                gains += change
            else:
                losses -= change
        avg_gain = gains / period
        avg_loss = losses / period
        if avg_loss == 0:
            rsi[i] = 100
        else:
            rs = avg_gain / avg_loss
            rsi[i] = 100 - (100 / (1 + rs))
    return rsi

def calc_atr(highs, lows, closes, period=14):
    atr = np.zeros(len(closes))
    for i in range(1, len(closes)):
        tr = max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1]))
        if i < period:
            atr[i] = tr
        else:
            atr[i] = (atr[i-1] * (period - 1) + tr) / period
    return atr

ema50 = calc_ema(closes, 50)
ema200 = calc_ema(closes, 200)
rsi = calc_rsi(closes, 14)
atr = calc_atr(highs, lows, closes, 14)
avg_volume = pd.Series(volumes).rolling(20).mean().values

def find_zigzag(highs, lows, depth=12, deviation=2.0):
    pivots = []
    direction = 0
    last_price = 0
    
    for i in range(depth, len(highs) - depth):
        is_ph = all(highs[i] > highs[i-j] and highs[i] > highs[i+j] for j in range(1, depth + 1))
        is_pl = all(lows[i] < lows[i-j] and lows[i] < lows[i+j] for j in range(1, depth + 1))
        
        if is_ph:
            if direction == -1 and last_price > 0 and abs(highs[i] - last_price) / last_price * 100 >= deviation:
                pivots.append((i, highs[i], 1))
                direction, last_price = 1, highs[i]
            elif direction == 1 and highs[i] > last_price and pivots:
                pivots[-1] = (i, highs[i], 1)
                last_price = highs[i]
            elif not pivots:
                pivots.append((i, highs[i], 1))
                direction, last_price = 1, highs[i]
        
        if is_pl:
            if direction == 1 and last_price > 0 and abs(lows[i] - last_price) / last_price * 100 >= deviation:
                pivots.append((i, lows[i], -1))
                direction, last_price = -1, lows[i]
            elif direction == -1 and lows[i] < last_price and pivots:
                pivots[-1] = (i, lows[i], -1)
                last_price = lows[i]
            elif not pivots:
                pivots.append((i, lows[i], -1))
                direction, last_price = -1, lows[i]
    
    return pivots

pivots = find_zigzag(highs, lows, 12, 2.0)

def backtest(params):
    min_strength = params['min_strength']
    sl_pct = params['sl_pct']
    tp_fib = params['tp_fib']
    signal_gap = params['signal_gap']
    use_trend_filter = params['use_trend_filter']
    use_rsi_filter = params['use_rsi_filter']
    use_volume_filter = params['use_volume_filter']
    require_sweep = params['require_sweep']
    
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
        
        # Filters
        trend_ok = not use_trend_filter or (closes[i] > ema200[i])
        rsi_ok = not use_rsi_filter or (rsi[i] < 50)  # Not overbought
        volume_ok = not use_volume_filter or (volumes[i] > avg_volume[i] * 0.8 if not np.isnan(avg_volume[i]) else True)
        
        # Sweep detection
        recent_low = min(lows[max(0,i-10):i]) if i > 10 else lows[i]
        swept = lows[i] < recent_low and closes[i] > recent_low
        sweep_ok = not require_sweep or swept
        
        # Wave 2 setup
        wave2_setup = False
        wave1_size = 0
        if p2[2] == -1 and p1[2] == 1 and p0[2] == -1:
            wave1_size = p1[1] - p2[1]
            if wave1_size > 0:
                retrace = (p1[1] - p0[1]) / wave1_size
                wave2_setup = 0.5 <= retrace <= 0.786
        
        # Scoring
        score = 0
        if in_discount: score += 2
        if wave2_setup: score += 3
        if closes[i] > opens[i]: score += 1
        
        ote_price = swing_high - (swing_high - swing_low) * 0.618
        if swing_low <= closes[i] <= ote_price: score += 3
        if swept: score += 2
        if trend_ok and use_trend_filter: score += 1
        if rsi_ok and use_rsi_filter: score += 1
        
        # Signal
        if score >= min_strength and in_discount and closes[i] > opens[i] and trend_ok and rsi_ok and volume_ok and sweep_ok:
            if i - last_signal_idx > signal_gap:
                entry = closes[i]
                tp = entry + (wave1_size * tp_fib if wave1_size > 0 else entry * 0.02)
                sl = entry * (1 - sl_pct / 100)
                signals.append({'idx': i, 'entry': entry, 'tp': tp, 'sl': sl, 'result': None})
                last_signal_idx = i
    
    wins, losses = 0, 0
    for sig in signals:
        for j in range(sig['idx'] + 1, min(sig['idx'] + 100, len(closes))):
            if highs[j] >= sig['tp']:
                wins += 1
                break
            elif lows[j] <= sig['sl']:
                losses += 1
                break
    
    total = wins + losses
    return {
        'params': params,
        'signals': len(signals),
        'wins': wins,
        'losses': losses,
        'win_rate': (wins / total * 100) if total > 0 else 0
    }

# Test grid with logic variations
param_grid = {
    'min_strength': [6, 7, 8],
    'sl_pct': [2.5, 3.0, 3.5],
    'tp_fib': [0.5, 0.618, 0.786],
    'signal_gap': [12, 15, 18],
    'use_trend_filter': [True, False],
    'use_rsi_filter': [True, False],
    'use_volume_filter': [True, False],
    'require_sweep': [True, False]
}

combinations = [dict(zip(param_grid.keys(), v)) for v in product(*param_grid.values())]
print(f"\nTesting {len(combinations)} combinations...\n")

results = []
best = None

for i, params in enumerate(combinations):
    result = backtest(params)
    results.append(result)
    if result['win_rate'] > (best['win_rate'] if best else 0) and result['signals'] >= 10:
        best = result
    if (i + 1) % 200 == 0:
        print(f"Progress: {i+1}/{len(combinations)} - Best so far: {best['win_rate']:.1f}%" if best else f"Progress: {i+1}/{len(combinations)}")

results.sort(key=lambda x: (x['win_rate'], x['signals']), reverse=True)

print("\n" + "="*70)
print("TOP 10 RESULTS")
print("="*70)

for i, r in enumerate(results[:10]):
    if r['signals'] >= 5:
        p = r['params']
        print(f"\n#{i+1} Win Rate: {r['win_rate']:.1f}% ({r['wins']}/{r['wins']+r['losses']}) - {r['signals']} signals")
        print(f"   min_str={p['min_strength']}, SL={p['sl_pct']}%, TP={p['tp_fib']}, gap={p['signal_gap']}")
        print(f"   trend={p['use_trend_filter']}, rsi={p['use_rsi_filter']}, vol={p['use_volume_filter']}, sweep={p['require_sweep']}")

print("\n" + "="*70)
print("BEST CONFIGURATION")
print("="*70)
if best:
    print(f"\nWin Rate: {best['win_rate']:.1f}%")
    print(f"Signals: {best['signals']} ({best['wins']} wins, {best['losses']} losses)")
    print(f"\nParameters:")
    for k, v in best['params'].items():
        print(f"  {k}: {v}")
