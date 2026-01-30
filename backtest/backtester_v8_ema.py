"""
Backtester v8 - EMA PULLBACK in Trend
Simple but potentially effective:
1. Trend: Price above EMA
2. Entry: Pullback touches EMA and bounces
3. SL: Below recent swing low
4. TP: R:R ratio

This is a classic trend-following strategy that often has good win rates.
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import List

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

class EMAPullbackBacktester:
    def __init__(self, df: pd.DataFrame, params: dict = None):
        self.df = df.copy()
        self.df.columns = [str(c).lower() for c in self.df.columns]
        
        self.params = {
            'ema_fast': 20,       # Fast EMA for pullback
            'ema_slow': 50,       # Slow EMA for trend
            'swing_lookback': 10, # Bars to find swing low
            'signal_gap': 5,
            'rr_ratio': 1.0,
            'touch_tolerance': 0.002,  # 0.2% tolerance for EMA touch
            'bounce_candles': 2,  # Require N bullish candles after touch
            'use_rsi': True,
            'rsi_min': 30,        # RSI must be above this (not too oversold)
            'rsi_max': 60,        # RSI must be below this (room to grow)
        }
        if params:
            self.params.update(params)
        
        self.signals = []
        self._ema_fast = None
        self._ema_slow = None
        self._rsi = None
    
    def calculate_indicators(self):
        # EMAs
        self._ema_fast = self.df['close'].ewm(span=self.params['ema_fast']).mean()
        self._ema_slow = self.df['close'].ewm(span=self.params['ema_slow']).mean()
        
        # RSI
        delta = self.df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        self._rsi = 100 - (100 / (1 + rs))
    
    def is_uptrend(self, bar: int) -> bool:
        """Check if we're in an uptrend"""
        if bar < self.params['ema_slow']:
            return False
        return (self.df['close'].iloc[bar] > self._ema_slow.iloc[bar] and
                self._ema_fast.iloc[bar] > self._ema_slow.iloc[bar])
    
    def check_ema_touch(self, bar: int) -> bool:
        """Check if price recently touched the fast EMA and bounced"""
        tol = self.params['touch_tolerance']
        ema = self._ema_fast.iloc[bar]
        
        # Check if low touched EMA (within tolerance)
        if self.df['low'].iloc[bar] <= ema * (1 + tol):
            # Check if it bounced (closed above EMA)
            if self.df['close'].iloc[bar] > ema:
                return True
        
        return False
    
    def check_bounce_confirmation(self, bar: int) -> bool:
        """Check for bullish confirmation after touch"""
        n = self.params.get('bounce_candles', 2)
        
        # Current candle should be bullish
        if self.df['close'].iloc[bar] <= self.df['open'].iloc[bar]:
            return False
        
        # Count recent bullish candles
        bullish_count = 0
        for i in range(max(0, bar - n + 1), bar + 1):
            if self.df['close'].iloc[i] > self.df['open'].iloc[i]:
                bullish_count += 1
        
        return bullish_count >= n
    
    def check_rsi(self, bar: int) -> bool:
        """Check RSI conditions"""
        if not self.params.get('use_rsi', True):
            return True
        
        rsi = self._rsi.iloc[bar]
        if pd.isna(rsi):
            return False
        
        return self.params['rsi_min'] <= rsi <= self.params['rsi_max']
    
    def find_swing_low(self, bar: int) -> float:
        """Find recent swing low for SL placement"""
        lookback = self.params['swing_lookback']
        start = max(0, bar - lookback)
        return self.df['low'].iloc[start:bar+1].min()
    
    def run_backtest(self) -> BacktestResult:
        self.signals = []
        self.calculate_indicators()
        
        last_signal_bar = -self.params['signal_gap'] - 1
        
        for bar in range(self.params['ema_slow'] + 5, len(self.df) - 1):
            if bar - last_signal_bar <= self.params['signal_gap']:
                continue
            
            # Check trend
            if not self.is_uptrend(bar):
                continue
            
            # Check EMA touch
            if not self.check_ema_touch(bar):
                continue
            
            # Check bounce confirmation
            if not self.check_bounce_confirmation(bar):
                continue
            
            # Check RSI
            if not self.check_rsi(bar):
                continue
            
            # Create signal
            entry = self.df['close'].iloc[bar]
            swing_low = self.find_swing_low(bar)
            sl = swing_low * 0.998  # SL just below swing low
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
