"""Test mid-range RR values"""
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

print("Testing different RR values")
print("="*50)

for rr in [1.0, 1.1, 1.2, 1.25, 1.3, 1.4, 1.5]:
    best_cov = 0
    best_p = None
    
    for zz in [2, 3, 4, 5]:
        for fib in [0.618, 0.7, 0.786, 0.85, 0.9, 0.95]:
            params = {'zigzag_depth': zz, 'fib_entry_level': fib, 'rr_ratio': rr}
            ok, valid = 0, 0
            
            for df in data.values():
                try:
                    r = ElliottICTBacktester(df, params).run_backtest()
                    if r.wins + r.losses >= 2:
                        valid += 1
                        if r.win_rate >= 85:
                            ok += 1
                except:
                    pass
            
            if valid >= 5:
                cov = ok / valid * 100
                if cov > best_cov:
                    best_cov = cov
                    best_p = params
    
    if best_p:
        print(f"RR={rr}: {best_cov:.0f}% (zz={best_p['zigzag_depth']}, fib={best_p['fib_entry_level']})")
    else:
        print(f"RR={rr}: No valid results")
