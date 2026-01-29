"""Optimize with fib=0.786 fixed"""
import os
import sys
sys.path.append(os.path.dirname(__file__))
from backtester import load_data, ElliottICTBacktester
import glob

DATA_DIR = r'C:\Users\danie\projects\elliott-wave-indicator\data'

def get_asset_name(filepath):
    fname = os.path.basename(filepath)
    for prefix in ['BATS_', 'BINANCE_', 'COINBASE_', 'FOREXCOM_']:
        if fname.startswith(prefix):
            return fname.split(',')[0].replace(prefix, '')
    if 'MNQ' in fname: return 'MNQ'
    if 'NQ' in fname: return 'NQ'
    return fname.split('_')[0]

files = glob.glob(os.path.join(DATA_DIR, '*1D*.csv'))
data = {}
for f in list(set(files)):
    asset = get_asset_name(f)
    try:
        data[asset] = load_data(f)
    except:
        pass

print("="*60)
print("OPTIMIZING WITH FIB=0.786 FIXED")
print("="*60)

best_cov = 0
best_params = None
best_results = None

# Wide grid search
for zz in [2, 3, 4, 5, 6, 8, 10, 12, 15]:
    for rr in [0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.5, 1.8, 2.0]:
        params = {'zigzag_depth': zz, 'fib_entry_level': 0.786, 'rr_ratio': rr}
        
        ok, valid = 0, 0
        results = {}
        
        for asset, df in data.items():
            try:
                r = ElliottICTBacktester(df, params).run_backtest()
                trades = r.wins + r.losses
                if trades >= 2:
                    valid += 1
                    results[asset] = {'wr': r.win_rate, 'w': r.wins, 'l': r.losses}
                    if r.win_rate >= 85:
                        ok += 1
            except:
                pass
        
        if valid >= 5:
            cov = ok / valid * 100
            if cov > best_cov:
                best_cov = cov
                best_params = params.copy()
                best_results = results.copy()
                passing = [a for a, r in results.items() if r['wr'] >= 85]
                print(f"NEW: zz={zz}, RR={rr} -> {cov:.0f}% ({ok}/{valid})")
                print(f"  Pass: {passing}")

print()
print("="*60)
print(f"BEST: {best_cov:.0f}% with zz={best_params['zigzag_depth']}, RR={best_params['rr_ratio']}")
print("="*60)

if best_results:
    print("\nAll results:")
    for a in sorted(best_results.keys()):
        r = best_results[a]
        s = "OK" if r['wr'] >= 85 else "FAIL"
        print(f"  {a:12s}: {r['w']:2d}W/{r['l']:2d}L = {r['wr']:5.1f}% [{s}]")
