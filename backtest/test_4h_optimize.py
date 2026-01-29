"""
Test 4H optimization with different RR ratios and parameters
Focus on failing assets: ADAUSDT, BTCUSDT, MNQ, OSCR, SOLUSD, TTWO
"""
import sys
sys.path.insert(0, r'C:\Users\danie\projects\elliott-wave-indicator\backtest')

from backtester import ElliottICTBacktester, load_data
import os
from pathlib import Path

DATA_DIR = Path(r'C:\Users\danie\projects\elliott-wave-indicator\data')

# 4H files (240 = 4H)
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

# Current best 4H params
BASE_PARAMS = {
    'zz_depth': 4,
    'fib_entry_level': 0.786,
    'rsi_threshold': 50,
    'fib_tolerance': 0.25,
    'rr_ratio': 1.5,
    'use_rsi_filter': True,
    'use_trend_filter': True,
    'use_volume_filter': True,
    'ema_period': 200,
    'signal_gap': 5,
    'zz_dev': 0.2,
}

# Parameter variations to test
RR_VALUES = [1.0, 1.25, 1.5, 2.0, 2.5, 3.0]
RSI_VALUES = [40, 45, 50, 55, 60]
FIB_TOL_VALUES = [0.15, 0.20, 0.25, 0.30, 0.35]
ZZ_DEPTH_VALUES = [3, 4, 5, 6]

def test_params(params):
    """Test all assets with given params, return results"""
    results = {}
    for asset, file in FILES_4H.items():
        path = DATA_DIR / file
        if not path.exists():
            continue
        try:
            df = load_data(str(path))
            bt = ElliottICTBacktester(df, params)
            result = bt.run_backtest()
            results[asset] = {
                'total': result.wins + result.losses,
                'wins': result.wins,
                'losses': result.losses,
                'win_rate': result.win_rate,
                'open': result.open_trades
            }
        except Exception as e:
            results[asset] = {'error': str(e)}
    return results

def count_passing(results, min_trades=2, min_wr=85):
    """Count assets with 85%+ win rate and 2+ trades"""
    passing = 0
    total_with_trades = 0
    for asset, r in results.items():
        if 'error' in r:
            continue
        if r['total'] >= min_trades:
            total_with_trades += 1
            if r['win_rate'] >= min_wr:
                passing += 1
    return passing, total_with_trades

def main():
    print("="*60)
    print("4H PARAMETER OPTIMIZATION")
    print("="*60)
    
    # Test current params first
    print("\n--- Current Params (baseline) ---")
    results = test_params(BASE_PARAMS)
    passing, total = count_passing(results)
    print(f"Coverage: {passing}/{total} = {passing/total*100:.0f}%")
    print("\nResults by asset:")
    for asset, r in sorted(results.items()):
        if 'error' not in r and r['total'] >= 2:
            status = "PASS" if r['win_rate'] >= 85 else "FAIL"
            print(f"  {asset}: {r['wins']}/{r['total']} = {r['win_rate']:.0f}% {status}")
    
    # Test different RR ratios
    print("\n" + "="*60)
    print("TESTING DIFFERENT RR RATIOS")
    print("="*60)
    
    best_rr = None
    best_rr_coverage = 0
    
    for rr in RR_VALUES:
        params = BASE_PARAMS.copy()
        params['rr_ratio'] = rr
        results = test_params(params)
        passing, total = count_passing(results)
        coverage = passing/total*100 if total > 0 else 0
        print(f"\nRR={rr}: {passing}/{total} = {coverage:.0f}%")
        
        if coverage > best_rr_coverage:
            best_rr_coverage = coverage
            best_rr = rr
    
    print(f"\n>>> Best RR: {best_rr} with {best_rr_coverage:.0f}% coverage")
    
    # Test different RSI thresholds with best RR
    print("\n" + "="*60)
    print(f"TESTING RSI THRESHOLDS (with RR={best_rr})")
    print("="*60)
    
    best_rsi = None
    best_rsi_coverage = 0
    
    for rsi in RSI_VALUES:
        params = BASE_PARAMS.copy()
        params['rr_ratio'] = best_rr
        params['rsi_threshold'] = rsi
        results = test_params(params)
        passing, total = count_passing(results)
        coverage = passing/total*100 if total > 0 else 0
        print(f"\nRSI<{rsi}: {passing}/{total} = {coverage:.0f}%")
        
        if coverage > best_rsi_coverage:
            best_rsi_coverage = coverage
            best_rsi = rsi
    
    print(f"\n>>> Best RSI: <{best_rsi} with {best_rsi_coverage:.0f}% coverage")
    
    # Test different Fib tolerance with best RR and RSI
    print("\n" + "="*60)
    print(f"TESTING FIB TOLERANCE (with RR={best_rr}, RSI<{best_rsi})")
    print("="*60)
    
    best_tol = None
    best_tol_coverage = 0
    
    for tol in FIB_TOL_VALUES:
        params = BASE_PARAMS.copy()
        params['rr_ratio'] = best_rr
        params['rsi_threshold'] = best_rsi
        params['fib_tolerance'] = tol
        results = test_params(params)
        passing, total = count_passing(results)
        coverage = passing/total*100 if total > 0 else 0
        print(f"\nTol={tol}: {passing}/{total} = {coverage:.0f}%")
        
        if coverage > best_tol_coverage:
            best_tol_coverage = coverage
            best_tol = tol
    
    print(f"\n>>> Best Tolerance: {best_tol} with {best_tol_coverage:.0f}% coverage")
    
    # Test different Zigzag depths
    print("\n" + "="*60)
    print(f"TESTING ZIGZAG DEPTH (with RR={best_rr}, RSI<{best_rsi}, Tol={best_tol})")
    print("="*60)
    
    best_zz = None
    best_zz_coverage = 0
    
    for zz in ZZ_DEPTH_VALUES:
        params = BASE_PARAMS.copy()
        params['rr_ratio'] = best_rr
        params['rsi_threshold'] = best_rsi
        params['fib_tolerance'] = best_tol
        params['zz_depth'] = zz
        results = test_params(params)
        passing, total = count_passing(results)
        coverage = passing/total*100 if total > 0 else 0
        print(f"\nZZ={zz}: {passing}/{total} = {coverage:.0f}%")
        
        if coverage > best_zz_coverage:
            best_zz_coverage = coverage
            best_zz = zz
    
    print(f"\n>>> Best Zigzag: {best_zz} with {best_zz_coverage:.0f}% coverage")
    
    # Final test with best params
    print("\n" + "="*60)
    print("FINAL TEST WITH OPTIMIZED PARAMS")
    print("="*60)
    
    best_params = BASE_PARAMS.copy()
    best_params['rr_ratio'] = best_rr
    best_params['rsi_threshold'] = best_rsi
    best_params['fib_tolerance'] = best_tol
    best_params['zz_depth'] = best_zz
    
    print(f"\nParams: RR={best_rr}, RSI<{best_rsi}, Tol={best_tol}, ZZ={best_zz}")
    
    results = test_params(best_params)
    passing, total = count_passing(results)
    
    print(f"\nFinal Coverage: {passing}/{total} = {passing/total*100:.0f}%")
    print("\nDetailed results:")
    for asset, r in sorted(results.items()):
        if 'error' not in r and r['total'] >= 2:
            status = "PASS" if r['win_rate'] >= 85 else "FAIL"
            print(f"  {asset}: {r['wins']}/{r['total']} = {r['win_rate']:.0f}% {status}")
    
    # Show failing assets
    print("\nFailing assets:")
    for asset, r in sorted(results.items()):
        if 'error' not in r and r['total'] >= 2 and r['win_rate'] < 85:
            print(f"  {asset}: {r['wins']}/{r['total']} = {r['win_rate']:.0f}%")

if __name__ == '__main__':
    main()
