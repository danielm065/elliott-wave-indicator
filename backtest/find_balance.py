"""Find balance between coverage and win rate"""
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

def backtest(df, zz, rsi_max):
    rsi = calculate_rsi(df)
    pivots = calculate_zigzag(df, zz)
    
    signals = []
    for i in range(2, len(pivots)):
        p0, p1, p2 = pivots[i-2], pivots[i-1], pivots[i]
        if p0['type'] == 'low' and p1['type'] == 'high' and p2['type'] == 'low':
            wave1_low, wave1_high = p0['val'], p1['val']
            wave2_low = p2['val']
            fib_price = wave1_high - (wave1_high - wave1_low) * 0.786
            tolerance = (wave1_high - wave1_low) * 0.05
            
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
print("FINDING BEST BALANCE (fib=0.786, RR=1.5)")
print("="*60)
print("Looking for: high coverage + high win rate")
print()

results = []

for zz in [2, 3, 4, 5, 6, 8]:
    for rsi_max in [45, 50, 55, 60, 65, 70, 100]:
        ok, fail, valid = 0, 0, 0
        ok_list = []
        
        for asset, df in data.items():
            try:
                w, l = backtest(df, zz, rsi_max)
                if w + l >= 2:
                    valid += 1
                    wr = w / (w + l) * 100
                    if wr >= 85:
                        ok += 1
                        ok_list.append(asset)
                    else:
                        fail += 1
            except:
                pass
        
        if valid >= 3:
            cov = ok / valid * 100
            # Score = coverage * valid count (want both high coverage AND many assets)
            score = cov * valid
            results.append({
                'zz': zz,
                'rsi': rsi_max,
                'ok': ok,
                'valid': valid,
                'cov': cov,
                'score': score,
                'ok_list': ok_list
            })

# Sort by score
results.sort(key=lambda x: -x['score'])

print("Top 10 combinations (sorted by score = coverage * valid assets):")
print()
for i, r in enumerate(results[:10]):
    rsi_str = f"RSI<{r['rsi']}" if r['rsi'] < 100 else "no RSI"
    print(f"{i+1}. zz={r['zz']}, {rsi_str}: {r['cov']:.0f}% ({r['ok']}/{r['valid']}) score={r['score']:.0f}")
    print(f"   OK: {r['ok_list']}")
    print()
