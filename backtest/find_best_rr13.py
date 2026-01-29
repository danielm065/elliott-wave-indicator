"""Find best params for RR=1.3"""
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

print("Deep search for RR=1.3")
print("="*50)

best_cov = 0
best_params = None
best_results = None

for zz in [2, 3, 4, 5, 6, 8, 10]:
    for fib in [0.382, 0.5, 0.55, 0.618, 0.65, 0.7, 0.75, 0.786, 0.82, 0.85, 0.88, 0.9, 0.92, 0.95]:
        params = {'zigzag_depth': zz, 'fib_entry_level': fib, 'rr_ratio': 1.3}
        ok, valid = 0, 0
        results = {}
        
        for asset, df in data.items():
            try:
                r = ElliottICTBacktester(df, params).run_backtest()
                if r.wins + r.losses >= 2:
                    valid += 1
                    results[asset] = r.win_rate
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
                passing = [a for a, wr in results.items() if wr >= 85]
                print(f"NEW: zz={zz}, fib={fib} -> {cov:.0f}% ({ok}/{valid})")
                print(f"  Pass: {passing}")

print()
print(f"BEST: {best_cov:.0f}% with zz={best_params['zigzag_depth']}, fib={best_params['fib_entry_level']}")
print()
print("Details:")
for a in sorted(best_results.keys()):
    wr = best_results[a]
    s = "OK" if wr >= 85 else "FAIL"
    print(f"  {a:10s}: {wr:.0f}% [{s}]")
