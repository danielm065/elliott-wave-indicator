"""
Elliott + ICT Backtester v6 - MULTI-TIMEFRAME + CONFLUENCE
Key improvements:
1. Higher timeframe trend confirmation
2. Fair Value Gap (FVG) detection
3. Order Block (OB) detection
4. Confluence scoring - multiple factors must align
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
    confluence_score: int = 0
    filled: bool = False
    result: int = 0

@dataclass
class BacktestResult:
    total: int
    wins: int
    losses: int
    win_rate: float
    signals: List[Signal]

class ElliottICTBacktesterV6:
    def __init__(self, df: pd.DataFrame, df_htf: pd.DataFrame = None, params: dict = None):
        """
        df: Current timeframe data
        df_htf: Higher timeframe data (4x current, e.g., 1H -> 4H)
        """
        self.df = df.copy()
        self.df.columns = [str(c).lower() for c in self.df.columns]
        
        self.df_htf = None
        if df_htf is not None:
            self.df_htf = df_htf.copy()
            self.df_htf.columns = [str(c).lower() for c in self.df_htf.columns]
        
        self.params = {
            'zz_depth': 3,
            'zz_dev': 0.2,
            'signal_gap': 5,
            'fib_entry_level': 0.786,
            'fib_tolerance': 0.10,
            'rr_ratio': 1.0,
            'ema_period': 50,
            # MTF settings
            'use_htf_trend': True,
            'htf_ema_period': 50,
            # FVG settings
            'use_fvg': True,
            'fvg_lookback': 20,
            # Order Block settings
            'use_ob': True,
            'ob_lookback': 20,
            # Confluence settings
            'min_confluence': 2,  # Minimum factors required
        }
        if params:
            self.params.update(params)
        
        self.signals = []
        self.zigzag_points = []
        self.fvgs = []  # Fair Value Gaps
        self.order_blocks = []  # Order Blocks
        
    def calculate_htf_trend(self, bar: int) -> int:
        """
        Returns: 1 for bullish, -1 for bearish, 0 for neutral
        """
        if self.df_htf is None or not self.params.get('use_htf_trend', True):
            return 1  # Default to bullish if no HTF data
        
        # Map current bar to HTF bar (approximately)
        htf_bars = len(self.df_htf)
        current_bars = len(self.df)
        htf_bar = int(bar * htf_bars / current_bars)
        htf_bar = min(htf_bar, htf_bars - 1)
        
        if htf_bar < self.params['htf_ema_period']:
            return 0
        
        # Calculate HTF EMA
        ema = self.df_htf['close'].ewm(span=self.params['htf_ema_period']).mean()
        price = self.df_htf['close'].iloc[htf_bar]
        ema_val = ema.iloc[htf_bar]
        
        if price > ema_val * 1.001:  # 0.1% above EMA
            return 1
        elif price < ema_val * 0.999:  # 0.1% below EMA
            return -1
        return 0
    
    def detect_fvg(self, bar: int) -> Optional[dict]:
        """
        Detect bullish Fair Value Gap (3-candle pattern)
        FVG exists when: candle[i-2].high < candle[i].low (gap between)
        """
        if not self.params.get('use_fvg', True):
            return None
        
        lookback = self.params.get('fvg_lookback', 20)
        
        for i in range(max(bar - lookback, 2), bar):
            # Bullish FVG: Low of current > High of 2 bars ago
            if self.df['low'].iloc[i] > self.df['high'].iloc[i-2]:
                fvg_top = self.df['low'].iloc[i]
                fvg_bottom = self.df['high'].iloc[i-2]
                current_price = self.df['close'].iloc[bar]
                
                # Check if price is in FVG zone
                if fvg_bottom <= current_price <= fvg_top:
                    return {'top': fvg_top, 'bottom': fvg_bottom, 'bar': i}
        
        return None
    
    def detect_order_block(self, bar: int) -> Optional[dict]:
        """
        Detect bullish Order Block
        OB: Last bearish candle before a strong bullish move
        """
        if not self.params.get('use_ob', True):
            return None
        
        lookback = self.params.get('ob_lookback', 20)
        
        for i in range(max(bar - lookback, 3), bar - 1):
            # Look for bearish candle followed by bullish candles
            c_open = self.df['open'].iloc[i]
            c_close = self.df['close'].iloc[i]
            
            if c_close < c_open:  # Bearish candle
                # Check if followed by bullish move
                next_high = self.df['high'].iloc[i+1:i+4].max()
                if next_high > self.df['high'].iloc[i] * 1.005:  # 0.5% move up
                    ob_top = self.df['high'].iloc[i]
                    ob_bottom = self.df['low'].iloc[i]
                    current_price = self.df['close'].iloc[bar]
                    
                    # Check if price is in OB zone
                    if ob_bottom <= current_price <= ob_top:
                        return {'top': ob_top, 'bottom': ob_bottom, 'bar': i}
        
        return None
    
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
    
    def calculate_confluence(self, bar: int, fib_price: float, swing_high: float, swing_low: float) -> int:
        """Calculate confluence score (0-5)"""
        score = 0
        
        # 1. Fib level hit (+1)
        score += 1
        
        # 2. HTF trend bullish (+1)
        htf_trend = self.calculate_htf_trend(bar)
        if htf_trend == 1:
            score += 1
        
        # 3. FVG zone (+1)
        fvg = self.detect_fvg(bar)
        if fvg:
            score += 1
        
        # 4. Order Block zone (+1)
        ob = self.detect_order_block(bar)
        if ob:
            score += 1
        
        # 5. RSI oversold (+1)
        delta = self.df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        if bar < len(rsi) and not pd.isna(rsi.iloc[bar]) and rsi.iloc[bar] < 35:
            score += 1
        
        return score
    
    def run_backtest(self) -> BacktestResult:
        self.signals = []
        self.calculate_zigzag()
        
        last_signal_bar = -self.params['signal_gap'] - 1
        min_confluence = self.params.get('min_confluence', 2)
        
        for bar in range(max(20, self.params['zz_depth'] + 1), len(self.df) - 1):
            if bar - last_signal_bar <= self.params['signal_gap']:
                continue
            
            at_fib, fib_price, swing_high, swing_low = self.check_fib_entry(bar)
            if not at_fib:
                continue
            
            # Calculate confluence score
            confluence = self.calculate_confluence(bar, fib_price, swing_high, swing_low)
            
            # Only enter if minimum confluence met
            if confluence < min_confluence:
                continue
            
            # Create signal
            entry = self.df['close'].iloc[bar]
            sl_buffer = (swing_high - swing_low) * 0.02
            sl = swing_low - sl_buffer
            risk = entry - sl
            
            if risk <= 0:
                continue
            
            rr_ratio = self.params.get('rr_ratio', 1.0)
            tp = entry + (risk * rr_ratio)
            
            self.signals.append(Signal(bar=bar, entry=entry, tp=tp, sl=sl, confluence_score=confluence))
            last_signal_bar = bar
        
        # Process signals
        for signal in self.signals:
            signal.filled = True
            
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
