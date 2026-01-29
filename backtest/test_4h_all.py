"""
Test ALL 20 4H assets with current best params
"""
import sys
sys.path.insert(0, r'C:\Users\danie\projects\elliott-wave-indicator\backtest')

from backtester import ElliottICTBacktester, load_data
from pathlib import Path

DATA_DIR = Path(r'C:\Users\danie\projects\elliott-wave-indicator\data')

# ALL 4H files
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

# Best params from optimization
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
    print("="*70, flush=True)
    print("4H FULL TEST - ALL 20 ASSETS", flush=True)
    print("="*70, flush=True)
    print(f"Params: ZZ={PARAMS['zz_depth']}, RR={PARAMS['rr_ratio']}, RSI<{PARAMS['rsi_threshold']}, Tol={PARAMS['fib_tolerance']}", flush=True)
    print()
    
    results = {}
    
    for asset, file in sorted(FILES_4H.items()):
        path = DATA_DIR / file
        if not path.exists():
            print(f"{asset}: FILE NOT FOUND - {file}", flush=True)
            continue
        
        try:
            df = load_data(str(path))
            bt = ElliottICTBacktester(df, PARAMS)
            result = bt.run_backtest()
            total = result.wins + result.losses
            wr = result.win_rate if total > 0 else 0
            
            results[asset] = {
                'total': total,
                'wins': result.wins,
                'losses': result.losses,
                'open': result.open_trades,
                'wr': wr
            }
            
            if total >= 2:
                status = "PASS" if wr >= 85 else "FAIL"
                print(f"{asset}: {result.wins}/{total} = {wr:.0f}% [{status}]", flush=True)
            else:
                print(f"{asset}: {total} trades (not enough)", flush=True)
                
        except Exception as e:
            print(f"{asset}: ERROR - {e}", flush=True)
    
    # Summary
    print()
    print("="*70, flush=True)
    print("SUMMARY", flush=True)
    print("="*70, flush=True)
    
    total_assets = len(results)
    assets_with_trades = sum(1 for r in results.values() if r['total'] >= 2)
    assets_passing_85 = sum(1 for r in results.values() if r['total'] >= 2 and r['wr'] >= 85)
    assets_passing_80 = sum(1 for r in results.values() if r['total'] >= 2 and r['wr'] >= 80)
    assets_no_signals = sum(1 for r in results.values() if r['total'] < 2)
    
    print(f"Total assets: {total_assets}", flush=True)
    print(f"Assets with 2+ trades: {assets_with_trades}", flush=True)
    print(f"Assets with no signals (<2): {assets_no_signals}", flush=True)
    print(f"Passing at 85%: {assets_passing_85}/{assets_with_trades} = {assets_passing_85/assets_with_trades*100:.0f}%", flush=True)
    print(f"Passing at 80%: {assets_passing_80}/{assets_with_trades} = {assets_passing_80/assets_with_trades*100:.0f}%", flush=True)
    
    print()
    print("PASSING (>=85%):", flush=True)
    for asset, r in sorted(results.items()):
        if r['total'] >= 2 and r['wr'] >= 85:
            print(f"  {asset}: {r['wins']}/{r['total']} = {r['wr']:.0f}%", flush=True)
    
    print()
    print("FAILING (<85%):", flush=True)
    for asset, r in sorted(results.items()):
        if r['total'] >= 2 and r['wr'] < 85:
            print(f"  {asset}: {r['wins']}/{r['total']} = {r['wr']:.0f}%", flush=True)
    
    print()
    print("NO SIGNALS (<2 trades):", flush=True)
    for asset, r in sorted(results.items()):
        if r['total'] < 2:
            print(f"  {asset}: {r['total']} trades", flush=True)

if __name__ == '__main__':
    main()
