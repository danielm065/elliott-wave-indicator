"""
Strategy 4: Dynamic TP based on ATR
"""
import pandas as pd
import numpy as np
from .base import BaseStrategy, Signal

class DynamicTPStrategy(BaseStrategy):
    """
    Dynamic TP Strategy:
    - Same entry logic as Elliott/Fib
    - TP: Based on ATR (volatility-adjusted)
    - SL: Below swing low
    """
    
    def calculate_atr(self, bar: int, period: int = 14):
        """Calculate ATR"""
        if bar < period:
            return None
        
        tr_list = []
        for i in range(bar - period, bar):
            high = self.df['high'].iloc[i]
            low = self.df['low'].iloc[i]
            prev_close = self.df['close'].iloc[i-1] if i > 0 else self.df['close'].iloc[i]
            
            tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
            tr_list.append(tr)
        
        return sum(tr_list) / len(tr_list)
    
    def find_swing_points(self, bar: int, depth: int = 5):
        """Find swing high and low"""
        swing_high = None
        swing_low = None
        
        for i in range(bar - 1, max(depth, bar - 30), -1):
            if i < depth:
                continue
            
            # Check for swing high
            if swing_high is None:
                is_high = all(
                    self.df['high'].iloc[i] >= self.df['high'].iloc[i-j] and
                    self.df['high'].iloc[i] >= self.df['high'].iloc[i+j]
                    for j in range(1, min(depth+1, len(self.df)-i))
                    if i+j < len(self.df) and i-j >= 0
                )
                if is_high:
                    swing_high = self.df['high'].iloc[i]
            
            # Check for swing low
            if swing_low is None:
                is_low = all(
                    self.df['low'].iloc[i] <= self.df['low'].iloc[i-j] and
                    self.df['low'].iloc[i] <= self.df['low'].iloc[i+j]
                    for j in range(1, min(depth+1, len(self.df)-i))
                    if i+j < len(self.df) and i-j >= 0
                )
                if is_low:
                    swing_low = self.df['low'].iloc[i]
            
            if swing_high and swing_low:
                break
        
        return swing_high, swing_low
    
    def generate_signals(self):
        signals = []
        last_signal_bar = -100
        
        signal_gap = self.params.get('signal_gap', 10)
        atr_mult = self.params.get('atr_mult', 3.0)  # TP = ATR * multiplier
        fib_level = self.params.get('fib_entry_level', 0.618)
        
        for bar in range(30, len(self.df) - 1):
            if bar - last_signal_bar <= signal_gap:
                continue
            
            swing_high, swing_low = self.find_swing_points(bar)
            
            if not swing_high or not swing_low or swing_high <= swing_low:
                continue
            
            # Fib retracement level
            fib_price = swing_high - ((swing_high - swing_low) * fib_level)
            
            # Check if price at fib level
            current_low = self.df['low'].iloc[bar]
            current_close = self.df['close'].iloc[bar]
            
            tolerance = (swing_high - swing_low) * 0.05
            
            if current_low <= fib_price + tolerance and current_low >= fib_price - tolerance:
                # Bullish candle
                if current_close > self.df['open'].iloc[bar]:
                    atr = self.calculate_atr(bar)
                    if not atr:
                        continue
                    
                    entry = current_close
                    sl = swing_low * 0.998
                    
                    # Dynamic TP based on ATR
                    tp = entry + (atr * atr_mult)
                    
                    signals.append(Signal(
                        bar=bar,
                        entry=entry,
                        tp=tp,
                        sl=sl,
                        direction=1
                    ))
                    last_signal_bar = bar
        
        return signals
