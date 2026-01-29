"""
Strategy 5: Momentum - RSI + EMA trend
"""
import pandas as pd
import numpy as np
from .base import BaseStrategy, Signal

class MomentumStrategy(BaseStrategy):
    """
    Momentum Strategy:
    - Entry: RSI oversold + price above EMA + bullish candle
    - SL: Below recent low
    - TP: Based on RR ratio
    """
    
    def calculate_rsi(self, bar: int, period: int = 14):
        """Calculate RSI"""
        if bar < period:
            return 50
        
        gains = []
        losses = []
        
        for i in range(bar - period, bar):
            change = self.df['close'].iloc[i] - self.df['close'].iloc[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def calculate_ema(self, bar: int, period: int = 50):
        """Calculate EMA"""
        if bar < period:
            return self.df['close'].iloc[bar]
        
        mult = 2 / (period + 1)
        ema = self.df['close'].iloc[bar - period]
        
        for i in range(bar - period + 1, bar + 1):
            ema = (self.df['close'].iloc[i] - ema) * mult + ema
        
        return ema
    
    def generate_signals(self):
        signals = []
        last_signal_bar = -100
        
        rr_ratio = self.params.get('rr_ratio', 2.0)
        signal_gap = self.params.get('signal_gap', 10)
        rsi_oversold = self.params.get('rsi_oversold', 35)
        ema_period = self.params.get('ema_period', 50)
        lookback = self.params.get('lookback', 10)
        
        for bar in range(max(50, ema_period) + 1, len(self.df) - 1):
            if bar - last_signal_bar <= signal_gap:
                continue
            
            rsi = self.calculate_rsi(bar)
            ema = self.calculate_ema(bar, ema_period)
            
            current_close = self.df['close'].iloc[bar]
            current_open = self.df['open'].iloc[bar]
            
            # Conditions:
            # 1. RSI was oversold recently
            recent_rsi_oversold = any(
                self.calculate_rsi(i) < rsi_oversold
                for i in range(max(0, bar - 5), bar)
            )
            
            # 2. Price above EMA (uptrend)
            above_ema = current_close > ema
            
            # 3. Bullish candle
            bullish = current_close > current_open
            
            # 4. RSI turning up
            rsi_turning_up = rsi > self.calculate_rsi(bar - 1)
            
            if recent_rsi_oversold and above_ema and bullish and rsi_turning_up:
                entry = current_close
                
                # SL below recent low
                recent_low = self.df['low'].iloc[bar - lookback:bar].min()
                sl = recent_low * 0.998
                
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
