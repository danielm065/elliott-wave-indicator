"""Deep search for best params"""
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

print(f"Testing {len(data)} assets")
print("Deep search with more combinations...")

best_coverage = 0
best_params = None

# Wider grid
for zz in [2, 3, 4, 5, 6, 7, 8, 10, 12]:
    for fib in [0.382, 0.5, 0.55, 0.618, 0.65, 0.70, 0.75, 0.786, 0.82, 0.85, 0.88, 0.9, 0.95]:
        params = {'zigzag_depth': zz, 'fib_entry_level': fib, 'rr_ratio': 2.0}
        
        ok = 0
        valid = 0
        
        for asset, df in data.items():
            try:
                bt = ElliottICTBacktester(df, params)
                r = bt.run_backtest()
                trades = r.wins + r.losses
                if trades >= 2:
                    valid += 1
                    if r.win_rate >= 85:
                        ok += 1
            except:
                pass
        
        if valid >= 5:
            cov = ok / valid * 100
            if cov > best_coverage:
                best_coverage = cov
                best_params = params.copy()
                print(f"NEW BEST: zz={zz}, fib={fib} -> {cov:.0f}% ({ok}/{valid})")

print(f"\nFINAL BEST: {best_coverage:.0f}% with {best_params}")
