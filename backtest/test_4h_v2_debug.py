"""
Debug V2 backtester - see what's happening with longs vs shorts
"""
import sys
sys.path.insert(0, r'C:\Users\danie\projects\elliott-wave-indicator\backtest')

from backtester_v2 import ElliottICTBacktesterV2, load_data
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

def test_mode(mode_name, params):
    print(f"\n{'='*60}", flush=True)
    print(f"Testing: {mode_name}", flush=True)
    print(f"{'='*60}", flush=True)
    
    results = {}
    for asset, file in FILES_4H.items():
        path = DATA_DIR / file
        if not path.exists():
            continue
        try:
            df = load_data(str(path))
            bt = ElliottICTBacktesterV2(df, params)
            result = bt.run_backtest()
            total = result.wins + result.losses
            results[asset] = {
                'total': total,
                'wins': result.wins,
                'wr': result.win_rate if total > 0 else 0,
                'long_w': result.long_wins,
                'long_l': result.long_losses,
                'short_w': result.short_wins,
                'short_l': result.short_losses
            }
        except Exception as e:
            print(f"Error {asset}: {e}", flush=True)
    
    passing = sum(1 for r in results.values() if r['total'] >= 2 and r['wr'] >= 80)
    with_trades = sum(1 for r in results.values() if r['total'] >= 2)
    
    print(f"\nPassing: {passing}/{with_trades} = {passing/with_trades*100:.0f}%" if with_trades > 0 else "N/A", flush=True)
    
    total_long = sum(r['long_w'] + r['long_l'] for r in results.values())
    total_short = sum(r['short_w'] + r['short_l'] for r in results.values())
    long_wins = sum(r['long_w'] for r in results.values())
    short_wins = sum(r['short_w'] for r in results.values())
    
    print(f"Longs: {long_wins}/{total_long} = {long_wins/total_long*100:.0f}%" if total_long > 0 else "Longs: 0", flush=True)
    print(f"Shorts: {short_wins}/{total_short} = {short_wins/total_short*100:.0f}%" if total_short > 0 else "Shorts: 0", flush=True)
    
    print("\nDetails:", flush=True)
    for asset, r in sorted(results.items()):
        if r['total'] >= 2:
            status = "PASS" if r['wr'] >= 80 else "FAIL"
            print(f"  {asset}: {r['wins']}/{r['total']} = {r['wr']:.0f}% [{status}] L:{r['long_w']}/{r['long_w']+r['long_l']} S:{r['short_w']}/{r['short_w']+r['short_l']}", flush=True)
        else:
            print(f"  {asset}: {r['total']} trades", flush=True)
    
    return passing, with_trades

def main():
    base_params = {
        'zz_depth': 2,
        'rr_ratio': 1.0,
        'rsi_threshold': 40,
        'fib_tolerance': 0.10,
        'fib_entry_level': 0.786,
        'use_rsi_filter': True,
        'use_trend_filter': True,
        'ema_period': 200,
        'signal_gap': 5,
        'zz_dev': 0.2,
    }
    
    # Test 1: Longs only (original)
    params1 = {**base_params, 'enable_longs': True, 'enable_shorts': False, 'enable_fvg': False}
    p1, t1 = test_mode("LONGS ONLY", params1)
    
    # Test 2: Shorts only
    params2 = {**base_params, 'enable_longs': False, 'enable_shorts': True, 'enable_fvg': False}
    p2, t2 = test_mode("SHORTS ONLY", params2)
    
    # Test 3: Longs + Shorts
    params3 = {**base_params, 'enable_longs': True, 'enable_shorts': True, 'enable_fvg': False}
    p3, t3 = test_mode("LONGS + SHORTS", params3)
    
    # Test 4: Longs + FVG
    params4 = {**base_params, 'enable_longs': True, 'enable_shorts': False, 'enable_fvg': True}
    p4, t4 = test_mode("LONGS + FVG", params4)
    
    print(f"\n{'='*60}", flush=True)
    print("SUMMARY", flush=True)
    print(f"{'='*60}", flush=True)
    print(f"Longs only:     {p1}/{t1}", flush=True)
    print(f"Shorts only:    {p2}/{t2}", flush=True)
    print(f"Longs + Shorts: {p3}/{t3}", flush=True)
    print(f"Longs + FVG:    {p4}/{t4}", flush=True)

if __name__ == '__main__':
    main()
