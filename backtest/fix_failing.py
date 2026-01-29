"""Find params that work for failing assets without breaking passing ones"""
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

# Load Daily
files = glob.glob(os.path.join(DATA_DIR, '*1D*.csv'))
data = {}
for f in list(set(files)):
    asset = get_asset_name(f)
    try:
        data[asset] = load_data(f)
    except:
        pass

print("="*60)
print("SEARCHING FOR UNIVERSAL PARAMS (RR=2.0)")
print("="*60)
print(f"Assets: {len(data)}")

best_coverage = 0
best_params = None
best_results = None

for zz in [3, 4, 5, 6, 8, 10]:
    for fib in [0.5, 0.618, 0.70, 0.786, 0.85, 0.9]:
        params = {'zigzag_depth': zz, 'fib_entry_level': fib, 'rr_ratio': 2.0}
        
        ok = 0
        valid = 0
        results = {}
        
        for asset, df in data.items():
            try:
                bt = ElliottICTBacktester(df, params)
                r = bt.run_backtest()
                trades = r.wins + r.losses
                if trades >= 2:
                    valid += 1
                    wr = r.win_rate
                    results[asset] = {'wr': wr, 'w': r.wins, 'l': r.losses}
                    if wr >= 85:
                        ok += 1
            except Exception as e:
                pass
        
        if valid >= 5:
            cov = ok / valid * 100
            if cov > best_coverage:
                best_coverage = cov
                best_params = params.copy()
                best_results = results.copy()
                
                passing = [a for a, r in results.items() if r['wr'] >= 85]
                failing = [(a, r['wr']) for a, r in results.items() if r['wr'] < 85]
                print(f"NEW BEST: zz={zz}, fib={fib} -> {cov:.0f}% ({ok}/{valid})")
                print(f"  Pass: {passing}")
                print(f"  Fail: {[(a, f'{wr:.0f}%') for a, wr in failing]}")

print(f"\n{'='*60}")
print(f"BEST: {best_coverage:.0f}% with {best_params}")
print(f"{'='*60}")

if best_results:
    print("\nAll results:")
    for a in sorted(best_results.keys()):
        r = best_results[a]
        status = "OK" if r['wr'] >= 85 else "FAIL"
        print(f"  {a:12s}: {r['w']:2d}W/{r['l']:2d}L = {r['wr']:5.1f}% [{status}]")
