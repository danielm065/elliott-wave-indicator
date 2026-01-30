# Elliott Wave + ICT Indicator - Project Vision

## מטרה
לפתח אינדיקטור TradingView שמזהה נקודות כניסה ל-Long בהתבסס על Elliott Wave + ICT concepts.

## יעדים
- **Win Rate:** 80%+ על כל נכס
- **כיסוי:** לפחות 80% מהנכסים עוברים את היעד
- **R:R יחס:** 1:1 (קבוע, לא לשנות)
- **טווחי זמן:** 1D, 4H, 1H, 30m, 15m, 5m

## הלוגיקה
1. **ZigZag** - מזהה Swing High/Low
2. **Fibonacci Retracement** - מחשב רמות תיקון
3. **Entry** - כניסה כשמחיר נוגע ברמת Fib
4. **SL** - מתחת ל-Swing Low
5. **TP** - לפי יחס R:R

## פילטרים אופציונליים
- **RSI Filter** - RSI מתחת לסף מסוים
- **Volume Filter** - נפח מעל ממוצע
- **Trend Filter** - מחיר מעל/מתחת EMA

## נכסים לבדיקה (20)
**מניות:** AMD, ASTS, BA, CRWV, GOOG, HIMS, IBKR, INTC, KRNT, MU, OSCR, PLTR, RKLB, TTWO
**קריפטו:** ADAUSDT, BTCUSDT, ETHUSD, SOLUSD
**פיוצ'רס:** MNQ
**פורקס:** USDILS

## קבצי נתונים
`data/` - קבצי CSV מ-TradingView לכל נכס וטווח זמן

## Backtester
`backtest/backtester.py` - הלוגיקה המרכזית (חייבת להתאים ל-Pine Script)
`backtest/test_parallel.py` - בדיקה מקבילית על 8 ליבות

## Output
`src/` - קוד Pine Script סופי
