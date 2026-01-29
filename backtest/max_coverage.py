"""Try to maximize coverage with fib=0.786, RR=1.5"""
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

def calculate_ema(df, period):
    return df['close'].ewm(span=period, adjust=False).mean()

def calculate_atr(df, period=14):
    high_low = df['high'] - df['low']
    high_close = abs(df['high'] - df['close'].shift())
    low_close = abs(df['low'] - df['close'].shift())
    tr = high_low.combine(high_close, max).combine(low_close, max)
    return tr.rolling(period).mean()

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

def backtest(df, params):
    zz = params['zz']
    rsi_max = params.get('rsi_max', 100)
    rsi_min = params.get('rsi_min', 0)
    use_ema = params.get('use_ema', False)
    ema_period = params.get('ema_period', 50)
    use_bullish = params.get('use_bullish', False)
    min_wave_pct = params.get('min_wave_pct', 0)
    fib_tolerance = params.get('fib_tolerance', 0.05)
    
    rsi = calculate_rsi(df)
    ema = calculate_ema(df, ema_period) if use_ema else None
    pivots = calculate_zigzag(df, zz)
    
    signals = []
    for i in range(2, len(pivots)):
        p0, p1, p2 = pivots[i-2], pivots[i-1], pivots[i]
        if p0['type'] == 'low' and p1['type'] == 'high' and p2['type'] == 'low':
            wave1_low, wave1_high = p0['val'], p1['val']
            wave1_pct = (wave1_high - wave1_low) / wave1_low * 100
            
            if wave1_pct < min_wave_pct:
                continue
            
            wave2_low = p2['val']
            fib_price = wave1_high - (wave1_high - wave1_low) * 0.786
            tolerance = (wave1_high - wave1_low) * fib_tolerance
            
            if abs(wave2_low - fib_price) <= tolerance:
                bar = p2['idx']
                
                # RSI filter
                if rsi.iloc[bar] > rsi_max or rsi.iloc[bar] < rsi_min:
                    continue
                
                # EMA filter
                if use_ema and df['close'].iloc[bar] < ema.iloc[bar]:
                    continue
                
                # Bullish candle filter
                if use_bullish and df['close'].iloc[bar] <= df['open'].iloc[bar]:
                    continue
                
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
print("MAXIMIZING COVERAGE (fib=0.786, RR=1.5)")
print("="*60)

best_cov = 0
best_params = None
best_ok = 0
best_valid = 0
best_list = []

# Extended grid search
for zz in [2, 3, 4, 5]:
    for rsi_max in [45, 50, 55, 60, 65, 70, 75, 100]:
        for rsi_min in [0, 20, 25, 30]:
            for min_wave in [0, 3, 5]:
                for fib_tol in [0.03, 0.05, 0.08, 0.10]:
                    for use_ema in [False, True]:
                        for use_bullish in [False, True]:
                            params = {
                                'zz': zz,
                                'rsi_max': rsi_max,
                                'rsi_min': rsi_min,
                                'min_wave_pct': min_wave,
                                'fib_tolerance': fib_tol,
                                'use_ema': use_ema,
                                'ema_period': 50,
                                'use_bullish': use_bullish
                            }
                            
                            ok, valid = 0, 0
                            ok_list = []
                            
                            for asset, df in data.items():
                                try:
                                    w, l = backtest(df, params)
                                    if w + l >= 2:
                                        valid += 1
                                        wr = w / (w + l) * 100
                                        if wr >= 85:
                                            ok += 1
                                            ok_list.append(asset)
                                except:
                                    pass
                            
                            if valid >= 5:
                                cov = ok / valid * 100
                                if cov > best_cov or (cov == best_cov and valid > best_valid):
                                    best_cov = cov
                                    best_params = params.copy()
                                    best_ok = ok
                                    best_valid = valid
                                    best_list = ok_list.copy()
                                    
                                    rsi_str = f"RSI {rsi_min}-{rsi_max}" if rsi_min > 0 else f"RSI<{rsi_max}"
                                    ema_str = "+EMA" if use_ema else ""
                                    bull_str = "+Bull" if use_bullish else ""
                                    wave_str = f"+Wave{min_wave}%" if min_wave > 0 else ""
                                    print(f"NEW: zz={zz}, {rsi_str}, tol={fib_tol}{ema_str}{bull_str}{wave_str}")
                                    print(f"     -> {cov:.0f}% ({ok}/{valid}): {ok_list}")

print()
print("="*60)
print(f"BEST: {best_cov:.0f}% ({best_ok}/{best_valid})")
print(f"Params: {best_params}")
print(f"Assets: {best_list}")
