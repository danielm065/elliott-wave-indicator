"""
Elliott + ICT Backtester v19
Python implementation for testing and optimization
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import List, Tuple, Optional
import json
import os

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

class ElliottICTBacktester:
    def __init__(self, df: pd.DataFrame, params: dict = None):
        """
        df: DataFrame with columns: Open, High, Low, Close, Volume
        params: dict with backtesting parameters
        """
        self.df = df.copy()
        # Normalize column names
        self.df.columns = [str(c).lower() for c in self.df.columns]
        # Make sure we have required columns
        required = ['open', 'high', 'low', 'close', 'volume']
        for col in required:
            if col not in self.df.columns:
                raise ValueError(f"Missing required column: {col}")
        
        # Default parameters (OPTIMIZED v21)
        self.params = {
            'sl_pct': 6.0,
            'tp_fib': 1.0,  # 100% of Wave 1 extension
            'zz_depth': 5,      # OPTIMIZED
            'zz_dev': 0.2,      # CRITICAL: 0.2 works best
            'signal_gap': 5,    # OPTIMIZED: reduced for more signals
            'fib_entry_level': 0.70,  # OPTIMIZED: 0.70 for higher TFs
            'fib_tolerance': 0.02,
            'wave_retrace_min': 0.5,
            'wave_retrace_max': 0.786,
            'use_rsi_filter': True,
            'rsi_threshold': 50,
            'use_volume_filter': True,
            'use_trend_filter': True,   # OPTIMIZED: enabled
            'ema_period': 200,
            'require_smt_or_fvg': False,
            'rr_ratio': 2.0,    # 1:2 R:R
        }
        if params:
            self.params.update(params)
        
        self.signals: List[Signal] = []
        self.zigzag_points = []
        
    def calculate_rsi(self, period=14) -> pd.Series:
        delta = self.df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
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
            # Check for pivot high
            is_ph = True
            for j in range(1, depth + 1):
                if highs[i] <= highs[i - j] or highs[i] <= highs[i + j]:
                    is_ph = False
                    break
            
            # Check for pivot low
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
    
    def check_wave2_setup(self, bar: int) -> Tuple[bool, float]:
        """Check if we have a valid Wave 2 setup at given bar"""
        points = [p for p in self.zigzag_points if p[0] <= bar]
        if len(points) < 3:
            return False, 0.0
        
        p0 = points[-1]  # Most recent
        p1 = points[-2]
        p2 = points[-3]
        
        # Pattern: Low (p2) -> High (p1) -> Low (p0) for bullish
        if p2[2] == -1 and p1[2] == 1 and p0[2] == -1:
            wave1_size = p1[1] - p2[1]
            if wave1_size > 0:
                retrace = (p1[1] - p0[1]) / wave1_size
                if self.params['wave_retrace_min'] <= retrace <= self.params['wave_retrace_max']:
                    return True, wave1_size
        
        return False, 0.0
    
    def check_fib_entry(self, bar: int) -> Tuple[bool, float, float, float]:
        """Check if price is at 0.79 Fib retracement level for BULLISH setup"""
        points = [p for p in self.zigzag_points if p[0] <= bar]
        if len(points) < 2:
            return False, 0.0, 0.0, 0.0
        
        p0 = points[-1]  # Most recent: (bar, price, direction)
        p1 = points[-2]
        
        swing_high = 0.0
        swing_low = 0.0
        
        # Bullish setup: Low → High (Wave 1 up)
        if p1[2] == -1 and p0[2] == 1:  # p1=Low, p0=High
            swing_low = p1[1]
            swing_high = p0[1]
        # Or Low → High → Low (Wave 2 in progress)
        elif len(points) >= 3:
            p2 = points[-3]
            if p2[2] == -1 and p1[2] == 1 and p0[2] == -1:
                swing_low = p2[1]
                swing_high = p1[1]
        
        if swing_high <= swing_low:
            return False, 0.0, 0.0, 0.0
        
        # 0.79 Fib = price at 79% retracement from high
        fib_level = self.params.get('fib_entry_level', 0.79)
        fib_price = swing_high - ((swing_high - swing_low) * fib_level)
        
        close = self.df['close'].iloc[bar]
        low = self.df['low'].iloc[bar]
        
        # Check if price touched the fib level (with tolerance)
        tolerance = (swing_high - swing_low) * self.params.get('fib_tolerance', 0.02)
        at_fib = low <= fib_price and close >= (fib_price - tolerance)
        
        return at_fib, fib_price, swing_high, swing_low
    
    def calculate_strength_score(self, bar: int, wave2: bool, in_discount: bool, in_ote: bool) -> int:
        """Calculate confluence strength score"""
        score = 0
        
        close = self.df['close'].iloc[bar]
        
        # Discount zone
        if in_discount:
            score += 2
        
        # OTE zone
        if in_ote:
            score += 3
        
        # Wave 2 setup
        if wave2:
            score += 2
        
        # Trend filter (EMA 200)
        if self.params['use_trend_filter']:
            ema = self.df['close'].rolling(self.params['ema_period']).mean().iloc[bar]
            if not pd.isna(ema) and close > ema:
                score += 1
        
        # RSI filter
        if self.params['use_rsi_filter']:
            rsi = self.calculate_rsi().iloc[bar]
            if not pd.isna(rsi) and rsi < self.params['rsi_threshold']:
                score += 1
        
        # Volume filter
        if self.params['use_volume_filter']:
            avg_vol = self.df['volume'].rolling(20).mean().iloc[bar]
            if not pd.isna(avg_vol) and self.df['volume'].iloc[bar] > avg_vol * 0.8:
                score += 1
        
        # Bullish candle
        if close > self.df['open'].iloc[bar]:
            score += 1
        
        return score
    
    def run_backtest(self) -> BacktestResult:
        """Run the backtest"""
        self.signals = []
        self.calculate_zigzag()
        
        last_signal_bar = -self.params['signal_gap'] - 1
        
        # Generate signals
        for bar in range(self.params['zz_depth'] + 1, len(self.df) - 1):
            # Check gap between signals
            if bar - last_signal_bar <= self.params['signal_gap']:
                continue
            
            # KEY: Check if price is at 0.79 Fib level
            at_fib, fib_price, swing_high, swing_low = self.check_fib_entry(bar)
            
            if not at_fib:
                continue
            
            # Check Wave 2 setup (for TP calculation)
            wave2, wave1_size = self.check_wave2_setup(bar)
            
            # TODO: Add SMT and FVG checks for full confirmation
            # For now, we just check bullish candle + trend
            
            # Check bullish candle
            if self.df['close'].iloc[bar] <= self.df['open'].iloc[bar]:
                continue
            
            # Check trend filter
            if self.params['use_trend_filter']:
                ema = self.df['close'].rolling(self.params['ema_period']).mean().iloc[bar]
                if pd.isna(ema) or self.df['close'].iloc[bar] <= ema:
                    continue
            
            # Signal fires! Entry at the 0.79 Fib price
            entry = fib_price
            
            # SL just below swing low (logical stop)
            sl_buffer = (swing_high - swing_low) * 0.02
            sl = swing_low - sl_buffer
            
            # Risk = Entry - SL
            risk = entry - sl
            
            # TP = Entry + 2*Risk (1:2 R:R)
            rr_ratio = self.params.get('rr_ratio', 2.0)
            tp = entry + (risk * rr_ratio)
            
            self.signals.append(Signal(bar=bar, entry=entry, tp=tp, sl=sl))
            last_signal_bar = bar
        
        # Process signals - IMMEDIATE ENTRY (market order at signal close)
        # Then check TP/SL from the NEXT bar
        for signal in self.signals:
            # Entry is immediate at signal bar close
            signal.filled = True
            signal.filled_bar = signal.bar
            
            # Check TP/SL from the bar AFTER entry
            for bar in range(signal.bar + 1, len(self.df)):
                low = self.df['low'].iloc[bar]
                high = self.df['high'].iloc[bar]
                
                # Check SL first (worst case)
                if low <= signal.sl:
                    signal.result = -1
                    break
                
                # Check TP
                if high >= signal.tp:
                    signal.result = 1
                    break
        
        # Calculate results
        wins = sum(1 for s in self.signals if s.result == 1)
        losses = sum(1 for s in self.signals if s.result == -1)
        open_trades = sum(1 for s in self.signals if s.result == 0)
        total = len(self.signals)
        win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0
        
        return BacktestResult(
            total=total,
            wins=wins,
            losses=losses,
            open_trades=open_trades,
            win_rate=win_rate,
            signals=self.signals
        )


def optimize_parameters(df: pd.DataFrame, param_ranges: dict) -> dict:
    """Grid search for optimal parameters"""
    best_result = None
    best_params = None
    best_score = -1
    
    # Generate all combinations
    from itertools import product
    
    keys = list(param_ranges.keys())
    values = [param_ranges[k] for k in keys]
    
    for combo in product(*values):
        params = dict(zip(keys, combo))
        bt = ElliottICTBacktester(df, params)
        result = bt.run_backtest()
        
        # Score: prioritize win rate but also need enough signals
        if result.wins + result.losses >= 5:  # Minimum trades
            score = result.win_rate * (1 + min(result.total, 30) / 100)
            if score > best_score:
                best_score = score
                best_result = result
                best_params = params.copy()
    
    return {
        'params': best_params,
        'result': best_result,
        'score': best_score
    }


def load_tradingview_csv(path: str) -> pd.DataFrame:
    """Load CSV exported from TradingView"""
    df = pd.read_csv(path)
    
    # TradingView format: time (unix), open, high, low, close, ...
    if 'time' in df.columns:
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df.set_index('time', inplace=True)
    
    # Keep only OHLCV columns
    cols = ['open', 'high', 'low', 'close']
    if 'volume' in df.columns:
        cols.append('volume')
    else:
        df['volume'] = 1  # Placeholder if no volume
        cols.append('volume')
    
    return df[cols]


def load_yfinance_csv(path: str) -> pd.DataFrame:
    """Load CSV from yfinance"""
    df = pd.read_csv(path, skiprows=2, index_col=0, parse_dates=True)
    df.columns = ['close', 'high', 'low', 'open', 'volume']
    return df[['open', 'high', 'low', 'close', 'volume']]


def load_data(path: str) -> pd.DataFrame:
    """Auto-detect and load CSV format"""
    # Peek at first line
    with open(path, 'r') as f:
        header = f.readline().lower()
    
    if 'time,open' in header:
        return load_tradingview_csv(path)
    elif 'price,close' in header:
        return load_yfinance_csv(path)
    else:
        # Generic
        df = pd.read_csv(path, index_col=0, parse_dates=True)
        df.columns = [c.lower() for c in df.columns]
        return df


if __name__ == '__main__':
    import sys
    
    # Default or command line arg
    data_path = sys.argv[1] if len(sys.argv) > 1 else r'C:\Users\danie\projects\elliott-wave-indicator\data\MNQ_1D.csv'
    
    df = load_data(data_path)
    
    print(f"Loaded {len(df)} bars of NQ Daily data")
    print(f"Date range: {df.index[0]} to {df.index[-1]}")
    print()
    
    # Run backtest with default 1D parameters
    bt = ElliottICTBacktester(df, {
        'sl_pct': 6.0,
        'tp_fib': 0.382,
        'zz_depth': 8,
        'signal_gap': 3,
        'min_strength': 7,
    })
    
    result = bt.run_backtest()
    
    print("=" * 50)
    print("BACKTEST RESULTS - NQ Daily")
    print("=" * 50)
    print(f"Total Signals: {result.total}")
    print(f"Wins: {result.wins}")
    print(f"Losses: {result.losses}")
    print(f"Open: {result.open_trades}")
    print(f"Win Rate: {result.win_rate:.1f}%")
    print()
    
    # Show last 5 signals
    print("Last 5 signals:")
    for s in result.signals[-5:]:
        date = df.index[s.bar]
        status = "WIN" if s.result == 1 else "LOSS" if s.result == -1 else "OPEN"
        filled = "FILLED" if s.filled else "NOT FILLED"
        print(f"  {date.date()} | Entry: {s.entry:.2f} | TP: {s.tp:.2f} | SL: {s.sl:.2f} | {filled} | {status}")
