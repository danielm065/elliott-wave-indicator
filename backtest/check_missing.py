"""Check assets with few/no trades"""
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

# Check missing assets
missing = ['ADAUSDT', 'CRWV', 'GOOG', 'HIMS', 'KRNT', 'USDILS', 'BA', 'BTCUSDT', 'SOLUSD']
print('Checking assets with few/no trades (RR=1.3):')
print('='*60)

for asset in missing:
    if asset not in data:
        print(f'{asset}: No data')
        continue
    
    df = data[asset]
    best_trades = 0
    best_wr = 0
    best_p = None
    
    for zz in [2, 3, 4, 5, 6]:
        for fib in [0.5, 0.618, 0.7, 0.786, 0.85, 0.9]:
            params = {'zigzag_depth': zz, 'fib_entry_level': fib, 'rr_ratio': 1.3}
            try:
                r = ElliottICTBacktester(df, params).run_backtest()
                trades = r.wins + r.losses
                if trades > best_trades or (trades == best_trades and r.win_rate > best_wr):
                    best_trades = trades
                    best_wr = r.win_rate if trades >= 2 else 0
                    best_p = params
            except:
                pass
    
    if best_trades >= 2:
        status = 'OK' if best_wr >= 85 else 'FAIL'
        zz = best_p['zigzag_depth']
        fib = best_p['fib_entry_level']
        print(f'{asset:12s}: {best_trades} trades, {best_wr:.0f}% [{status}] (zz={zz}, fib={fib})')
    else:
        print(f'{asset:12s}: Max {best_trades} trades - NOT ENOUGH DATA')
