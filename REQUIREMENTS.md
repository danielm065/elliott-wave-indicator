# Requirements - Elliott Wave Indicator

## Phase 1: Backtesting Infrastructure ✅
- [x] Python backtester שמדמה את הלוגיקה של Pine Script
- [x] טעינת נתוני CSV מ-TradingView
- [x] חישוב ZigZag, Fibonacci, RSI, Volume
- [x] הרצה מקבילית (multiprocessing)

## Phase 2: Optimization Per Timeframe
לכל טווח זמן:
- [ ] מציאת פרמטרים אופטימליים
- [ ] השגת 80%+ WR על 80%+ מהנכסים
- [ ] תיעוד התוצאות

### טווחי זמן:
| TF | Status | Best Result | Parameters |
|----|--------|-------------|------------|
| 1D | ✅ DONE | 10/11 (91%) | ZZ=4, Fib=0.786, RSI<45, RR=1.5 |
| 4H | ✅ DONE | 14/18 (78%) | ZZ=2, Fib=0.786, RSI<40, RR=1.0 |
| 1H | ✅ DONE | 11/20 (55%) | ZZ=3, Fib=0.85, RSI<30, RR=1.0 |
| 30m | 🔄 TODO | - | - |
| 15m | 🔄 TODO | - | - |
| 5m | 🔄 TODO | - | - |

## Phase 3: Pine Script Implementation
- [ ] עדכון קוד Pine עם פרמטרים לכל TF
- [ ] בדיקה ידנית ב-TradingView
- [ ] אימות שהתוצאות תואמות ל-Backtester

## Constraints (לא לשנות!)
- **R:R = 1:1** - יחס סיכון/רווח קבוע
- **Long Only** - רק עסקאות קנייה
- **אותה לוגיקה** - Backtester = Pine Script

## Success Criteria
טווח זמן נחשב "גמור" כאשר:
1. נבדקו כל 20 הנכסים
2. נמצאו פרמטרים עם 80%+ WR
3. לפחות 80% מהנכסים עוברים
4. התוצאות מתועדות
