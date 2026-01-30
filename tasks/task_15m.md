# Task: Optimize 15m Parameters

## Mission
מצא פרמטרים אופטימליים עבור 15m שמשיגים 80%+ WR על כמה שיותר נכסים.

## Data Files (15 = 15 minutes)
```python
FILES_15M = {
    'AMD': 'BATS_AMD, 15_c4561.csv',
    'ASTS': 'BATS_ASTS, 15_bb200.csv',
    'BA': 'BATS_BA, 15_9984c.csv',
    'CRWV': 'BATS_CRWV, 15_7ab04.csv',
    'GOOG': 'BATS_GOOG, 15_dd970.csv',
    'HIMS': 'BATS_HIMS, 15_eece3.csv',
    'IBKR': 'BATS_IBKR, 15_6f0d9.csv',
    'INTC': 'BATS_INTC, 15_d64fe.csv',
    'KRNT': 'BATS_KRNT, 15_b437d.csv',
    'MU': 'BATS_MU, 15_56dd5.csv',
    'OSCR': 'BATS_OSCR, 15_a161b.csv',
    'PLTR': 'BATS_PLTR, 15_838ea.csv',
    'RKLB': 'BATS_RKLB, 15_90881.csv',
    'TTWO': 'BATS_TTWO, 15_e2f45.csv',
    'ADAUSDT': 'BINANCE_ADAUSDT, 15_370bf.csv',
    'BTCUSDT': 'BINANCE_BTCUSDT, 15_15096.csv',
    'ETHUSD': 'BINANCE_ETHUSD, 15_4699d.csv',
    'MNQ': 'MNQ_15m.csv',
    'SOLUSD': 'COINBASE_SOLUSD, 15_3fc82.csv',
    'USDILS': 'FOREXCOM_USDILS, 15_5d720.csv',
}
```

## Instructions
1. Copy `backtest/test_parallel.py` to `backtest/test_15m.py`
2. Update FILES dict to use FILES_15M above
3. Set `'rr_ratio': 1.0` (don't change!)
4. Run: `python backtest/test_15m.py`
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
TIMEFRAME: 15m
BEST RESULT: X/20 passing 80%+
PARAMETERS: ZZ=X, Fib=X, Tol=X, RSI<X, Gap=X, Trend=X, Vol=X, RSI_F=X

PASSING: [list with WR%]
FAILING: [list with WR%]
```
