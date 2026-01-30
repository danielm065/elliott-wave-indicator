"""
Deep analysis - what makes winning trades vs losing trades?
Find patterns we can exploit.
"""
import sys
sys.path.insert(0, r'C:\Users\danie\projects\elliott-wave-indicator\backtest')

from backtester import ElliottICTBacktester, load_data
from pathlib import Path
import numpy as np
import pandas as pd

DATA_DIR = Path(r'C:\Users\danie\projects\elliott-wave-indicator\data')

# Test on a few representative assets
FILES = {
    'GOOG': 'BATS_GOOG, 60_78270.csv',      # Failing asset
    'AMD': 'BATS_AMD, 60_2853d.csv',         # Passing asset
    'ETHUSD': 'BINANCE_ETHUSD, 60_b3215.csv', # Crypto - failing
    'BTCUSDT': 'BINANCE_BTCUSDT, 60_b6ebd.csv', # Crypto - passing
}

# Best params from earlier tests
PARAMS = {
    'zz_depth': 3, 'fib_entry_level': 0.786, 'fib_tolerance': 0.05,
    'rsi_threshold': 30, 'signal_gap': 5, 'use_trend_filter': False,
    'use_volume_filter': True, 'use_rsi_filter': True,
    'rr_ratio': 1.0, 'zz_dev': 0.2, 'ema_period': 200,
}

def analyze_trades(asset, file):
    path = DATA_DIR / file
    if not path.exists():
        return
    
    df = load_data(str(path))
    bt = ElliottICTBacktester(df, PARAMS)
    result = bt.run_backtest()
    
    print(f"\n{'='*60}")
    print(f"{asset}: {result.wins}/{result.wins + result.losses} = {result.win_rate:.0f}%")
    print(f"{'='*60}")
    
    # Calculate metrics for each trade
    wins = []
    losses = []
    
    for signal in bt.signals:
        if signal.result == 0:
            continue
            
        bar = signal.bar
        
        # Calculate metrics at entry
        close = df['close'].iloc[bar]
        open_p = df['open'].iloc[bar]
        high = df['high'].iloc[bar]
        low = df['low'].iloc[bar]
        
        # Candle characteristics
        body = abs(close - open_p)
        full_range = high - low
        body_ratio = body / full_range if full_range > 0 else 0
        is_bullish = close > open_p
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = (100 - (100 / (1 + rs))).iloc[bar]
        
        # Volume ratio
        avg_vol = df['volume'].rolling(20).mean().iloc[bar]
        vol_ratio = df['volume'].iloc[bar] / avg_vol if avg_vol > 0 else 1
        
        # Price position in range
        range_20 = df['high'].rolling(20).max().iloc[bar] - df['low'].rolling(20).min().iloc[bar]
        if range_20 > 0:
            price_pos = (close - df['low'].rolling(20).min().iloc[bar]) / range_20
        else:
            price_pos = 0.5
        
        # Previous candles momentum
        if bar >= 3:
            momentum = (df['close'].iloc[bar] - df['close'].iloc[bar-3]) / df['close'].iloc[bar-3] * 100
        else:
            momentum = 0
        
        # Distance from EMA
        ema = df['close'].ewm(span=50).mean().iloc[bar]
        ema_dist = (close - ema) / ema * 100
        
        trade_data = {
            'bar': bar,
            'body_ratio': body_ratio,
            'is_bullish': is_bullish,
            'rsi': rsi,
            'vol_ratio': vol_ratio,
            'price_pos': price_pos,
            'momentum': momentum,
            'ema_dist': ema_dist,
            'risk': signal.entry - signal.sl,
        }
        
        if signal.result == 1:
            wins.append(trade_data)
        else:
            losses.append(trade_data)
    
    if not wins and not losses:
        print("No completed trades")
        return
    
    print(f"\nWINS ({len(wins)}) vs LOSSES ({len(losses)}):")
    print("-" * 40)
    
    metrics = ['body_ratio', 'rsi', 'vol_ratio', 'price_pos', 'momentum', 'ema_dist']
    
    for m in metrics:
        win_avg = np.mean([w[m] for w in wins]) if wins else 0
        loss_avg = np.mean([l[m] for l in losses]) if losses else 0
        print(f"{m:12}: WIN={win_avg:7.2f}  LOSS={loss_avg:7.2f}  diff={win_avg-loss_avg:+.2f}")
    
    # Bullish candle ratio
    win_bullish = sum(1 for w in wins if w['is_bullish']) / len(wins) * 100 if wins else 0
    loss_bullish = sum(1 for l in losses if l['is_bullish']) / len(losses) * 100 if losses else 0
    print(f"{'bullish%':12}: WIN={win_bullish:7.1f}  LOSS={loss_bullish:7.1f}")

print("Analyzing trade patterns...\n")

for asset, file in FILES.items():
    try:
        analyze_trades(asset, file)
    except Exception as e:
        print(f"{asset}: Error - {e}")

print("\n" + "="*60)
print("INSIGHTS: Look for significant differences between WIN and LOSS")
print("These can become new filters to improve accuracy")
print("="*60)
