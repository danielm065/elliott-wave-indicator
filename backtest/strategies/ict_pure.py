"""
Strategy 1: ICT Pure - FVG + SMT without Elliott Waves
"""
import pandas as pd
import numpy as np
from .base import BaseStrategy, Signal

class ICTPureStrategy(BaseStrategy):
    """
    ICT Pure Strategy:
    - Entry: FVG fill in discount zone
    - Confirmation: Bullish candle after FVG fill
    - SL: Below swing low
    - TP: Based on RR ratio
    """
    
    def find_fvg(self, bar: int, lookback: int = 20):
        """Find Fair Value Gaps"""
        fvgs = []
        
        for i in range(max(2, bar - lookback), bar):
            # Bullish FVG: gap between candle 1 high and candle 3 low
            if i >= 2:
                high_1 = self.df['high'].iloc[i-2]
                low_3 = self.df['low'].iloc[i]
                
                if low_3 > high_1:  # Gap exists
                    fvgs.append({
                        'type': 'bullish',
                        'top': low_3,
                        'bottom': high_1,
                        'bar': i
                    })
        
        return fvgs
    
    def find_swing_low(self, bar: int, lookback: int = 20):
        """Find recent swing low"""
        depth = self.params.get('swing_depth', 5)
        
        for i in range(bar - 1, max(depth, bar - lookback), -1):
            if i < depth:
                continue
            
            is_low = True
            for j in range(1, depth + 1):
                if i - j < 0 or i + j >= len(self.df):
                    is_low = False
                    break
                if self.df['low'].iloc[i] >= self.df['low'].iloc[i-j] or \
                   self.df['low'].iloc[i] >= self.df['low'].iloc[i+j]:
                    is_low = False
                    break
            
            if is_low:
                return self.df['low'].iloc[i], i
        
        return self.df['low'].iloc[bar - lookback:bar].min(), bar - 5
    
    def generate_signals(self):
        signals = []
        last_signal_bar = -100
        
        rr_ratio = self.params.get('rr_ratio', 2.0)
        signal_gap = self.params.get('signal_gap', 10)
        
        for bar in range(30, len(self.df) - 1):
            if bar - last_signal_bar <= signal_gap:
                continue
            
            # Find FVGs
            fvgs = self.find_fvg(bar)
            
            if not fvgs:
                continue
            
            # Check if price filled any FVG
            current_low = self.df['low'].iloc[bar]
            
            for fvg in fvgs:
                if fvg['type'] == 'bullish':
                    # Price entered the FVG zone
                    if current_low <= fvg['top'] and current_low >= fvg['bottom']:
                        # Bullish candle confirmation
                        if self.df['close'].iloc[bar] > self.df['open'].iloc[bar]:
                            # Entry at close
                            entry = self.df['close'].iloc[bar]
                            
                            # SL below swing low
                            swing_low, _ = self.find_swing_low(bar)
                            sl = swing_low * 0.998  # Small buffer
                            
                            # TP based on RR
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
                            break
        
        return signals
