"""
1H - Check remaining 3 assets
"""
import sys
sys.path.insert(0, r'C:\Users\danie\projects\elliott-wave-indicator\backtest')

from backtester import ElliottICTBacktester, load_data
from pathlib import Path
from itertools import product

DATA_DIR = Path(r'C:\Users\danie\projects\elliott-wave-indicator\data')

REMAINING = {
    'KRNT': 'BATS_KRNT, 60_f5a05.csv',
    'SOLUSD': 'COINBASE_SOLUSD, 60_49536.csv',
    'USDILS': 'FOREXCOM_USDILS, 60_14147.csv',
}

ZZ = [2, 3, 4, 5]
FIB = [0.50, 0.618, 0.70, 0.786, 0.85]
TOL = [0.05, 0.10, 0.15, 0.20, 0.30]
RSI = [35, 40, 50, 60, 70]
GAP = [2, 3, 5]
TREND = [True, False]

def find_best(asset, file):
    path = DATA_DIR / file
    if not path.exists():
        return None
    
    df = load_data(str(path))
    best = {'wr': 0, 'total': 0, 'params': None}
    
    for zz, fib, tol, rsi, gap, trend in product(ZZ, FIB, TOL, RSI, GAP, TREND):
        params = {
            'zz_depth': zz, 'fib_entry_level': fib, 'fib_tolerance': tol,
            'rsi_threshold': rsi, 'signal_gap': gap, 'use_trend_filter': trend,
            'use_volume_filter': True, 'use_rsi_filter': True,
            'rr_ratio': 1.0, 'zz_dev': 0.2, 'ema_period': 200,
        }
        try:
            bt = ElliottICTBacktester(df, params)
            result = bt.run_backtest()
            total = result.wins + result.losses
            if total >= 2 and result.win_rate >= 80:
                if total > best['total'] or (total == best['total'] and result.win_rate > best['wr']):
                    best = {'total': total, 'wins': result.wins, 'wr': result.win_rate,
                            'params': f"ZZ={zz},Fib={fib},Tol={tol},RSI<{rsi},Gap={gap},T={trend}"}
        except:
            pass
    return best if best['params'] else None

for asset, file in REMAINING.items():
    print(f"{asset}...", end=" ", flush=True)
    best = find_best(asset, file)
    if best:
        print(f"FOUND: {best['wins']}/{best['total']} = {best['wr']:.0f}%", flush=True)
        print(f"  {best['params']}", flush=True)
    else:
        print("Cannot reach 80%", flush=True)
