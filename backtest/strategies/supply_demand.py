"""
Strategy 3: Supply/Demand Zones
"""
import pandas as pd
import numpy as np
from .base import BaseStrategy, Signal

class SupplyDemandStrategy(BaseStrategy):
    """
    Supply/Demand Strategy:
    - Entry: Bounce from demand zone
    - SL: Below demand zone
    - TP: At supply zone or RR ratio
    """
    
    def find_zones(self, bar: int, lookback: int = 50):
        """Find supply and demand zones"""
        demand_zones = []
        supply_zones = []
        
        for i in range(max(3, bar - lookback), bar - 3):
            # Demand zone: sharp move up from this area
            if i < 3:
                continue
            
            # Check for bullish engulfing or strong bullish candle
            candle_range = self.df['high'].iloc[i] - self.df['low'].iloc[i]
            body = self.df['close'].iloc[i] - self.df['open'].iloc[i]
            
            if body > 0 and body > candle_range * 0.6:  # Strong bullish
                # Check if price moved significantly after
                future_high = self.df['high'].iloc[i:min(i+10, bar)].max()
                move = (future_high - self.df['close'].iloc[i]) / self.df['close'].iloc[i]
                
                if move > 0.02:  # 2% move up
                    demand_zones.append({
                        'top': self.df['open'].iloc[i],
                        'bottom': self.df['low'].iloc[i],
                        'bar': i
                    })
            
            # Supply zone: sharp move down from this area
            if body < 0 and abs(body) > candle_range * 0.6:  # Strong bearish
                future_low = self.df['low'].iloc[i:min(i+10, bar)].min()
                move = (self.df['close'].iloc[i] - future_low) / self.df['close'].iloc[i]
                
                if move > 0.02:  # 2% move down
                    supply_zones.append({
                        'top': self.df['high'].iloc[i],
                        'bottom': self.df['open'].iloc[i],
                        'bar': i
                    })
        
        return demand_zones, supply_zones
    
    def generate_signals(self):
        signals = []
        last_signal_bar = -100
        
        rr_ratio = self.params.get('rr_ratio', 2.0)
        signal_gap = self.params.get('signal_gap', 10)
        
        for bar in range(50, len(self.df) - 1):
            if bar - last_signal_bar <= signal_gap:
                continue
            
            demand_zones, supply_zones = self.find_zones(bar)
            
            if not demand_zones:
                continue
            
            current_low = self.df['low'].iloc[bar]
            current_close = self.df['close'].iloc[bar]
            
            # Check if price touched a demand zone and bounced
            for zone in demand_zones:
                if current_low <= zone['top'] and current_low >= zone['bottom']:
                    # Bullish candle = bounce
                    if current_close > self.df['open'].iloc[bar]:
                        entry = current_close
                        sl = zone['bottom'] * 0.995
                        
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
