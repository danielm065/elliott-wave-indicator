"""
Elliott + ICT Backtester v3 - SIMPLER IMPROVEMENTS
Focus on:
1. Better exit logic (trailing SL)
2. Flexible Fib entry (multiple levels)
3. Simpler wave detection
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
    original_sl: float
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

class ElliottICTBacktesterV3:
    def __init__(self, df: pd.DataFrame, params: dict = None):
        self.df = df.copy()
        self.df.columns = [str(c).lower() for c in self.df.columns]
        
        self.params = {
            'zz_depth': 3,
            'zz_dev': 0.2,
            'signal_gap': 5,
            'fib_levels': [0.5, 0.618, 0.786],  # Multiple Fib levels
            'fib_tolerance': 0.10,
            'use_rsi_filter': True,
            'rsi_threshold': 40,
            'use_volume_filter': True,
            'use_trend_filter': False,
            'ema_period': 200,
            'rr_ratio': 1.0,
            'use_trailing_sl': True,
            'trailing_trigger': 0.5,  # Move SL to BE after 50% of target
            'require_bullish': True,
        }
        if params:
            self.params.update(params)
        
        self.signals = []
        self.zigzag_points = []
        
    def calculate_rsi(self, period=14) -> pd.Series:
        delta = self.df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
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
        """Check if price is at ANY of the Fib levels"""
        points = [p for p in self.zigzag_points if p[0] <= bar]
        if len(points) < 2:
            return False, 0.0, 0.0, 0.0
        
        p0 = points[-1]
        p1 = points[-2]
        
        swing_high = 0.0
        swing_low = 0.0
        
        # Bullish: we need Low -> High pattern
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
        
        close = self.df['close'].iloc[bar]
        low = self.df['low'].iloc[bar]
        
        swing_range = swing_high - swing_low
        tolerance = swing_range * self.params['fib_tolerance']
        
        # Check each Fib level
        fib_levels = self.params.get('fib_levels', [0.618])
        if not isinstance(fib_levels, list):
            fib_levels = [fib_levels]
        
        for fib_level in fib_levels:
            fib_price = swing_high - (swing_range * fib_level)
            
            # Price touched the fib level
            if low <= fib_price + tolerance and close >= fib_price - tolerance:
                return True, fib_price, swing_high, swing_low
        
        return False, 0.0, 0.0, 0.0
    
    def run_backtest(self) -> BacktestResult:
        self.signals = []
        self.calculate_zigzag()
        
        rsi = self.calculate_rsi()
        ema = self.df['close'].rolling(self.params['ema_period']).mean()
        avg_vol = self.df['volume'].rolling(20).mean()
        
        last_signal_bar = -self.params['signal_gap'] - 1
        
        for bar in range(self.params['zz_depth'] + 1, len(self.df) - 1):
            if bar - last_signal_bar <= self.params['signal_gap']:
                continue
            
            at_fib, fib_price, swing_high, swing_low = self.check_fib_entry(bar)
            if not at_fib:
                continue
            
            # RSI filter
            if self.params['use_rsi_filter']:
                if pd.isna(rsi.iloc[bar]) or rsi.iloc[bar] >= self.params['rsi_threshold']:
                    continue
            
            # Bullish candle
            if self.params.get('require_bullish', True):
                if self.df['close'].iloc[bar] <= self.df['open'].iloc[bar]:
                    continue
            
            # Trend filter
            if self.params['use_trend_filter']:
                if pd.isna(ema.iloc[bar]) or self.df['close'].iloc[bar] <= ema.iloc[bar]:
                    continue
            
            # Volume filter
            if self.params['use_volume_filter']:
                if not pd.isna(avg_vol.iloc[bar]) and self.df['volume'].iloc[bar] < avg_vol.iloc[bar] * 0.5:
                    continue
            
            # Create signal
            entry = self.df['close'].iloc[bar]
            sl_buffer = (swing_high - swing_low) * 0.02
            sl = swing_low - sl_buffer
            risk = entry - sl
            rr_ratio = self.params.get('rr_ratio', 1.0)
            tp = entry + (risk * rr_ratio)
            
            self.signals.append(Signal(bar=bar, entry=entry, tp=tp, sl=sl, original_sl=sl))
            last_signal_bar = bar
        
        # Process signals with trailing SL
        use_trailing = self.params.get('use_trailing_sl', True)
        trailing_trigger = self.params.get('trailing_trigger', 0.5)
        
        for signal in self.signals:
            signal.filled = True
            signal.filled_bar = signal.bar
            
            current_sl = signal.sl
            target_move = signal.tp - signal.entry
            trigger_price = signal.entry + (target_move * trailing_trigger)
            sl_moved = False
            
            for bar in range(signal.bar + 1, len(self.df)):
                low = self.df['low'].iloc[bar]
                high = self.df['high'].iloc[bar]
                
                # Move SL to breakeven if triggered
                if use_trailing and not sl_moved and high >= trigger_price:
                    current_sl = signal.entry  # Move SL to breakeven
                    signal.sl = current_sl
                    sl_moved = True
                
                # Check SL
                if low <= current_sl:
                    signal.result = -1 if not sl_moved else 0  # Breakeven counts as 0
                    break
                
                # Check TP
                if high >= signal.tp:
                    signal.result = 1
                    break
        
        # Count results (breakeven = not counted as loss)
        wins = sum(1 for s in self.signals if s.result == 1)
        losses = sum(1 for s in self.signals if s.result == -1)
        breakeven = sum(1 for s in self.signals if s.result == 0 and s.sl != s.original_sl)
        open_trades = sum(1 for s in self.signals if s.result == 0 and s.sl == s.original_sl)
        total = wins + losses
        win_rate = (wins / total * 100) if total > 0 else 0.0
        
        return BacktestResult(
            total=total,
            wins=wins,
            losses=losses,
            open_trades=open_trades + breakeven,
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
