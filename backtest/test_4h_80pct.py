"""
Test 4H with 80% threshold instead of 85%
See how many more assets would pass
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

# Best params found
PARAMS = {
    'zz_depth': 3,
    'rr_ratio': 1.0,
    'rsi_threshold': 50,
    'fib_tolerance': 0.20,
    'fib_entry_level': 0.786,
    'use_rsi_filter': True,
    'use_trend_filter': True,
    'use_volume_filter': True,
    'ema_period': 200,
    'signal_gap': 5,
    'zz_dev': 0.2,
}

def main():
    print("="*60)
    print("4H RESULTS WITH DIFFERENT THRESHOLDS")
    print("="*60)
    print(f"Params: ZZ={PARAMS['zz_depth']}, RR={PARAMS['rr_ratio']}, RSI<{PARAMS['rsi_threshold']}, Tol={PARAMS['fib_tolerance']}")
    
    results = {}
    
    for asset, file in FILES_4H.items():
        path = DATA_DIR / file
        if not path.exists():
            continue
        try:
            df = load_data(str(path))
            bt = ElliottICTBacktester(df, PARAMS)
            result = bt.run_backtest()
            total = result.wins + result.losses
            results[asset] = {
                'total': total,
                'wins': result.wins,
                'losses': result.losses,
                'wr': result.win_rate if total > 0 else 0
            }
        except Exception as e:
            print(f"Error {asset}: {e}")
    
    # Count at different thresholds
    thresholds = [70, 75, 80, 85, 90]
    
    print("\n" + "="*60)
    print("COVERAGE AT DIFFERENT WIN RATE THRESHOLDS")
    print("="*60)
    
    for thresh in thresholds:
        passing = 0
        total = 0
        for asset, r in results.items():
            if r['total'] >= 2:
                total += 1
                if r['wr'] >= thresh:
                    passing += 1
        coverage = passing/total*100 if total > 0 else 0
        print(f"  >= {thresh}% WR: {passing}/{total} = {coverage:.0f}% coverage")
    
    print("\n" + "="*60)
    print("ALL RESULTS (sorted by win rate)")
    print("="*60)
    
    sorted_results = sorted(results.items(), key=lambda x: -x[1]['wr'])
    
    for asset, r in sorted_results:
        if r['total'] >= 2:
            status_85 = ">=85" if r['wr'] >= 85 else ">=80" if r['wr'] >= 80 else ">=70" if r['wr'] >= 70 else "<70"
            print(f"  {asset}: {r['wins']}/{r['total']} = {r['wr']:.0f}% [{status_85}]")
    
    print("\nNo signals (< 2 trades):")
    for asset, r in sorted_results:
        if r['total'] < 2:
            print(f"  {asset}: {r['total']} trades")

if __name__ == '__main__':
    main()
