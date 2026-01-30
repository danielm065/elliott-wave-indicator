# Task: Optimize 5m Parameters

## Mission
מצא פרמטרים אופטימליים עבור 5m שמשיגים 80%+ WR על כמה שיותר נכסים.

## Data Files (5 = 5 minutes)
```python
FILES_5M = {
    'AMD': 'BATS_AMD, 5_f7455.csv',
    'ASTS': 'BATS_ASTS, 5_521f9.csv',
    'BA': 'BATS_BA, 5_e3560.csv',
    'CRWV': 'BATS_CRWV, 5_8bf0e.csv',
    'GOOG': 'BATS_GOOG, 5_8b9d7.csv',
    'HIMS': 'BATS_HIMS, 5_58bb0.csv',
    'IBKR': 'BATS_IBKR, 5_d46be.csv',
    'INTC': 'BATS_INTC, 5_c9971.csv',
    'KRNT': 'BATS_KRNT, 5_204ad.csv',
    'MU': 'BATS_MU, 5_b2508.csv',
    'OSCR': 'BATS_OSCR, 5_864be.csv',
    'PLTR': 'BATS_PLTR, 5_f339c.csv',
    'RKLB': 'BATS_RKLB, 5_b0b72.csv',
    'TTWO': 'BATS_TTWO, 5_d7ea8.csv',
    'ADAUSDT': 'BINANCE_ADAUSDT, 5_e01b1.csv',
    'BTCUSDT': 'BINANCE_BTCUSDT, 5_69b1c.csv',
    'ETHUSD': 'BINANCE_ETHUSD, 5_26e57.csv',
    'MNQ': 'MNQ_5m.csv',
    'SOLUSD': 'COINBASE_SOLUSD, 5_77193.csv',
    'USDILS': 'FOREXCOM_USDILS, 5_7aa81.csv',
}
```

## Instructions
1. Copy `backtest/test_parallel.py` to `backtest/test_5m.py`
2. Update FILES dict to use FILES_5M above
3. Set `'rr_ratio': 1.0` (don't change!)
4. Run: `python backtest/test_5m.py`
5. Report results in format below

## Parameter Grid
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

## Output Format
```
TIMEFRAME: 5m
BEST RESULT: X/20 passing 80%+
PARAMETERS: ZZ=X, Fib=X, Tol=X, RSI<X, Gap=X, Trend=X, Vol=X, RSI_F=X

PASSING: [list with WR%]
FAILING: [list with WR%]
```
