"""
Base strategy class for backtesting
"""
import pandas as pd
from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class Signal:
    bar: int
    entry: float
    tp: float
    sl: float
    direction: int = 1  # 1=long, -1=short
    result: int = 0  # 0=open, 1=win, -1=loss

@dataclass
class BacktestResult:
    total: int
    wins: int
    losses: int
    open_trades: int
    win_rate: float
    signals: List[Signal]

class BaseStrategy:
    """Base class for all strategies"""
    
    def __init__(self, df: pd.DataFrame, params: dict):
        self.df = df
        self.params = params
        self.signals = []
    
    def generate_signals(self) -> List[Signal]:
        """Override in subclass"""
        raise NotImplementedError
    
    def run_backtest(self) -> BacktestResult:
        """Run backtest with generated signals"""
        self.signals = self.generate_signals()
        
        # Process signals
        for signal in self.signals:
            signal.result = 0  # Reset
            
            # Check TP/SL from next bar
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
