"""
Elliott + ICT Backtester v2
Added: Bearish setups, FVG entries, multiple patterns
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
    direction: int  # 1=long, -1=short
    pattern: str    # 'fib', 'fvg', 'ob'
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
    long_wins: int = 0
    long_losses: int = 0
    short_wins: int = 0
    short_losses: int = 0

class ElliottICTBacktesterV2:
    def __init__(self, df: pd.DataFrame, params: dict = None):
        self.df = df.copy()
        self.df.columns = [str(c).lower() for c in self.df.columns]
        
        required = ['open', 'high', 'low', 'close', 'volume']
        for col in required:
            if col not in self.df.columns:
                raise ValueError(f"Missing required column: {col}")
        
        self.params = {
            'zz_depth': 3,
            'zz_dev': 0.2,
            'signal_gap': 5,
            'fib_entry_level': 0.786,
            'fib_tolerance': 0.10,
            'use_rsi_filter': True,
            'rsi_threshold': 50,
            'use_trend_filter': True,
            'ema_period': 200,
            'rr_ratio': 1.0,
            # New params
            'enable_longs': True,
            'enable_shorts': True,
            'enable_fvg': True,
            'fvg_min_size': 0.001,  # Minimum FVG size as % of price
        }
        if params:
            self.params.update(params)
        
        self.signals: List[Signal] = []
        self.zigzag_points = []
        self.fvg_zones = []
        
    def calculate_rsi(self, period=14) -> pd.Series:
        delta = self.df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    def calculate_ema(self, period=200) -> pd.Series:
        return self.df['close'].ewm(span=period, adjust=False).mean()
    
    def calculate_zigzag(self) -> List[Tuple[int, float, int]]:
        """Returns list of (bar_index, price, direction) where direction: 1=high, -1=low"""
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
    
    def detect_fvg_zones(self) -> List[dict]:
        """Detect Fair Value Gaps"""
        fvgs = []
        min_size = self.params['fvg_min_size']
        
        for i in range(2, len(self.df)):
            # Bullish FVG: Gap between bar[i-2] high and bar[i] low
            prev_high = self.df['high'].iloc[i-2]
            curr_low = self.df['low'].iloc[i]
            
            if curr_low > prev_high:
                size = (curr_low - prev_high) / self.df['close'].iloc[i]
                if size >= min_size:
                    fvgs.append({
                        'bar': i,
                        'type': 'bullish',
                        'top': curr_low,
                        'bottom': prev_high,
                        'mid': (curr_low + prev_high) / 2
                    })
            
            # Bearish FVG: Gap between bar[i-2] low and bar[i] high
            prev_low = self.df['low'].iloc[i-2]
            curr_high = self.df['high'].iloc[i]
            
            if curr_high < prev_low:
                size = (prev_low - curr_high) / self.df['close'].iloc[i]
                if size >= min_size:
                    fvgs.append({
                        'bar': i,
                        'type': 'bearish',
                        'top': prev_low,
                        'bottom': curr_high,
                        'mid': (prev_low + curr_high) / 2
                    })
        
        self.fvg_zones = fvgs
        return fvgs
    
    def check_bullish_fib_setup(self, bar: int) -> Tuple[bool, float, float, float]:
        """Check for bullish Fib retracement entry"""
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
        at_fib = low <= fib_price and close >= (fib_price - tolerance)
        
        return at_fib, fib_price, swing_high, swing_low
    
    def check_bearish_fib_setup(self, bar: int) -> Tuple[bool, float, float, float]:
        """Check for bearish Fib retracement entry (SHORT)"""
        points = [p for p in self.zigzag_points if p[0] <= bar]
        if len(points) < 2:
            return False, 0.0, 0.0, 0.0
        
        p0 = points[-1]
        p1 = points[-2]
        
        swing_high = 0.0
        swing_low = 0.0
        
        # Bearish: High -> Low (Wave 1 down)
        if p1[2] == 1 and p0[2] == -1:
            swing_high = p1[1]
            swing_low = p0[1]
        elif len(points) >= 3:
            p2 = points[-3]
            if p2[2] == 1 and p1[2] == -1 and p0[2] == 1:
                swing_high = p2[1]
                swing_low = p1[1]
        
        if swing_high <= swing_low:
            return False, 0.0, 0.0, 0.0
        
        fib_level = self.params['fib_entry_level']
        fib_price = swing_low + ((swing_high - swing_low) * fib_level)
        
        close = self.df['close'].iloc[bar]
        high = self.df['high'].iloc[bar]
        
        tolerance = (swing_high - swing_low) * self.params['fib_tolerance']
        at_fib = high >= fib_price and close <= (fib_price + tolerance)
        
        return at_fib, fib_price, swing_high, swing_low
    
    def check_fvg_entry(self, bar: int) -> Tuple[bool, int, float]:
        """Check if price is entering an unfilled FVG"""
        close = self.df['close'].iloc[bar]
        low = self.df['low'].iloc[bar]
        high = self.df['high'].iloc[bar]
        
        for fvg in self.fvg_zones:
            if fvg['bar'] >= bar - 20 and fvg['bar'] < bar:  # Recent FVG
                if fvg['type'] == 'bullish':
                    if low <= fvg['mid'] <= high:
                        return True, 1, fvg['mid']  # Long entry
                elif fvg['type'] == 'bearish':
                    if low <= fvg['mid'] <= high:
                        return True, -1, fvg['mid']  # Short entry
        
        return False, 0, 0.0
    
    def run_backtest(self) -> BacktestResult:
        """Run the backtest with multiple patterns"""
        self.signals = []
        self.calculate_zigzag()
        self.detect_fvg_zones()
        
        rsi = self.calculate_rsi() if self.params['use_rsi_filter'] else None
        ema = self.calculate_ema(self.params['ema_period']) if self.params['use_trend_filter'] else None
        
        last_signal_bar = -self.params['signal_gap'] - 1
        
        for bar in range(self.params['zz_depth'] + 2, len(self.df) - 1):
            if bar - last_signal_bar <= self.params['signal_gap']:
                continue
            
            close = self.df['close'].iloc[bar]
            
            # === LONG SIGNALS ===
            if self.params['enable_longs']:
                # Pattern 1: Bullish Fib retracement
                at_fib, fib_price, swing_high, swing_low = self.check_bullish_fib_setup(bar)
                
                if at_fib:
                    # Filters
                    rsi_ok = not self.params['use_rsi_filter'] or (rsi is not None and rsi.iloc[bar] < self.params['rsi_threshold'])
                    trend_ok = not self.params['use_trend_filter'] or (ema is not None and close > ema.iloc[bar])
                    bullish_candle = close > self.df['open'].iloc[bar]
                    
                    if rsi_ok and trend_ok and bullish_candle:
                        entry = fib_price
                        sl_buffer = (swing_high - swing_low) * 0.02
                        sl = swing_low - sl_buffer
                        risk = entry - sl
                        tp = entry + (risk * self.params['rr_ratio'])
                        
                        self.signals.append(Signal(bar=bar, entry=entry, tp=tp, sl=sl, direction=1, pattern='fib'))
                        last_signal_bar = bar
                        continue
                
                # Pattern 2: Bullish FVG entry
                if self.params['enable_fvg']:
                    fvg_hit, fvg_dir, fvg_price = self.check_fvg_entry(bar)
                    if fvg_hit and fvg_dir == 1:
                        rsi_ok = not self.params['use_rsi_filter'] or (rsi is not None and rsi.iloc[bar] < self.params['rsi_threshold'])
                        trend_ok = not self.params['use_trend_filter'] or (ema is not None and close > ema.iloc[bar])
                        
                        if rsi_ok and trend_ok:
                            entry = fvg_price
                            sl = self.df['low'].iloc[bar] * 0.99
                            risk = entry - sl
                            tp = entry + (risk * self.params['rr_ratio'])
                            
                            self.signals.append(Signal(bar=bar, entry=entry, tp=tp, sl=sl, direction=1, pattern='fvg'))
                            last_signal_bar = bar
                            continue
            
            # === SHORT SIGNALS ===
            if self.params['enable_shorts']:
                # Pattern 1: Bearish Fib retracement
                at_fib, fib_price, swing_high, swing_low = self.check_bearish_fib_setup(bar)
                
                if at_fib:
                    # Filters (inverted for shorts)
                    rsi_ok = not self.params['use_rsi_filter'] or (rsi is not None and rsi.iloc[bar] > (100 - self.params['rsi_threshold']))
                    trend_ok = not self.params['use_trend_filter'] or (ema is not None and close < ema.iloc[bar])
                    bearish_candle = close < self.df['open'].iloc[bar]
                    
                    if rsi_ok and trend_ok and bearish_candle:
                        entry = fib_price
                        sl_buffer = (swing_high - swing_low) * 0.02
                        sl = swing_high + sl_buffer
                        risk = sl - entry
                        tp = entry - (risk * self.params['rr_ratio'])
                        
                        self.signals.append(Signal(bar=bar, entry=entry, tp=tp, sl=sl, direction=-1, pattern='fib'))
                        last_signal_bar = bar
                        continue
                
                # Pattern 2: Bearish FVG entry
                if self.params['enable_fvg']:
                    fvg_hit, fvg_dir, fvg_price = self.check_fvg_entry(bar)
                    if fvg_hit and fvg_dir == -1:
                        rsi_ok = not self.params['use_rsi_filter'] or (rsi is not None and rsi.iloc[bar] > (100 - self.params['rsi_threshold']))
                        trend_ok = not self.params['use_trend_filter'] or (ema is not None and close < ema.iloc[bar])
                        
                        if rsi_ok and trend_ok:
                            entry = fvg_price
                            sl = self.df['high'].iloc[bar] * 1.01
                            risk = sl - entry
                            tp = entry - (risk * self.params['rr_ratio'])
                            
                            self.signals.append(Signal(bar=bar, entry=entry, tp=tp, sl=sl, direction=-1, pattern='fvg'))
                            last_signal_bar = bar
                            continue
        
        # Process signals
        for signal in self.signals:
            signal.filled = True
            signal.filled_bar = signal.bar
            
            for bar in range(signal.bar + 1, len(self.df)):
                low = self.df['low'].iloc[bar]
                high = self.df['high'].iloc[bar]
                
                if signal.direction == 1:  # Long
                    if low <= signal.sl:
                        signal.result = -1
                        break
                    if high >= signal.tp:
                        signal.result = 1
                        break
                else:  # Short
                    if high >= signal.sl:
                        signal.result = -1
                        break
                    if low <= signal.tp:
                        signal.result = 1
                        break
        
        # Calculate results
        wins = sum(1 for s in self.signals if s.result == 1)
        losses = sum(1 for s in self.signals if s.result == -1)
        open_trades = sum(1 for s in self.signals if s.result == 0)
        total = len(self.signals)
        win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0
        
        long_wins = sum(1 for s in self.signals if s.result == 1 and s.direction == 1)
        long_losses = sum(1 for s in self.signals if s.result == -1 and s.direction == 1)
        short_wins = sum(1 for s in self.signals if s.result == 1 and s.direction == -1)
        short_losses = sum(1 for s in self.signals if s.result == -1 and s.direction == -1)
        
        return BacktestResult(
            total=total,
            wins=wins,
            losses=losses,
            open_trades=open_trades,
            win_rate=win_rate,
            signals=self.signals,
            long_wins=long_wins,
            long_losses=long_losses,
            short_wins=short_wins,
            short_losses=short_losses
        )


def load_data(path: str) -> pd.DataFrame:
    """Load CSV data"""
    with open(path, 'r') as f:
        header = f.readline().lower()
    
    if 'time,open' in header:
        df = pd.read_csv(path)
        if 'time' in df.columns:
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('time', inplace=True)
        df.columns = [c.lower() for c in df.columns]
        if 'volume' not in df.columns:
            df['volume'] = 1
        return df[['open', 'high', 'low', 'close', 'volume']]
    else:
        df = pd.read_csv(path, index_col=0, parse_dates=True)
        df.columns = [c.lower() for c in df.columns]
        if 'volume' not in df.columns:
            df['volume'] = 1
        return df
