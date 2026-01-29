"""
Strategy 2: Breakout - Entry on high/low break
"""
import pandas as pd
import numpy as np
from .base import BaseStrategy, Signal

class BreakoutStrategy(BaseStrategy):
    """
    Breakout Strategy:
    - Entry: Break above recent high
    - SL: Below recent low
    - TP: Based on RR ratio
    """
    
    def find_range(self, bar: int, lookback: int = 20):
        """Find recent high and low"""
        start = max(0, bar - lookback)
        high = self.df['high'].iloc[start:bar].max()
        low = self.df['low'].iloc[start:bar].min()
        return high, low
    
    def generate_signals(self):
        signals = []
        last_signal_bar = -100
        
        rr_ratio = self.params.get('rr_ratio', 2.0)
        signal_gap = self.params.get('signal_gap', 10)
        lookback = self.params.get('lookback', 20)
        
        for bar in range(lookback + 1, len(self.df) - 1):
            if bar - last_signal_bar <= signal_gap:
                continue
            
            # Find range
            range_high, range_low = self.find_range(bar, lookback)
            
            # Breakout: close above range high
            if self.df['close'].iloc[bar] > range_high:
                # Additional filter: strong candle
                candle_range = self.df['high'].iloc[bar] - self.df['low'].iloc[bar]
                body = abs(self.df['close'].iloc[bar] - self.df['open'].iloc[bar])
                
                if body > candle_range * 0.5:  # Body > 50% of range
                    entry = self.df['close'].iloc[bar]
                    sl = range_low * 0.998
                    
                    risk = entry - sl
                    tp = entry + (risk * rr_ratio)
                    
                    signals.append(Signal(
                        bar=bar,
                        entry=entry,
                        tp=tp,
                        sl=sl,
                        direction=1
                    ))
                    last_signal_bar = bar
        
        return signals
