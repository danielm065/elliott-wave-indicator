"""Find best params per asset - check if each asset CAN pass with some params"""
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
print("FINDING BEST PARAMS PER ASSET (RR=2.0)")
print("="*60)

can_pass = []
cannot_pass = []

for asset, df in sorted(data.items()):
    best_wr = 0
    best_params = None
    best_trades = 0
    
    for zz in [2, 3, 4, 5, 6, 8, 10]:
        for fib in [0.5, 0.618, 0.7, 0.786, 0.85, 0.9, 0.95]:
            params = {'zigzag_depth': zz, 'fib_entry_level': fib, 'rr_ratio': 2.0}
            
            try:
                r = ElliottICTBacktester(df, params).run_backtest()
                trades = r.wins + r.losses
                
                if trades >= 2:
                    if r.win_rate > best_wr or (r.win_rate == best_wr and trades > best_trades):
                        best_wr = r.win_rate
                        best_params = params.copy()
                        best_trades = trades
            except:
                pass
    
    if best_params:
        status = "[OK]" if best_wr >= 85 else "[X]"
        print(f"{asset:12s}: Best {best_wr:.0f}% (zz={best_params['zigzag_depth']}, fib={best_params['fib_entry_level']}) [{status}]")
        
        if best_wr >= 85:
            can_pass.append((asset, best_params, best_wr))
        else:
            cannot_pass.append((asset, best_wr))
    else:
        print(f"{asset:12s}: No valid trades")
        cannot_pass.append((asset, 0))

print(f"\n{'='*60}")
print(f"SUMMARY")
print(f"{'='*60}")
print(f"Can pass with some params: {len(can_pass)}/{len(data)}")
print(f"Cannot pass with any params: {len(cannot_pass)}")

print("\nAssets that CAN pass:")
for asset, params, wr in can_pass:
    print(f"  {asset}: {wr:.0f}% with zz={params['zigzag_depth']}, fib={params['fib_entry_level']}")

print("\nAssets that CANNOT pass:")
for asset, wr in cannot_pass:
    print(f"  {asset}: best {wr:.0f}%")
