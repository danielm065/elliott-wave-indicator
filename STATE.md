# State - Current Project Status

## Last Updated
2026-01-31 10:15

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

### 30m ✅
- Result: 13/20 (65%)
- Params: ZZ=3, Fib=0.85, Tol=3%, Gap=10, RSI<25, Trend=OFF, Vol=ON
- Passing: ADAUSDT, AMD, ASTS, BA, BTCUSDT, CRWV, ETHUSD, HIMS, IBKR, KRNT, MU, PLTR, TTWO

## Pending Timeframes
- 15m
- 5m

## Lessons Learned

### Optimization Strategy
1. **Use multiprocessing** - 8 cores, chunksize=50 for speed
2. **Wide grid first** - Cover all parameter combinations
3. **Track incrementally** - Print NEW BEST as found
4. **~24K combos = ~1 hour** - Plan accordingly
5. **Write status to JSON** - Enable external monitoring
6. **Background process** - Use Start-Process for long runs

### Parameter Patterns Emerging
- **ZZ=3** works well for 1H and 30m
- **Fib=0.85** consistent across shorter timeframes
- **RSI<25** - stricter for shorter TFs
- **Trend=OFF** better for 1H/30m
- **Vol=ON** generally helps
- **Tolerance 3%** - tight but works

### What Doesn't Work
1. Too many confluence filters = no signals
2. MTF analysis didn't improve results
3. R:R=1.0 limits achievable WR (~65% realistic for intraday)
4. R:R=1.5+ needed for 80%+ WR (only works on daily)

## Next Steps
1. Run 15m optimization
2. Then 5m
3. Compile final results

## Files Structure
```
backtest/
  backtester.py               # Main backtester
  optimize_30m_monitored.py   # 30m with JSON status
data/
  *.csv                       # TradingView exports
optimization_status.json      # Current run status
RESULTS.md                    # Summary of all results
```
