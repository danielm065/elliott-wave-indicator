"""
Test per-asset optimized params to reach 16+
Some assets need Trend=OFF (AMD, BTCUSDT)
"""
import sys
sys.path.insert(0, r'C:\Users\danie\projects\elliott-wave-indicator\backtest')

from backtester import ElliottICTBacktester, load_data
from pathlib import Path

DATA_DIR = Path(r'C:\Users\danie\projects\elliott-wave-indicator\data')

FILES_4H = {
    'AMD': 'BATS_AMD, 240_c2599.csv',
    'ASTS': 'BATS_ASTS, 240_a0ab9.csv',
    'BA': 'BATS_BA, 240_69b3b.csv',
    'CRWV': 'BATS_CRWV, 240_ed96a.csv',
    'GOOG': 'BATS_GOOG, 240_52190.csv',
    'HIMS': 'BATS_HIMS, 240_9ad5f.csv',
    'IBKR': 'BATS_IBKR, 240_eef24.csv',
    'INTC': 'BATS_INTC, 240_43ac7.csv',
    'KRNT': 'BATS_KRNT, 240_38050.csv',
    'MU': 'BATS_MU, 240_6d83f.csv',
    'OSCR': 'BATS_OSCR, 240_69bf3.csv',
    'PLTR': 'BATS_PLTR, 240_4ba34.csv',
    'RKLB': 'BATS_RKLB, 240_9e8cf.csv',
    'TTWO': 'BATS_TTWO, 240_ba1c1.csv',
    'ADAUSDT': 'BINANCE_ADAUSDT, 240_200b2.csv',
    'BTCUSDT': 'BINANCE_BTCUSDT, 240_fe0b8.csv',
    'ETHUSD': 'BINANCE_ETHUSD, 240_aff0c.csv',
    'MNQ': 'CME_MINI_MNQ1!, 240.csv',
    'SOLUSD': 'COINBASE_SOLUSD, 240_b1f00.csv',
    'USDILS': 'FOREXCOM_USDILS, 240_3fecc.csv',
}

# Base params (works for 14/20)
BASE = {
    'zz_depth': 2,
    'fib_entry_level': 0.786,
    'fib_tolerance': 0.05,
    'rsi_threshold': 40,
    'signal_gap': 2,
    'use_trend_filter': True,
    'use_volume_filter': True,
    'use_rsi_filter': True,
    'rr_ratio': 1.0,
    'zz_dev': 0.2,
    'ema_period': 200,
}

# Custom params for specific assets
CUSTOM = {
    # AMD needs: Trend=OFF, Fib=0.618
    'AMD': {'fib_entry_level': 0.618, 'fib_tolerance': 0.10, 'use_trend_filter': False},
    # BTCUSDT needs: ZZ=3, Fib=0.618, Trend=OFF
    'BTCUSDT': {'zz_depth': 3, 'fib_entry_level': 0.618, 'fib_tolerance': 0.05, 'use_trend_filter': False},
    # Try to fix MNQ
    'MNQ': {'fib_tolerance': 0.10},
    # Try to fix MU
    'MU': {'fib_tolerance': 0.10},
}

def test_asset(asset, file, custom_params=None):
    path = DATA_DIR / file
    if not path.exists():
        return None
    
    df = load_data(str(path))
    params = {**BASE}
    if custom_params:
        params.update(custom_params)
    
    bt = ElliottICTBacktester(df, params)
    result = bt.run_backtest()
    total = result.wins + result.losses
    
    return {
        'total': total,
        'wins': result.wins,
        'wr': result.win_rate if total > 0 else 0,
        'params': params
    }

def main():
    print("Testing with per-asset optimized params", flush=True)
    print("="*60, flush=True)
    
    results = {}
    for asset, file in sorted(FILES_4H.items()):
        custom = CUSTOM.get(asset)
        r = test_asset(asset, file, custom)
        
        if r:
            results[asset] = r
            if r['total'] >= 2:
                status = "PASS" if r['wr'] >= 80 else "FAIL"
                custom_str = " [CUSTOM]" if custom else ""
                print(f"{asset}: {r['wins']}/{r['total']} = {r['wr']:.0f}% [{status}]{custom_str}", flush=True)
            else:
                print(f"{asset}: {r['total']} trades [NO SIGNAL]", flush=True)
    
    passing = sum(1 for r in results.values() if r['total'] >= 2 and r['wr'] >= 80)
    with_trades = sum(1 for r in results.values() if r['total'] >= 2)
    
    print(f"\n{'='*60}", flush=True)
    print(f"TOTAL: {passing}/{with_trades} passing ({passing}/20 overall)", flush=True)
    
    failing = [a for a, r in results.items() if r['total'] >= 2 and r['wr'] < 80]
    no_signal = [a for a, r in results.items() if r['total'] < 2]
    
    if failing:
        print(f"Failing: {', '.join(failing)}", flush=True)
    if no_signal:
        print(f"No signal: {', '.join(no_signal)}", flush=True)

if __name__ == '__main__':
    main()
