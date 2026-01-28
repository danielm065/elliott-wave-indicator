# Elliott Wave Indicator

🌊 Pine Script indicator for TradingView that identifies Elliott Wave buy signals with built-in backtesting.

## Features

- **Automatic Wave Detection** - Identifies potential Wave 2 and Wave 4 completions
- **Buy Signals** - Generates entry signals for Wave 3 and Wave 5 starts
- **Fibonacci Targets** - Calculates price targets based on Elliott Wave theory
- **Built-in Backtesting** - Tracks historical performance automatically
- **Statistics Dashboard** - Shows win rate, total trades, and success metrics per timeframe

## Installation

1. Open TradingView
2. Go to Pine Editor
3. Copy the code from `src/elliott-wave-indicator.pine`
4. Click "Add to Chart"

## Settings

### Zigzag Settings
- **Depth** - Higher values = smoother waves, fewer signals
- **Deviation %** - Minimum price change to form new pivot

### Elliott Wave Settings
- **Wave 2 Retracement** - Valid range for Wave 2 (default: 38.2% - 78.6%)
- **Wave 4 Retracement** - Valid range for Wave 4 (default: 23.6% - 50%)

### Target Settings
- **Target Extension** - Fibonacci extension for profit target (default: 1.618)
- **Stop Loss %** - Stop loss percentage below entry

## Elliott Wave Rules Applied

Based on the classic Elliott Wave Principle:

1. **Wave 2** never retraces more than 100% of Wave 1
2. **Wave 3** is never the shortest wave
3. **Wave 4** does not enter Wave 1 territory
4. **Wave 2** typically retraces 50-61.8% of Wave 1
5. **Wave 4** typically retraces 38.2% of Wave 3

## Signal Types

| Signal | Description | Target |
|--------|-------------|--------|
| BUY W3 | Wave 2 complete, entering Wave 3 | 1.618 × Wave 1 |
| BUY W5 | Wave 4 complete, entering Wave 5 | Wave 1 length |

## Statistics Table

The indicator displays:
- Total signals generated
- Wins (target hit)
- Losses (stop hit)
- Open trades
- **Win Rate %** (color coded: 🟢 >60%, 🟡 40-60%, 🔴 <40%)

## Roadmap

- [ ] Short signals (bearish waves)
- [ ] Multi-timeframe analysis
- [ ] Wave degree detection
- [ ] Alternation rule validation
- [ ] Alert improvements

## License

Mozilla Public License 2.0

## Author

© danielm065
