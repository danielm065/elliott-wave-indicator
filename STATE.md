# State - Current Project Status

## Last Updated
2026-01-30 23:10

## Current Phase
**Phase 2: Optimization Per Timeframe**

## Completed Timeframes

### 1D ✅
- Result: 10/11 (91%)
- Params: ZZ=4, Fib=0.786, RSI<45, Tol=18%, R:R=1.5

### 4H ✅
- Result: 14/18 (78%)
- Params: ZZ=2, Fib=0.786, RSI<40, Tol=5%, Gap=2, Trend=ON, Vol=ON

### 1H ✅
- Result: 13/20 (65%)
- Params: ZZ=3, Fib=0.85, Tol=3%, RSI<25, Trend=OFF, Vol=ON
- Passing: AMD, ASTS, BTCUSDT, CRWV, GOOG, HIMS, IBKR, INTC, MNQ, MU, PLTR, SOLUSD, USDILS

## Pending Timeframes
- 30m
- 15m
- 5m

## Lessons Learned

### Optimization Strategy
1. **Use multiprocessing** - 8 cores, chunksize=50 for speed
2. **Wide grid first** - Cover all parameter combinations
3. **Track incrementally** - Print NEW BEST as found
4. **~40K combos = ~1 hour** - Plan accordingly

### Parameter Insights
1. **Fib level 0.786-0.85** - Sweet spot for entries
2. **RSI < 25-40** - Catches reversals
3. **Volume filter = ON** - Generally helps
4. **Trend filter** - Varies by timeframe
5. **Tolerance 3-5%** - Balance precision vs. signal count

### What Doesn't Work
1. Too many confluence filters = no signals
2. MTF analysis didn't improve results
3. R:R=1.0 limits achievable WR (~65% realistic)
4. R:R=1.5+ needed for 80%+ WR

## Next Steps
1. Run 30m optimization with same approach
2. Then 15m, then 5m
3. Compile final results

## Files Structure
```
backtest/
  backtester.py           # Main backtester
  optimize_1h_deep.py     # Deep optimization (template)
  test_parallel.py        # Parallel grid search
data/
  *.csv                   # TradingView exports
RESULTS.md                # Summary of all results
```
