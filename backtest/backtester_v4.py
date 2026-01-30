"""
Elliott + ICT Backtester v4 - DATA-DRIVEN IMPROVEMENTS
Based on analysis of winning vs losing trades:
1. Positive momentum filter (3-bar momentum > 0)
2. Price position filter (price > 0.4 in 20-bar range)
3. EMA proximity filter (price near/above EMA)
4. Body ratio filter (strong candles)
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class Signal:
    bar: int
    entry: float
    tp: float
    sl: float
    filled: bool = False
    filled_bar: int = 0
    result: int = 0

@dataclass
class BacktestResult:
    total: int
    wins: int
    losses: int
    open_trades: int
    win_rate: float
    signals: List[Signal]

class ElliottICTBacktesterV4:
    def __init__(self, df: pd.DataFrame, params: dict = None):
        self.df = df.copy()
        self.df.columns = [str(c).lower() for c in self.df.columns]
        
        self.params = {
            'zz_depth': 3,
            'zz_dev': 0.2,
            'signal_gap': 5,
            'fib_entry_level': 0.786,
            'fib_tolerance': 0.10,
            'rr_ratio': 1.0,
            'ema_period': 50,
            # NEW data-driven filters
            'use_momentum_filter': True,
            'momentum_bars': 3,
            'min_momentum': 0.0,  # Must be positive
            'use_position_filter': True,
            'min_price_position': 0.35,
            'use_ema_filter': True,
            'max_ema_distance': 2.0,  # Max % below EMA
            'use_body_filter': True,
            'min_body_ratio': 0.3,
        }
        if params:
            self.params.update(params)
        
        self.signals = []
        self.zigzag_points = []
        self._ema = None
        
    def calculate_ema(self, period=50) -> pd.Series:
        if self._ema is None:
            self._ema = self.df['close'].ewm(span=period).mean()
        return self._ema
    
    def calculate_zigzag(self) -> List[Tuple[int, float, int]]:
        depth = self.params['zz_depth']
        dev = self.params['zz_dev']
        highs = self.df['high'].values
        lows = self.df['low'].values
        points = []
        direction = 0
        last_price = 0.0
        
        for i in range(depth, len(self.df) - depth):
            is_ph = all(highs[i] > highs[i - j] and highs[i] > highs[i + j] for j in range(1, depth + 1))
            is_pl = all(lows[i] < lows[i - j] and lows[i] < lows[i + j] for j in range(1, depth + 1))
            
            if is_ph and direction != 1:
                if last_price == 0 or abs(highs[i] - last_price) / last_price * 100 >= dev:
                    if direction == 1 and points and highs[i] > points[-1][1]:
                        points[-1] = (i, highs[i], 1)
                    else:
                        points.append((i, highs[i], 1))
                    direction = 1
                    last_price = highs[i]
            
            if is_pl and direction != -1:
                if last_price == 0 or abs(lows[i] - last_price) / last_price * 100 >= dev:
                    if direction == -1 and points and lows[i] < points[-1][1]:
                        points[-1] = (i, lows[i], -1)
                    else:
                        points.append((i, lows[i], -1))
                    direction = -1
                    last_price = lows[i]
        
        self.zigzag_points = points
        return points
    
    def check_fib_entry(self, bar: int) -> Tuple[bool, float, float, float]:
        points = [p for p in self.zigzag_points if p[0] <= bar]
        if len(points) < 2:
            return False, 0.0, 0.0, 0.0
        
        p0 = points[-1]
        p1 = points[-2]
        swing_high = 0.0
        swing_low = 0.0
        
        if p1[2] == -1 and p0[2] == 1:
            swing_low = p1[1]
            swing_high = p0[1]
        elif len(points) >= 3:
            p2 = points[-3]
            if p2[2] == -1 and p1[2] == 1 and p0[2] == -1:
                swing_low = p2[1]
                swing_high = p1[1]
        
        if swing_high <= swing_low:
            return False, 0.0, 0.0, 0.0
        
        fib_level = self.params['fib_entry_level']
        fib_price = swing_high - ((swing_high - swing_low) * fib_level)
        
        close = self.df['close'].iloc[bar]
        low = self.df['low'].iloc[bar]
        tolerance = (swing_high - swing_low) * self.params['fib_tolerance']
        
        at_fib = low <= fib_price + tolerance and close >= fib_price - tolerance
        return at_fib, fib_price, swing_high, swing_low
    
    def check_momentum(self, bar: int) -> bool:
        """Check if momentum is positive (price rising over N bars)"""
        if not self.params.get('use_momentum_filter', True):
            return True
        
        n = self.params.get('momentum_bars', 3)
        if bar < n:
            return True
        
        momentum = (self.df['close'].iloc[bar] - self.df['close'].iloc[bar-n]) / self.df['close'].iloc[bar-n] * 100
        return momentum >= self.params.get('min_momentum', 0.0)
    
    def check_price_position(self, bar: int) -> bool:
        """Check if price is in upper part of 20-bar range"""
        if not self.params.get('use_position_filter', True):
            return True
        
        if bar < 20:
            return True
        
        high_20 = self.df['high'].iloc[bar-20:bar+1].max()
        low_20 = self.df['low'].iloc[bar-20:bar+1].min()
        range_20 = high_20 - low_20
        
        if range_20 == 0:
            return True
        
        position = (self.df['close'].iloc[bar] - low_20) / range_20
        return position >= self.params.get('min_price_position', 0.35)
    
    def check_ema_proximity(self, bar: int) -> bool:
        """Check if price is near or above EMA"""
        if not self.params.get('use_ema_filter', True):
            return True
        
        ema = self.calculate_ema(self.params.get('ema_period', 50))
        if pd.isna(ema.iloc[bar]):
            return True
        
        distance = (self.df['close'].iloc[bar] - ema.iloc[bar]) / ema.iloc[bar] * 100
        # Allow price to be up to max_ema_distance% below EMA
        return distance >= -self.params.get('max_ema_distance', 2.0)
    
    def check_body_ratio(self, bar: int) -> bool:
        """Check if candle has strong body (not indecisive)"""
        if not self.params.get('use_body_filter', True):
            return True
        
        o = self.df['open'].iloc[bar]
        h = self.df['high'].iloc[bar]
        l = self.df['low'].iloc[bar]
        c = self.df['close'].iloc[bar]
        
        full_range = h - l
        if full_range == 0:
            return False
        
        body = abs(c - o)
        ratio = body / full_range
        
        return ratio >= self.params.get('min_body_ratio', 0.3) and c > o  # Must be bullish
    
    def run_backtest(self) -> BacktestResult:
        self.signals = []
        self.calculate_zigzag()
        
        last_signal_bar = -self.params['signal_gap'] - 1
        
        for bar in range(max(20, self.params['zz_depth'] + 1), len(self.df) - 1):
            if bar - last_signal_bar <= self.params['signal_gap']:
                continue
            
            at_fib, fib_price, swing_high, swing_low = self.check_fib_entry(bar)
            if not at_fib:
                continue
            
            # Apply data-driven filters
            if not self.check_momentum(bar):
                continue
            
            if not self.check_price_position(bar):
                continue
            
            if not self.check_ema_proximity(bar):
                continue
            
            if not self.check_body_ratio(bar):
                continue
            
            # Create signal
            entry = self.df['close'].iloc[bar]
            sl_buffer = (swing_high - swing_low) * 0.02
            sl = swing_low - sl_buffer
            risk = entry - sl
            rr_ratio = self.params.get('rr_ratio', 1.0)
            tp = entry + (risk * rr_ratio)
            
            self.signals.append(Signal(bar=bar, entry=entry, tp=tp, sl=sl))
            last_signal_bar = bar
        
        # Process signals
        for signal in self.signals:
            signal.filled = True
            signal.filled_bar = signal.bar
            
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
            open_trades=sum(1 for s in self.signals if s.result == 0),
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
