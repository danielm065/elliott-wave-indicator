"""
Elliott + ICT Backtester v2 - IMPROVED
Key improvements:
1. Momentum confirmation (RSI rising)
2. ATR volatility filter
3. Candle pattern detection (reversal candles)
4. Wave quality scoring
5. Adaptive tolerance based on volatility
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
    filled: bool = False
    filled_bar: int = 0
    result: int = 0  # 0=open, 1=win, -1=loss

@dataclass
class BacktestResult:
    total: int
    wins: int
    losses: int
    open_trades: int
    win_rate: float
    signals: List[Signal]

class ElliottICTBacktesterV2:
    def __init__(self, df: pd.DataFrame, params: dict = None):
        self.df = df.copy()
        self.df.columns = [str(c).lower() for c in self.df.columns]
        
        required = ['open', 'high', 'low', 'close', 'volume']
        for col in required:
            if col not in self.df.columns:
                raise ValueError(f"Missing required column: {col}")
        
        # Default parameters
        self.params = {
            'zz_depth': 3,
            'zz_dev': 0.2,
            'signal_gap': 5,
            'fib_entry_level': 0.786,
            'fib_tolerance': 0.10,
            'use_rsi_filter': True,
            'rsi_threshold': 40,
            'use_volume_filter': True,
            'use_trend_filter': False,
            'ema_period': 200,
            'rr_ratio': 1.0,
            # NEW parameters
            'use_momentum_filter': True,
            'use_atr_filter': True,
            'atr_period': 14,
            'use_candle_filter': True,
            'use_wave_quality': True,
            'min_wave_quality': 0.5,
        }
        if params:
            self.params.update(params)
        
        self.signals: List[Signal] = []
        self.zigzag_points = []
        self._rsi = None
        self._atr = None
        self._ema = None
        
    def calculate_rsi(self, period=14) -> pd.Series:
        if self._rsi is None:
            delta = self.df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            self._rsi = 100 - (100 / (1 + rs))
        return self._rsi
    
    def calculate_atr(self, period=14) -> pd.Series:
        if self._atr is None:
            high = self.df['high']
            low = self.df['low']
            close = self.df['close']
            tr1 = high - low
            tr2 = abs(high - close.shift())
            tr3 = abs(low - close.shift())
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            self._atr = tr.rolling(window=period).mean()
        return self._atr
    
    def calculate_ema(self, period=200) -> pd.Series:
        if self._ema is None:
            self._ema = self.df['close'].ewm(span=period, adjust=False).mean()
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
            is_ph = True
            for j in range(1, depth + 1):
                if highs[i] <= highs[i - j] or highs[i] <= highs[i + j]:
                    is_ph = False
                    break
            
            is_pl = True
            for j in range(1, depth + 1):
                if lows[i] >= lows[i - j] or lows[i] >= lows[i + j]:
                    is_pl = False
                    break
            
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
    
    def check_wave_quality(self, bar: int) -> float:
        """
        Score wave quality 0-1
        Good waves: clean movement, not too choppy
        """
        points = [p for p in self.zigzag_points if p[0] <= bar]
        if len(points) < 3:
            return 0.0
        
        p0 = points[-1]
        p1 = points[-2]
        p2 = points[-3]
        
        # Wave 1: p2 to p1
        wave1_bars = p1[0] - p2[0]
        wave1_move = abs(p1[1] - p2[1])
        
        if wave1_bars == 0:
            return 0.0
        
        # Calculate how "clean" the wave is
        # Look at the path from p2 to p1
        start_bar = p2[0]
        end_bar = p1[0]
        
        if start_bar >= end_bar:
            return 0.0
        
        # Sum of actual bar-to-bar movements
        actual_path = 0.0
        for i in range(start_bar, end_bar):
            actual_path += abs(self.df['close'].iloc[i+1] - self.df['close'].iloc[i])
        
        if actual_path == 0:
            return 0.0
        
        # Efficiency = direct move / actual path (1.0 = perfect straight line)
        efficiency = wave1_move / actual_path
        
        return min(1.0, efficiency)
    
    def check_reversal_candle(self, bar: int) -> bool:
        """
        Check for bullish reversal candle patterns:
        - Hammer
        - Bullish engulfing
        - Piercing line
        """
        if bar < 1:
            return False
        
        o = self.df['open'].iloc[bar]
        h = self.df['high'].iloc[bar]
        l = self.df['low'].iloc[bar]
        c = self.df['close'].iloc[bar]
        
        o_prev = self.df['open'].iloc[bar-1]
        h_prev = self.df['high'].iloc[bar-1]
        l_prev = self.df['low'].iloc[bar-1]
        c_prev = self.df['close'].iloc[bar-1]
        
        body = abs(c - o)
        full_range = h - l
        
        if full_range == 0:
            return False
        
        body_ratio = body / full_range
        
        # Current bar is bullish
        is_bullish = c > o
        
        if not is_bullish:
            return False
        
        # Hammer: small body at top, long lower wick
        lower_wick = min(o, c) - l
        upper_wick = h - max(o, c)
        
        is_hammer = (lower_wick > body * 2) and (upper_wick < body * 0.5) and body_ratio < 0.4
        
        # Bullish engulfing: current body engulfs previous body
        prev_is_bearish = c_prev < o_prev
        engulfs = c > o_prev and o < c_prev
        is_engulfing = prev_is_bearish and engulfs and body > abs(c_prev - o_prev)
        
        # Strong bullish bar (large body, small wicks)
        is_strong = body_ratio > 0.6 and lower_wick < body * 0.3
        
        return is_hammer or is_engulfing or is_strong
    
    def check_momentum_rising(self, bar: int) -> bool:
        """Check if RSI is rising (momentum confirmation)"""
        rsi = self.calculate_rsi()
        if bar < 3:
            return False
        
        rsi_now = rsi.iloc[bar]
        rsi_prev = rsi.iloc[bar-2]
        
        if pd.isna(rsi_now) or pd.isna(rsi_prev):
            return False
        
        return rsi_now > rsi_prev
    
    def check_atr_ok(self, bar: int) -> bool:
        """Check if volatility is in good range (not too low, not extreme)"""
        atr = self.calculate_atr()
        if bar < 20:
            return True
        
        atr_now = atr.iloc[bar]
        atr_avg = atr.iloc[bar-20:bar].mean()
        
        if pd.isna(atr_now) or pd.isna(atr_avg) or atr_avg == 0:
            return True
        
        ratio = atr_now / atr_avg
        
        # Allow if ATR is between 0.5x and 2x average
        return 0.5 <= ratio <= 2.0
    
    def check_fib_entry(self, bar: int) -> Tuple[bool, float, float, float]:
        """Check if price is at Fib retracement level for BULLISH setup"""
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
        
        fib_level = self.params.get('fib_entry_level', 0.786)
        fib_price = swing_high - ((swing_high - swing_low) * fib_level)
        
        close = self.df['close'].iloc[bar]
        low = self.df['low'].iloc[bar]
        
        # Adaptive tolerance based on ATR
        base_tol = self.params.get('fib_tolerance', 0.10)
        atr = self.calculate_atr()
        if not pd.isna(atr.iloc[bar]):
            atr_tol = atr.iloc[bar] * 0.5
            tolerance = max(base_tol * (swing_high - swing_low), atr_tol)
        else:
            tolerance = base_tol * (swing_high - swing_low)
        
        at_fib = low <= fib_price + tolerance and close >= fib_price - tolerance
        
        return at_fib, fib_price, swing_high, swing_low
    
    def run_backtest(self) -> BacktestResult:
        self.signals = []
        self.calculate_zigzag()
        
        last_signal_bar = -self.params['signal_gap'] - 1
        
        for bar in range(self.params['zz_depth'] + 1, len(self.df) - 1):
            if bar - last_signal_bar <= self.params['signal_gap']:
                continue
            
            at_fib, fib_price, swing_high, swing_low = self.check_fib_entry(bar)
            if not at_fib:
                continue
            
            # Wave quality filter
            if self.params.get('use_wave_quality', True):
                quality = self.check_wave_quality(bar)
                if quality < self.params.get('min_wave_quality', 0.5):
                    continue
            
            # RSI filter
            if self.params['use_rsi_filter']:
                rsi = self.calculate_rsi().iloc[bar]
                if pd.isna(rsi) or rsi >= self.params['rsi_threshold']:
                    continue
            
            # Momentum filter (RSI rising)
            if self.params.get('use_momentum_filter', True):
                if not self.check_momentum_rising(bar):
                    continue
            
            # ATR filter
            if self.params.get('use_atr_filter', True):
                if not self.check_atr_ok(bar):
                    continue
            
            # Candle pattern filter
            if self.params.get('use_candle_filter', True):
                if not self.check_reversal_candle(bar):
                    continue
            
            # Trend filter
            if self.params['use_trend_filter']:
                ema = self.calculate_ema().iloc[bar]
                if pd.isna(ema) or self.df['close'].iloc[bar] <= ema:
                    continue
            
            # Volume filter
            if self.params['use_volume_filter']:
                avg_vol = self.df['volume'].rolling(20).mean().iloc[bar]
                if not pd.isna(avg_vol) and self.df['volume'].iloc[bar] < avg_vol * 0.5:
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
        open_trades = sum(1 for s in self.signals if s.result == 0)
        total = wins + losses
        win_rate = (wins / total * 100) if total > 0 else 0.0
        
        return BacktestResult(
            total=total,
            wins=wins,
            losses=losses,
            open_trades=open_trades,
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
