"""
Elliott + ICT Backtester v5 - CONFIRMATION ENTRY
Key change: Don't enter immediately at Fib touch.
Wait for CONFIRMATION - next bar must close above entry bar's high.
This filters out false breakdowns.
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

class ElliottICTBacktesterV5:
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
            # Confirmation settings
            'use_confirmation': True,
            'confirm_type': 'close_above_high',  # or 'bullish_candle' or 'higher_low'
            'max_confirm_bars': 3,  # Max bars to wait for confirmation
        }
        if params:
            self.params.update(params)
        
        self.signals = []
        self.zigzag_points = []
        self.pending_setups = []  # Store setups waiting for confirmation
        
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
    
    def check_fib_touch(self, bar: int) -> Tuple[bool, float, float, float]:
        """Check if price touched Fib level"""
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
        
        low = self.df['low'].iloc[bar]
        tolerance = (swing_high - swing_low) * self.params['fib_tolerance']
        
        touched = low <= fib_price + tolerance
        return touched, fib_price, swing_high, swing_low
    
    def check_confirmation(self, setup_bar: int, current_bar: int) -> bool:
        """Check if we have confirmation after the setup bar"""
        if not self.params.get('use_confirmation', True):
            return True
        
        confirm_type = self.params.get('confirm_type', 'close_above_high')
        setup_high = self.df['high'].iloc[setup_bar]
        setup_close = self.df['close'].iloc[setup_bar]
        setup_low = self.df['low'].iloc[setup_bar]
        
        curr_close = self.df['close'].iloc[current_bar]
        curr_low = self.df['low'].iloc[current_bar]
        curr_open = self.df['open'].iloc[current_bar]
        
        if confirm_type == 'close_above_high':
            # Current bar closes above setup bar's high
            return curr_close > setup_high
        
        elif confirm_type == 'bullish_candle':
            # Current bar is bullish and closes above setup close
            return curr_close > curr_open and curr_close > setup_close
        
        elif confirm_type == 'higher_low':
            # Current bar has higher low than setup bar
            return curr_low > setup_low and curr_close > curr_open
        
        return True
    
    def run_backtest(self) -> BacktestResult:
        self.signals = []
        self.pending_setups = []
        self.calculate_zigzag()
        
        last_signal_bar = -self.params['signal_gap'] - 1
        max_confirm = self.params.get('max_confirm_bars', 3)
        
        for bar in range(self.params['zz_depth'] + 1, len(self.df) - 1):
            # Check pending setups for confirmation
            new_pending = []
            for setup in self.pending_setups:
                setup_bar = setup['bar']
                bars_waited = bar - setup_bar
                
                if bars_waited > max_confirm:
                    # Too long, discard setup
                    continue
                
                if bar - last_signal_bar <= self.params['signal_gap']:
                    new_pending.append(setup)
                    continue
                
                if self.check_confirmation(setup_bar, bar):
                    # Confirmed! Create signal
                    entry = self.df['close'].iloc[bar]
                    swing_low = setup['swing_low']
                    swing_high = setup['swing_high']
                    sl_buffer = (swing_high - swing_low) * 0.02
                    sl = swing_low - sl_buffer
                    risk = entry - sl
                    
                    if risk > 0:
                        rr_ratio = self.params.get('rr_ratio', 1.0)
                        tp = entry + (risk * rr_ratio)
                        self.signals.append(Signal(bar=bar, entry=entry, tp=tp, sl=sl))
                        last_signal_bar = bar
                else:
                    new_pending.append(setup)
            
            self.pending_setups = new_pending
            
            # Check for new Fib touch
            if bar - last_signal_bar <= self.params['signal_gap']:
                continue
            
            touched, fib_price, swing_high, swing_low = self.check_fib_touch(bar)
            if touched:
                # Store as pending setup
                self.pending_setups.append({
                    'bar': bar,
                    'fib_price': fib_price,
                    'swing_high': swing_high,
                    'swing_low': swing_low,
                })
        
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
