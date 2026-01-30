# Task: Optimize [TIMEFRAME] Parameters

## Mission
מצא את הפרמטרים האופטימליים עבור טווח זמן [TIMEFRAME] שמשיגים:
- **80%+ Win Rate** על כל נכס אפשרי
- **כיסוי מקסימלי** - כמה שיותר נכסים עוברים

## Constraints (לא לשנות!)
- **R:R = 1.0** (יחס 1:1)
- **Long only**

## Input Files
- **Backtester:** `C:\Users\danie\projects\elliott-wave-indicator\backtest\backtester.py`
- **Parallel Test:** `C:\Users\danie\projects\elliott-wave-indicator\backtest\test_parallel.py`
- **Data:** `C:\Users\danie\projects\elliott-wave-indicator\data\*[TIMEFRAME]*.csv`

## Process
1. **Copy** `test_parallel.py` to `test_[TIMEFRAME].py`
2. **Update** the data files list for this timeframe
3. **Run** parallel grid search
4. **Document** best results

## Parameter Grid to Test
```python
ZZ = [2, 3, 4, 5]
FIB = [0.50, 0.618, 0.70, 0.786, 0.85]
TOL = [0.05, 0.10, 0.15]
RSI = [25, 30, 40, 50]
GAP = [3, 5, 7]
TREND = [True, False]
VOL = [True, False]
RSI_F = [True, False]
```

## Expected Output
1. **Console output:** Best parameters and results per asset
2. **Report format:**
```
TIMEFRAME: [TF]
BEST RESULT: X/20 passing 80%+
PARAMETERS:
  - ZZ: X
  - Fib: X
  - Tol: X
  - RSI: <X
  - Gap: X
  - Trend: ON/OFF
  - Vol: ON/OFF
  - RSI_F: ON/OFF

PASSING ASSETS:
  - ASSET1: XX% (X/X)
  - ASSET2: XX% (X/X)
  ...

FAILING ASSETS:
  - ASSET1: XX% (X/X)
  - ASSET2: XX% (X/X)
  ...
```

## Success Criteria
- Grid search completed
- Best parameters identified
- Results documented in above format
- Report back to supervisor

## Time Estimate
~10-15 minutes

## Notes
- Use multiprocessing (all CPU cores)
- If no data files exist for this TF, report back
- Don't change R:R ratio (must stay 1.0)
