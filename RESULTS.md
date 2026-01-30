# Elliott Wave Indicator - Optimization Results

## Summary

| Timeframe | Passing | Total | Rate | Status |
|-----------|---------|-------|------|--------|
| 1D | 10 | 11 | 91% | ✅ |
| 4H | 14 | 18 | 78% | ✅ |
| 1H | 13 | 20 | 65% | ✅ |
| 30m | - | - | - | Pending |
| 15m | - | - | - | Pending |
| 5m | - | - | - | Pending |

## Best Parameters by Timeframe

### 1D (Daily)
```
ZZ=4, Fib=0.786, RSI<45, Tol=18%, R:R=1.5
```
- Result: 10/11 (91%)
- Note: Higher R:R (1.5) significantly improved results

### 4H (4-Hour)
```
ZZ=2, Fib=0.786, RSI<40, Tol=5%, Gap=2, Trend=ON, Vol=ON
```
- Result: 14/18 (78%)

### 1H (Hourly)
```
ZZ=3, Fib=0.85, Tol=3%, Gap=?, RSI<25, Trend=OFF, Vol=ON, R:R=1.0
```
- Result: 13/20 (65%)
- Passing: AMD, ASTS, BTCUSDT, CRWV, GOOG, HIMS, IBKR, INTC, MNQ, MU, PLTR, SOLUSD, USDILS
- Failing: ADAUSDT (78%), BA (71%), ETHUSD (50%), KRNT (50%), OSCR (75%), RKLB (75%), TTWO (64%)

## Key Insights

### What Works
1. **Higher Fib levels (0.786-0.85)** - Better entry points
2. **Low RSI threshold (<25-40)** - Catches oversold conditions
3. **Volume filter ON** - Confirms momentum
4. **Trend filter varies** - ON for 4H, OFF for 1H

### What Doesn't Work
1. **Too many filters** - Reduces signals without improving WR
2. **Tight tolerance** - Misses good entries
3. **High R:R with R:R=1.0** - Hard to achieve 80%+ WR

### Optimization Strategy
1. Start with wide parameter grid
2. Use multiprocessing for speed
3. Track best result incrementally
4. ~40K combinations takes ~1 hour

## Files

- `backtest/backtester.py` - Main backtester
- `backtest/optimize_1h_deep.py` - Deep optimization script
- `backtest/test_parallel.py` - Parallel grid search
- `data/*.csv` - TradingView price data
