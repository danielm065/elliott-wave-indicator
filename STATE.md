# State - Current Project Status

## Last Updated
2026-01-30 10:15

## Current Phase
**Phase 2: Optimization Per Timeframe**

## Active Work
- טווחי זמן שנותרו: 30m, 15m, 5m
- מעבר לעבודה עם תתי-סוכנים

## Completed Timeframes

### 1D ✅
- Result: 10/11 (91%)
- Params: ZZ=4, Fib=0.786, RSI<45, Tol=18%, RR=1.5

### 4H ✅
- Result: 14/18 (78%)
- Params: ZZ=2, Fib=0.786, RSI<40, Tol=5%, Gap=2, Trend=ON, Vol=ON

### 1H ✅
- Result: 11/20 (55%)
- Params: ZZ=3, Fib=0.85, RSI<30, Tol=5%, Gap=7, Vol=ON, RSI_F=ON
- Note: R:R=1:1 limits achievable WR

## Key Decisions
1. **R:R קבוע 1:1** - לא לשנות (בקשת הלקוח)
2. **Multiprocessing** - שימוש ב-8 ליבות להאצה
3. **80% threshold** - יעד WR מינימלי

## Blockers
- אין כרגע

## Insights Learned
- R:R נמוך יותר = WR גבוה יותר (קל יותר להגיע ל-TP)
- יותר מדי פילטרים = פחות סיגנלים בלי שיפור
- Multiprocessing חיוני לחיפוש גריד גדול

## Files Structure
```
backtest/
  backtester.py      # Main backtester
  test_parallel.py   # Parallel grid search (USE THIS!)
data/
  *.csv              # TradingView exports
src/
  *.pine             # Pine Script code
```

## How to Run Optimization
```python
# Edit test_parallel.py with desired grid
# Run:
python backtest/test_parallel.py
# Results printed to console
```
