"""
Elliott + ICT Backtester v7 - BREAKOUT + PULLBACK Strategy
Instead of Fib retracement, look for:
1. Break of Structure (BOS) - price breaks previous high
2. Pullback to the broken level
3. Entry on the pullback with SL below the pullback low
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import List, Tuple, Optional

@dataclass
class Signal:
    bar: int
    entry: float
    tp: float
    sl: float
    result: int = 0

@dataclass
class BacktestResult:
    total: int
    wins: int
    losses: int
    win_rate: float
    signals: List[Signal]

class BreakoutPullbackBacktester:
    def __init__(self, df: pd.DataFrame, params: dict = None):
        self.df = df.copy()
        self.df.columns = [str(c).lower() for c in self.df.columns]
        
        self.params = {
            'lookback': 20,  # Bars to look for swing high
            'pullback_pct': 0.5,  # Pullback must retrace at least 50%
            'max_pullback_pct': 1.0,  # But not more than 100%
            'signal_gap': 5,
            'rr_ratio': 1.0,
            'use_volume_confirm': True,
            'volume_mult': 1.2,  # Breakout candle volume > avg * mult
            'use_ema_filter': True,
            'ema_period': 50,
        }
        if params:
            self.params.update(params)
        
        self.signals = []
        self.swing_highs = []
    
    def find_swing_highs(self) -> List[Tuple[int, float]]:
        """Find all swing highs (local maximums)"""
        lookback = self.params['lookback']
        highs = self.df['high'].values
        swing_highs = []
        
        for i in range(lookback, len(self.df) - lookback):
            is_high = True
            for j in range(1, lookback + 1):
                if highs[i] <= highs[i-j] or highs[i] <= highs[i+j]:
                    is_high = False
                    break
            if is_high:
                swing_highs.append((i, highs[i]))
        
        self.swing_highs = swing_highs
        return swing_highs
    
    def check_breakout(self, bar: int) -> Optional[dict]:
        """Check if there was a recent breakout of a swing high"""
        lookback = self.params['lookback']
        
        # Find the most recent swing high before this bar
        relevant_highs = [(i, h) for i, h in self.swing_highs if i < bar - 3]
        if not relevant_highs:
            return None
        
        # Get the most recent swing high
        swing_bar, swing_high = max(relevant_highs, key=lambda x: x[0])
        
        # Check if price broke above this swing high recently
        for i in range(max(swing_bar + 1, bar - lookback), bar):
            if self.df['close'].iloc[i] > swing_high:
                # Found a breakout - now check for pullback
                breakout_bar = i
                breakout_high = self.df['high'].iloc[i]
                
                # Pullback should be between breakout and current bar
                if bar > breakout_bar + 1:
                    pullback_low = self.df['low'].iloc[breakout_bar+1:bar].min()
                    pullback_range = breakout_high - swing_high
                    
                    if pullback_range > 0:
                        pullback_depth = (breakout_high - pullback_low) / pullback_range
                        
                        # Check if pullback is valid
                        min_pb = self.params['pullback_pct']
                        max_pb = self.params['max_pullback_pct']
                        
                        if min_pb <= pullback_depth <= max_pb:
                            # Check if current price is bouncing
                            if self.df['close'].iloc[bar] > self.df['open'].iloc[bar]:
                                return {
                                    'swing_high': swing_high,
                                    'breakout_bar': breakout_bar,
                                    'breakout_high': breakout_high,
                                    'pullback_low': pullback_low,
                                }
        
        return None
    
    def check_volume_confirm(self, bar: int, breakout_bar: int) -> bool:
        """Check if breakout had volume confirmation"""
        if not self.params.get('use_volume_confirm', True):
            return True
        
        if 'volume' not in self.df.columns:
            return True
        
        avg_vol = self.df['volume'].iloc[max(0, breakout_bar-20):breakout_bar].mean()
        breakout_vol = self.df['volume'].iloc[breakout_bar]
        
        return breakout_vol > avg_vol * self.params['volume_mult']
    
    def check_ema_filter(self, bar: int) -> bool:
        """Check if price is above EMA (bullish)"""
        if not self.params.get('use_ema_filter', True):
            return True
        
        ema = self.df['close'].ewm(span=self.params['ema_period']).mean()
        return self.df['close'].iloc[bar] > ema.iloc[bar]
    
    def run_backtest(self) -> BacktestResult:
        self.signals = []
        self.find_swing_highs()
        
        last_signal_bar = -self.params['signal_gap'] - 1
        
        for bar in range(self.params['lookback'] + 5, len(self.df) - 1):
            if bar - last_signal_bar <= self.params['signal_gap']:
                continue
            
            # Check for breakout + pullback setup
            setup = self.check_breakout(bar)
            if not setup:
                continue
            
            # Check volume confirmation
            if not self.check_volume_confirm(bar, setup['breakout_bar']):
                continue
            
            # Check EMA filter
            if not self.check_ema_filter(bar):
                continue
            
            # Create signal
            entry = self.df['close'].iloc[bar]
            sl = setup['pullback_low'] * 0.998  # SL below pullback low
            risk = entry - sl
            
            if risk <= 0:
                continue
            
            rr_ratio = self.params.get('rr_ratio', 1.0)
            tp = entry + (risk * rr_ratio)
            
            self.signals.append(Signal(bar=bar, entry=entry, tp=tp, sl=sl))
            last_signal_bar = bar
        
        # Process signals
        for signal in self.signals:
            for bar in range(signal.bar + 1, len(self.df)):
                low = self.df['low'].iloc[bar]
                high = self.df['high'].iloc[bar]
                
                if low <= signal.sl:
                    signal.result = -1
                    break
                
                if high >= signal.tp:
                    signal.result = 1
                    break
        
        wins = sum(1 for s in self.signals if s.result == 1)
        losses = sum(1 for s in self.signals if s.result == -1)
        total = wins + losses
        win_rate = (wins / total * 100) if total > 0 else 0.0
        
        return BacktestResult(
            total=total,
            wins=wins,
            losses=losses,
            win_rate=win_rate,
            signals=self.signals
        )

def load_data(filepath: str) -> pd.DataFrame:
    df = pd.read_csv(filepath)
    df.columns = [str(c).lower() for c in df.columns]
    if 'time' in df.columns:
        df['time'] = pd.to_datetime(df['time'])
        df = df.set_index('time')
    return df
