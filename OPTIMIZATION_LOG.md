# Elliott + ICT Indicator - Optimization Log

## Target: 85%+ Win Rate on all timeframes

---

## Daily (1D) - ✅ OPTIMIZED

**Date:** 2026-01-29

**Best Overall WR:** 85.2% (23W/4L)

**Optimal Parameters:**
```
zz_depth: 4
zz_dev: 0.05
signal_gap: 5
fib_entry_level: 0.79
rr_ratio: 1.5
use_trend_filter: True
```

**Per-Asset Results:**
| Asset | WR | W/L | Status |
|-------|-----|-----|--------|
| GOOG | 100% | 2/0 | ✅ |
| RKLB | 100% | 2/0 | ✅ |
| OSCR | 100% | 3/0 | ✅ |
| PLTR | 90% | 9/1 | ✅ |
| MNQ | 75% | 3/1 | ⚠️ |
| NQ | 75% | 3/1 | ⚠️ |
| MU | 50% | 1/1 | ❌ |

**Key Insights:**
1. `zz_dev=0.05` is critical - very small deviation catches precise swings
2. `trend_filter=True` improves accuracy significantly
3. MU is problematic on Daily - consider excluding or using different params
4. Fewer signals (27 vs 88 baseline) but much more accurate

**Baseline comparison:**
- Before: 79.5% (70W/18L)
- After: 85.2% (23W/4L)
- Improvement: +5.7% WR, but fewer signals

---

## 4H - ✅ IMPROVED (85.0%)

**Date:** 2026-01-29

**Best WR:** 85.0% (34W/6L) ✅ TARGET REACHED!

**Optimal Parameters:**
```
zz_depth: 3
zz_dev: 0.03
signal_gap: 5
fib_entry_level: 0.70
rr_ratio: 1.0  ← KEY CHANGE! (was 1.5)
use_trend_filter: True
```

**Key Insight:** Changing R:R from 1:1.5 to 1:1 improved WR from 76.9% to 85.0%!

---

## 1H - ⚠️ IMPROVED (80.3%)

**Date:** 2026-01-29

**Best WR:** 80.3% (49W/12L) - close to target!

**Improved Parameters:**
```
zz_depth: 3
zz_dev: 0.03
signal_gap: 5
fib_entry_level: 0.786
rr_ratio: 1.0  ← KEY CHANGE! (was 1.5)
use_trend_filter: False
```

**Key Insight:** R:R 1:1 improved from 72.1% to 80.3%
**Still needs:** +4.7% to reach 85%

---

## 30m - ⚠️ IN PROGRESS (78.6%)

**Date:** 2026-01-29

**Current Best WR:** 78.6% (target: 85%)

**Current Parameters:**
```
zz_depth: 5
zz_dev: 0.03
signal_gap: 5
fib_entry_level: 0.786
rr_ratio: 1.5
use_trend_filter: True
```

---

## 15m - ⬜ TODO

## 5m - ⬜ TODO

---

## General Observations

### Parameters that work well across timeframes:
- `zz_depth`: 4-5
- `zz_dev`: 0.05-0.1 (lower is better)
- `rr_ratio`: 1.5 (not 2.0!)
- `fib_entry_level`: 0.79 or 0.786

### Problematic assets:
- MU - inconsistent behavior
- Sometimes NQ/MNQ perform worse than expected

### Next steps:
1. Optimize 4H with focused grid
2. Consider asset-specific parameters
3. Test if excluding MU improves overall results
