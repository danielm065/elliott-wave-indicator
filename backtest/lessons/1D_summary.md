# Daily (1D) Analysis - Round 1

## Current Params
- zz_depth: 5
- zz_dev: 0.5
- signal_gap: 10
- fib_entry: 0.79
- rr_ratio: 2.0
- trend_filter: True
- rsi_filter: True

## Results Table
| Asset | Trades | Wins | Losses | Win Rate | Status |
|-------|--------|------|--------|----------|--------|
| GOOG  | 2      | 2    | 0      | 100.0%   | OK     |
| RKLB  | 2      | 2    | 0      | 100.0%   | OK     |
| PLTR  | 7      | 5    | 2      | 71.4%    | FAIL   |
| OSCR  | 3      | 2    | 1      | 66.7%    | FAIL   |
| MNQ   | 3      | 2    | 1      | 66.7%    | FAIL   |
| MU    | 3      | 1    | 2      | 33.3%    | FAIL   |

## Summary
- **Passing (85%+):** 2/6 = 33%
- **Target:** 90%
- **Gap:** 57%

## Observations
1. Assets with FEW signals (2) have 100% - possibly luck/overfitting
2. PLTR has most signals (7) - better sample, still fails at 71%
3. MU is worst performer (33%) - strategy doesn't fit this stock

## Hypotheses to Test
1. **Lower RR ratio** - current 2.0 might be too aggressive, try 1.0-1.5
2. **Different fib levels** - 0.79 might not be optimal for all
3. **Adjust signal_gap** - more/fewer signals might help

## Next Step
Test with RR=1.0 to see if taking profit earlier improves win rate
