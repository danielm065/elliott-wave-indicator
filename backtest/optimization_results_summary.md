# Optimization Results Summary
Date: 2026-01-29

## Lower Timeframes (30m, 15m, 5m)

### 30m - 88.2% Win Rate (15W/2L)
| Parameter | Value |
|-----------|-------|
| zz_depth | 4 |
| zz_dev | 0.01 |
| signal_gap | 8 |
| fib_entry | 0.618 |
| rr_ratio | 0.8 |
| trend_filter | True |
| rsi_filter | True |

### 15m - 86.4% Win Rate (19W/3L)
| Parameter | Value |
|-----------|-------|
| zz_depth | 5 |
| zz_dev | 0.01 |
| signal_gap | 8 |
| fib_entry | 0.786 |
| rr_ratio | 0.8 |
| trend_filter | True |
| rsi_filter | True |

### 5m - 92.9% Win Rate (13W/1L) ⭐ Best!
| Parameter | Value |
|-----------|-------|
| zz_depth | 4 |
| zz_dev | 0.01 |
| signal_gap | 10 |
| fib_entry | 0.75 |
| rr_ratio | 0.8 |
| trend_filter | True |
| rsi_filter | True |

## Key Insights

1. **Very tight ZZ Deviation (0.01)** works best across all lower TFs
2. **Trend + RSI filters** are essential - always enabled in best configs
3. **Different Fib levels** work best per TF:
   - 30m: 0.618 (deeper retracement)
   - 15m: 0.786 (shallower)
   - 5m: 0.75 (middle ground)
4. **Signal gap 8-10** is optimal for lower TFs (vs 20-60 before)

## Applied to Pine Script
All parameters updated in: `src/elliott-ict-v20-fixed.pine`
