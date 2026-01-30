# Task: Optimize 30m Parameters

## Mission
מצא פרמטרים אופטימליים עבור 30m שמשיגים 80%+ WR על כמה שיותר נכסים.

## Data Files (30 = 30 minutes)
```python
FILES_30M = {
    'AMD': 'BATS_AMD, 30_cfc90.csv',
    'ASTS': 'BATS_ASTS, 30_7f37b.csv',
    'BA': 'BATS_BA, 30_46d47.csv',
    'CRWV': 'BATS_CRWV, 30_05e77.csv',
    'GOOG': 'BATS_GOOG, 30_2c4a7.csv',
    'HIMS': 'BATS_HIMS, 30_99196.csv',
    'IBKR': 'BATS_IBKR, 30_092a2.csv',
    'INTC': 'BATS_INTC, 30_a2d5b.csv',
    'KRNT': 'BATS_KRNT, 30_eb176.csv',
    'MU': 'BATS_MU, 30_cb8e4.csv',
    'OSCR': 'BATS_OSCR, 30_c1577.csv',
    'PLTR': 'BATS_PLTR, 30_25ae9.csv',
    'RKLB': 'BATS_RKLB, 30_3756c.csv',
    'TTWO': 'BATS_TTWO, 30_e5d22.csv',
    'ADAUSDT': 'BINANCE_ADAUSDT, 30_d120f.csv',
    'BTCUSDT': 'BINANCE_BTCUSDT, 30_af66c.csv',
    'ETHUSD': 'BINANCE_ETHUSD, 30_c3cd4.csv',
    'MNQ': 'MNQ_30m.csv',
    'SOLUSD': 'COINBASE_SOLUSD, 30_e1ec0.csv',
    'USDILS': 'FOREXCOM_USDILS, 30_740f2.csv',
}
```

## Instructions
1. Copy `backtest/test_parallel.py` to `backtest/test_30m.py`
2. Update FILES dict to use FILES_30M above
3. Set `'rr_ratio': 1.0` (don't change!)
4. Run: `python backtest/test_30m.py`
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
TIMEFRAME: 30m
BEST RESULT: X/20 passing 80%+
PARAMETERS: ZZ=X, Fib=X, Tol=X, RSI<X, Gap=X, Trend=X, Vol=X, RSI_F=X

PASSING: [list with WR%]
FAILING: [list with WR%]
```
