"""
Compare original vs optimized params on all 4H assets
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

PARAM_SETS = {
    'Original (SKILL.md)': {'zz_depth': 4, 'rr_ratio': 1.5, 'rsi_threshold': 50, 'fib_tolerance': 0.25},
    'Optimized (ZZ=3)': {'zz_depth': 3, 'rr_ratio': 1.0, 'rsi_threshold': 50, 'fib_tolerance': 0.20},
}

def test_params(params):
    full_params = {**BASE, **params}
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
        except:
            pass
    return results

def main():
    all_results = {}
    
    for name, params in PARAM_SETS.items():
        print(f"\n{'='*70}", flush=True)
        print(f"{name}", flush=True)
        print(f"ZZ={params['zz_depth']}, RR={params['rr_ratio']}, RSI<{params['rsi_threshold']}, Tol={params['fib_tolerance']}", flush=True)
        print(f"{'='*70}", flush=True)
        
        results = test_params(params)
        all_results[name] = results
        
        assets_with_trades = sum(1 for r in results.values() if r['total'] >= 2)
        passing_85 = sum(1 for r in results.values() if r['total'] >= 2 and r['wr'] >= 85)
        passing_80 = sum(1 for r in results.values() if r['total'] >= 2 and r['wr'] >= 80)
        no_signals = sum(1 for r in results.values() if r['total'] < 2)
        
        print(f"\nAssets with 2+ trades: {assets_with_trades}", flush=True)
        print(f"No signals (<2): {no_signals}", flush=True)
        print(f"Pass at 85%: {passing_85}/{assets_with_trades} = {passing_85/assets_with_trades*100:.0f}%" if assets_with_trades > 0 else "N/A", flush=True)
        print(f"Pass at 80%: {passing_80}/{assets_with_trades} = {passing_80/assets_with_trades*100:.0f}%" if assets_with_trades > 0 else "N/A", flush=True)
        
        print("\nAll results:", flush=True)
        for asset, r in sorted(results.items()):
            if r['total'] >= 2:
                status = "PASS" if r['wr'] >= 85 else "80+" if r['wr'] >= 80 else "FAIL"
                print(f"  {asset}: {r['wins']}/{r['total']} = {r['wr']:.0f}% [{status}]", flush=True)
            else:
                print(f"  {asset}: {r['total']} trades", flush=True)
    
    # Side by side comparison
    print(f"\n{'='*70}", flush=True)
    print("SIDE-BY-SIDE COMPARISON", flush=True)
    print(f"{'='*70}", flush=True)
    print(f"{'Asset':<12} {'Original':<15} {'Optimized':<15} {'Better':<10}", flush=True)
    print("-"*52, flush=True)
    
    orig = all_results['Original (SKILL.md)']
    opt = all_results['Optimized (ZZ=3)']
    
    for asset in sorted(FILES_4H.keys()):
        o = orig.get(asset, {'total': 0, 'wins': 0, 'wr': 0})
        p = opt.get(asset, {'total': 0, 'wins': 0, 'wr': 0})
        
        o_str = f"{o['wins']}/{o['total']}={o['wr']:.0f}%" if o['total'] >= 2 else f"{o['total']}tr"
        p_str = f"{p['wins']}/{p['total']}={p['wr']:.0f}%" if p['total'] >= 2 else f"{p['total']}tr"
        
        if o['total'] >= 2 and p['total'] >= 2:
            better = "OPT" if p['wr'] > o['wr'] else "ORIG" if o['wr'] > p['wr'] else "SAME"
        elif p['total'] >= 2:
            better = "OPT"
        elif o['total'] >= 2:
            better = "ORIG"
        else:
            better = "-"
        
        print(f"{asset:<12} {o_str:<15} {p_str:<15} {better:<10}", flush=True)

if __name__ == '__main__':
    main()
