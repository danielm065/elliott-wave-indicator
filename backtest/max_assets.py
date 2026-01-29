"""Maximize number of passing assets"""
import os
import sys
sys.path.append(os.path.dirname(__file__))
from backtester import load_data
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

print(f"Total assets: {len(data)}")
print(f"Assets: {sorted(data.keys())}")
print()

def calculate_rsi(df, period=14):
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_zigzag(df, depth):
    highs = df['high'].values
    lows = df['low'].values
    pivots = []
    last_pivot_type = None
    for i in range(depth, len(df) - depth):
        is_high = all(highs[i] >= highs[i-j] and highs[i] >= highs[i+j] for j in range(1, depth+1))
        is_low = all(lows[i] <= lows[i-j] and lows[i] <= lows[i+j] for j in range(1, depth+1))
        if is_high and last_pivot_type != 'high':
            pivots.append({'idx': i, 'type': 'high', 'val': highs[i]})
            last_pivot_type = 'high'
        elif is_low and last_pivot_type != 'low':
            pivots.append({'idx': i, 'type': 'low', 'val': lows[i]})
            last_pivot_type = 'low'
    return pivots

def backtest(df, zz, rsi_max, tol):
    rsi = calculate_rsi(df)
    pivots = calculate_zigzag(df, zz)
    signals = []
    for i in range(2, len(pivots)):
        p0, p1, p2 = pivots[i-2], pivots[i-1], pivots[i]
        if p0['type'] == 'low' and p1['type'] == 'high' and p2['type'] == 'low':
            wave1_low, wave1_high = p0['val'], p1['val']
            wave2_low = p2['val']
            fib_price = wave1_high - (wave1_high - wave1_low) * 0.786
            tolerance = (wave1_high - wave1_low) * tol
            if abs(wave2_low - fib_price) <= tolerance:
                bar = p2['idx']
                if rsi.iloc[bar] < rsi_max:
                    entry = df['close'].iloc[bar]
                    sl = wave1_low * 0.99
                    tp = entry + (entry - sl) * 1.5
                    signals.append({'bar': bar, 'sl': sl, 'tp': tp})
    wins, losses = 0, 0
    for sig in signals:
        for bar in range(sig['bar'] + 1, len(df)):
            if df['low'].iloc[bar] <= sig['sl']:
                losses += 1
                break
            if df['high'].iloc[bar] >= sig['tp']:
                wins += 1
                break
    return wins, losses

print("="*60)
print("MAXIMIZING # OF PASSING ASSETS (fib=0.786, RR=1.5)")
print("="*60)

best_ok = 0
best_params = None
best_list = []
best_valid = 0

# Wider grid
for zz in [2, 3, 4, 5, 6]:
    for rsi_max in [40, 45, 50, 55, 60, 65, 70, 75, 80]:
        for tol in [0.05, 0.08, 0.10, 0.12, 0.15, 0.18, 0.20]:
            ok = 0
            valid = 0
            ok_list = []
            
            for asset, df in data.items():
                try:
                    w, l = backtest(df, zz, rsi_max, tol)
                    if w + l >= 2:
                        valid += 1
                        wr = w / (w + l) * 100
                        if wr >= 85:
                            ok += 1
                            ok_list.append(asset)
                except:
                    pass
            
            if ok > best_ok:
                best_ok = ok
                best_params = {'zz': zz, 'rsi': rsi_max, 'tol': tol}
                best_list = ok_list.copy()
                best_valid = valid
                cov = ok/valid*100 if valid > 0 else 0
                print(f"NEW BEST: {ok} assets passing!")
                print(f"  Params: zz={zz}, RSI<{rsi_max}, tol={tol}")
                print(f"  Coverage: {cov:.0f}% ({ok}/{valid})")
                print(f"  Assets: {ok_list}")
                print()

print()
print("="*60)
print(f"BEST: {best_ok} assets passing")
print(f"Params: zz={best_params['zz']}, RSI<{best_params['rsi']}, tolerance={best_params['tol']}")
print(f"Coverage: {best_ok}/{best_valid} = {best_ok/best_valid*100:.0f}%")
print()
print("Passing assets:")
for a in sorted(best_list):
    print(f"  - {a}")
print()

# Show all assets status
print("="*60)
print("ALL ASSETS STATUS:")
print("="*60)
for asset in sorted(data.keys()):
    try:
        w, l = backtest(data[asset], best_params['zz'], best_params['rsi'], best_params['tol'])
        if w + l == 0:
            print(f"{asset:12s}: 0 signals")
        elif w + l == 1:
            print(f"{asset:12s}: 1 signal")
        else:
            wr = w/(w+l)*100
            s = 'OK' if wr >= 85 else 'FAIL'
            print(f"{asset:12s}: {w}W/{l}L = {wr:.0f}% [{s}]")
    except Exception as e:
        print(f"{asset:12s}: ERROR")
