"""
Quick 4H test with specific parameter sets
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

BASE = {
    'fib_entry_level': 0.786,
    'use_rsi_filter': True,
    'use_trend_filter': True,
    'use_volume_filter': True,
    'ema_period': 200,
    'signal_gap': 5,
    'zz_dev': 0.2,
}

# Parameter sets to test
PARAM_SETS = [
    {'name': 'Original', 'zz_depth': 4, 'rr_ratio': 1.5, 'rsi_threshold': 50, 'fib_tolerance': 0.25},
    {'name': 'Lower RR', 'zz_depth': 4, 'rr_ratio': 1.0, 'rsi_threshold': 50, 'fib_tolerance': 0.25},
    {'name': 'Tighter Tol', 'zz_depth': 4, 'rr_ratio': 1.5, 'rsi_threshold': 50, 'fib_tolerance': 0.18},
    {'name': 'ZZ=3', 'zz_depth': 3, 'rr_ratio': 1.5, 'rsi_threshold': 50, 'fib_tolerance': 0.25},
    {'name': 'RSI<45', 'zz_depth': 4, 'rr_ratio': 1.5, 'rsi_threshold': 45, 'fib_tolerance': 0.25},
    {'name': 'RSI<55', 'zz_depth': 4, 'rr_ratio': 1.5, 'rsi_threshold': 55, 'fib_tolerance': 0.25},
    {'name': 'ZZ=3+RR=1', 'zz_depth': 3, 'rr_ratio': 1.0, 'rsi_threshold': 50, 'fib_tolerance': 0.20},
    {'name': 'ZZ=5', 'zz_depth': 5, 'rr_ratio': 1.5, 'rsi_threshold': 50, 'fib_tolerance': 0.25},
    {'name': 'Conservative', 'zz_depth': 5, 'rr_ratio': 1.0, 'rsi_threshold': 45, 'fib_tolerance': 0.20},
    {'name': 'Aggressive', 'zz_depth': 3, 'rr_ratio': 2.0, 'rsi_threshold': 55, 'fib_tolerance': 0.30},
]

def test_params(params):
    full_params = {**BASE, **{k: v for k, v in params.items() if k != 'name'}}
    results = {}
    
    for asset, file in FILES_4H.items():
        path = DATA_DIR / file
        if not path.exists():
            continue
        try:
            df = load_data(str(path))
            bt = ElliottICTBacktester(df, full_params)
            result = bt.run_backtest()
            total = result.wins + result.losses
            results[asset] = {
                'total': total,
                'wins': result.wins,
                'wr': result.win_rate if total > 0 else 0
            }
        except Exception as e:
            print(f"  Error {asset}: {e}")
    
    return results

def main():
    print("="*60)
    print("4H QUICK PARAMETER TEST", flush=True)
    print("="*60)
    
    all_results = []
    
    for p in PARAM_SETS:
        print(f"\nTesting: {p['name']}...", flush=True)
        results = test_params(p)
        
        passing = 0
        total_with_trades = 0
        
        for asset, r in results.items():
            if r['total'] >= 2:
                total_with_trades += 1
                if r['wr'] >= 85:
                    passing += 1
        
        coverage = passing/total_with_trades*100 if total_with_trades > 0 else 0
        all_results.append({
            'name': p['name'],
            'params': p,
            'passing': passing,
            'total': total_with_trades,
            'coverage': coverage,
            'results': results
        })
        
        print(f"  -> {passing}/{total_with_trades} = {coverage:.0f}%", flush=True)
    
    # Sort by coverage
    all_results.sort(key=lambda x: -x['coverage'])
    
    print("\n" + "="*60)
    print("RANKING", flush=True)
    print("="*60)
    
    for i, r in enumerate(all_results):
        print(f"{i+1}. {r['name']}: {r['passing']}/{r['total']} = {r['coverage']:.0f}%", flush=True)
    
    # Show best result details
    best = all_results[0]
    print("\n" + "="*60)
    print(f"BEST: {best['name']}", flush=True)
    print("="*60)
    
    p = best['params']
    print(f"Params: ZZ={p['zz_depth']}, RR={p['rr_ratio']}, RSI<{p['rsi_threshold']}, Tol={p['fib_tolerance']}", flush=True)
    
    print("\nPassing assets:", flush=True)
    for asset, r in sorted(best['results'].items()):
        if r['total'] >= 2 and r['wr'] >= 85:
            print(f"  {asset}: {r['wins']}/{r['total']} = {r['wr']:.0f}%", flush=True)
    
    print("\nFailing assets:", flush=True)
    for asset, r in sorted(best['results'].items()):
        if r['total'] >= 2 and r['wr'] < 85:
            print(f"  {asset}: {r['wins']}/{r['total']} = {r['wr']:.0f}%", flush=True)
    
    print("\nNo signals:", flush=True)
    for asset, r in sorted(best['results'].items()):
        if r['total'] < 2:
            print(f"  {asset}: {r['total']} trades", flush=True)

if __name__ == '__main__':
    main()
