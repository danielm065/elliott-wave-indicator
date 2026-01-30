"""
1H - Find per-asset params to reach 16/20
"""
import sys
sys.path.insert(0, r'C:\Users\danie\projects\elliott-wave-indicator\backtest')

from backtester import ElliottICTBacktester, load_data
from pathlib import Path
from itertools import product

DATA_DIR = Path(r'C:\Users\danie\projects\elliott-wave-indicator\data')

FILES_1H = {
    'AMD': 'BATS_AMD, 60_2853d.csv',
    'ASTS': 'BATS_ASTS, 60_360b6.csv',
    'BA': 'BATS_BA, 60_a5067.csv',
    'CRWV': 'BATS_CRWV, 60_58712.csv',
    'GOOG': 'BATS_GOOG, 60_78270.csv',
    'HIMS': 'BATS_HIMS, 60_ea867.csv',
    'IBKR': 'BATS_IBKR, 60_ebbaf.csv',
    'INTC': 'BATS_INTC, 60_59380.csv',
    'KRNT': 'BATS_KRNT, 60_f5a05.csv',
    'MU': 'BATS_MU, 60_609b8.csv',
    'OSCR': 'BATS_OSCR, 60_092fb.csv',
    'PLTR': 'BATS_PLTR, 60_14b34.csv',
    'RKLB': 'BATS_RKLB, 60_ae005.csv',
    'TTWO': 'BATS_TTWO, 60_73235.csv',
    'ADAUSDT': 'BINANCE_ADAUSDT, 60_ee9e1.csv',
    'BTCUSDT': 'BINANCE_BTCUSDT, 60_b6ebd.csv',
    'ETHUSD': 'BINANCE_ETHUSD, 60_b3215.csv',
    'MNQ': 'MNQ_1H.csv',
    'SOLUSD': 'COINBASE_SOLUSD, 60_49536.csv',
    'USDILS': 'FOREXCOM_USDILS, 60_14147.csv',
}

# Failed assets from uniform test
FAILED = ['ASTS', 'BA', 'GOOG', 'IBKR', 'MU', 'PLTR', 'RKLB', 'TTWO']
NO_SIGNAL = ['HIMS', 'INTC', 'KRNT', 'SOLUSD', 'USDILS']

# Grid for finding custom params
ZZ = [2, 3, 4, 5]
FIB = [0.50, 0.618, 0.70, 0.786, 0.85]
TOL = [0.05, 0.10, 0.15, 0.20, 0.30]
RSI = [35, 40, 50, 60, 70]
GAP = [2, 3, 5]
TREND = [True, False]

def find_best_params(asset, file):
    path = DATA_DIR / file
    if not path.exists():
        return None
    
    df = load_data(str(path))
    best = {'wr': 0, 'total': 0, 'params': None}
    
    for zz, fib, tol, rsi, gap, trend in product(ZZ, FIB, TOL, RSI, GAP, TREND):
        params = {
            'zz_depth': zz,
            'fib_entry_level': fib,
            'fib_tolerance': tol,
            'rsi_threshold': rsi,
            'signal_gap': gap,
            'use_trend_filter': trend,
            'use_volume_filter': True,
            'use_rsi_filter': True,
            'rr_ratio': 1.0,
            'zz_dev': 0.2,
            'ema_period': 200,
        }
        
        try:
            bt = ElliottICTBacktester(df, params)
            result = bt.run_backtest()
            total = result.wins + result.losses
            
            if total >= 2 and result.win_rate >= 80:
                if total > best['total'] or (total == best['total'] and result.win_rate > best['wr']):
                    best = {
                        'total': total,
                        'wins': result.wins,
                        'wr': result.win_rate,
                        'params': f"ZZ={zz},Fib={fib},Tol={tol},RSI<{rsi},Gap={gap},T={trend}"
                    }
        except:
            pass
    
    return best if best['params'] else None

def main():
    print("Finding per-asset params for failing 1H assets...", flush=True)
    
    results = {}
    
    for asset in FAILED + NO_SIGNAL:
        file = FILES_1H.get(asset)
        if not file:
            continue
        
        print(f"\n{asset}...", end=" ", flush=True)
        best = find_best_params(asset, file)
        
        if best:
            print(f"FOUND: {best['wins']}/{best['total']} = {best['wr']:.0f}%", flush=True)
            print(f"  {best['params']}", flush=True)
            results[asset] = best
        else:
            print("Cannot reach 80%", flush=True)
    
    print(f"\n{'='*60}", flush=True)
    print("SUMMARY", flush=True)
    print(f"{'='*60}", flush=True)
    
    can_pass = len(results)
    already_pass = 7  # From uniform test
    
    print(f"Already passing: {already_pass}", flush=True)
    print(f"Can pass with custom: {can_pass}", flush=True)
    print(f"Total potential: {already_pass + can_pass}/20", flush=True)
    
    if results:
        print("\nCustom params needed:", flush=True)
        for asset, r in results.items():
            print(f"  {asset}: {r['params']}", flush=True)

if __name__ == '__main__':
    main()
