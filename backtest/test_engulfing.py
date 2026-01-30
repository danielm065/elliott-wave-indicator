"""
Engulfing Pattern Strategy - known for decent win rates in trend
"""
import sys
sys.path.insert(0, r'C:\Users\danie\projects\elliott-wave-indicator\backtest')

import pandas as pd
import numpy as np
from pathlib import Path
from multiprocessing import Pool, cpu_count
from itertools import product

DATA_DIR = Path(r'C:\Users\danie\projects\elliott-wave-indicator\data')

FILES_1H = {
    'AMD': 'BATS_AMD, 60_2853d.csv',
    'ASTS': 'BATS_ASTS, 60_360b6.csv',
    'BA': 'BATS_BA, 60_a5067.csv',
    'CRWV': 'BATS_CRWV, 60_58712.csv',
    'GOOG': 'BATS_GOOG, 60_78270.csv',
    'HIMS': 'BATS_HIMS, 60_ea867.csv',
    'IBKR': 'BATS_IBKR, 60_ebbaf.csv',
    'INTC': 'BATS_INTC, 60_59380.csv',
    'KRNT': 'BATS_KRNT, 60_f5a05.csv',
    'MU': 'BATS_MU, 60_609b8.csv',
    'OSCR': 'BATS_OSCR, 60_092fb.csv',
    'PLTR': 'BATS_PLTR, 60_14b34.csv',
    'RKLB': 'BATS_RKLB, 60_ae005.csv',
    'TTWO': 'BATS_TTWO, 60_73235.csv',
    'ADAUSDT': 'BINANCE_ADAUSDT, 60_ee9e1.csv',
    'BTCUSDT': 'BINANCE_BTCUSDT, 60_b6ebd.csv',
    'ETHUSD': 'BINANCE_ETHUSD, 60_b3215.csv',
    'MNQ': 'MNQ_1H.csv',
    'SOLUSD': 'COINBASE_SOLUSD, 60_49536.csv',
    'USDILS': 'FOREXCOM_USDILS, 60_14147.csv',
}

def load_data(filepath: str) -> pd.DataFrame:
    df = pd.read_csv(filepath)
    df.columns = [str(c).lower() for c in df.columns]
    return df

print("Loading data...", flush=True)
DATA = {}
for asset, file in FILES_1H.items():
    path = DATA_DIR / file
    if path.exists():
        try:
            DATA[asset] = load_data(str(path))
        except:
            pass
print(f"Loaded {len(DATA)} assets", flush=True)

def is_bullish_engulfing(df, bar):
    """Check for bullish engulfing pattern"""
    if bar < 1:
        return False
    
    prev_open = df['open'].iloc[bar-1]
    prev_close = df['close'].iloc[bar-1]
    curr_open = df['open'].iloc[bar]
    curr_close = df['close'].iloc[bar]
    
    # Previous candle bearish, current bullish
    # Current body completely engulfs previous body
    return (prev_close < prev_open and  # prev bearish
            curr_close > curr_open and  # curr bullish
            curr_open <= prev_close and  # opens below prev close
            curr_close >= prev_open)  # closes above prev open

def test_engulfing(df, params):
    """Test engulfing strategy on dataframe"""
    ema_period = params['ema_period']
    rsi_period = params['rsi_period']
    rsi_max = params['rsi_max']
    sl_mult = params['sl_mult']
    signal_gap = params['signal_gap']
    rr_ratio = 1.0
    
    # Calculate indicators
    ema = df['close'].ewm(span=ema_period).mean()
    
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(rsi_period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(rsi_period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    signals = []
    last_bar = -signal_gap - 1
    
    for bar in range(ema_period + 5, len(df) - 1):
        if bar - last_bar <= signal_gap:
            continue
        
        # Trend filter
        if df['close'].iloc[bar] <= ema.iloc[bar]:
            continue
        
        # RSI filter
        if pd.isna(rsi.iloc[bar]) or rsi.iloc[bar] > rsi_max:
            continue
        
        # Pattern check
        if not is_bullish_engulfing(df, bar):
            continue
        
        entry = df['close'].iloc[bar]
        sl = df['low'].iloc[bar] * (1 - sl_mult)
        risk = entry - sl
        
        if risk <= 0:
            continue
        
        tp = entry + (risk * rr_ratio)
        signals.append({'bar': bar, 'entry': entry, 'tp': tp, 'sl': sl, 'result': 0})
        last_bar = bar
    
    # Process signals
    for signal in signals:
        for bar in range(signal['bar'] + 1, len(df)):
            if df['low'].iloc[bar] <= signal['sl']:
                signal['result'] = -1
                break
            if df['high'].iloc[bar] >= signal['tp']:
                signal['result'] = 1
                break
    
    wins = sum(1 for s in signals if s['result'] == 1)
    losses = sum(1 for s in signals if s['result'] == -1)
    total = wins + losses
    return total, wins, (wins/total*100) if total > 0 else 0

def test_combo(args):
    ema, rsi_p, rsi_max, sl_mult, gap = args
    params = {
        'ema_period': ema, 'rsi_period': rsi_p, 'rsi_max': rsi_max,
        'sl_mult': sl_mult, 'signal_gap': gap
    }
    
    results = {}
    for asset, df in DATA.items():
        total, wins, wr = test_engulfing(df, params)
        results[asset] = {'total': total, 'wins': wins, 'wr': wr}
    
    passing = sum(1 for r in results.values() if r['total'] >= 2 and r['wr'] >= 80)
    return (passing, args, results)

if __name__ == '__main__':
    EMA = [20, 30, 50]
    RSI_P = [14]
    RSI_MAX = [50, 60, 70]
    SL_MULT = [0.002, 0.005, 0.01]
    GAP = [3, 5, 7]
    
    combos = list(product(EMA, RSI_P, RSI_MAX, SL_MULT, GAP))
    print(f"Testing {len(combos)} Engulfing combos...", flush=True)
    
    best = {'passing': 0}
    with Pool(processes=cpu_count()) as pool:
        for i, (passing, args, results) in enumerate(pool.imap_unordered(test_combo, combos, chunksize=10)):
            if passing > best['passing']:
                best = {'passing': passing, 'args': args, 'results': results}
                print(f"  NEW BEST: {passing}/20 - EMA={args[0]}, RSI<{args[2]}, SL={args[3]}", flush=True)
    
    print(f"\n{'='*60}", flush=True)
    print(f"BEST ENGULFING: {best['passing']}/20", flush=True)
    print(f"Params: EMA={best['args'][0]}, RSI<{best['args'][2]}, SL_mult={best['args'][3]}", flush=True)
    
    if 'results' in best:
        passing_list = [f"{a}({r['wr']:.0f}%)" for a, r in best['results'].items() if r['total']>=2 and r['wr']>=80]
        failing_list = [f"{a}({r['wr']:.0f}%)" for a, r in best['results'].items() if r['total']>=2 and r['wr']<80]
        print(f"PASSING: {passing_list}", flush=True)
        print(f"FAILING: {failing_list}", flush=True)
