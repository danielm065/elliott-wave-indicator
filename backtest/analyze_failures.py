"""
Analyze why some assets fail - find patterns
"""
import sys
sys.path.insert(0, r'C:\Users\danie\projects\elliott-wave-indicator\backtest')

from backtester import ElliottICTBacktester, load_data
from pathlib import Path
import numpy as np

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

# Best uniform params for 1H
PARAMS = {
    'zz_depth': 3, 'fib_entry_level': 0.85, 'fib_tolerance': 0.1,
    'rsi_threshold': 30, 'signal_gap': 5, 'use_trend_filter': False,
    'use_volume_filter': True, 'use_rsi_filter': True,
    'rr_ratio': 1.0, 'zz_dev': 0.2, 'ema_period': 200,
}

print("Analyzing asset characteristics...\n")

results = []
for asset, file in FILES_1H.items():
    path = DATA_DIR / file
    if not path.exists():
        continue
    
    df = load_data(str(path))
    
    # Calculate characteristics
    returns = df['close'].pct_change().dropna()
    volatility = returns.std() * 100
    avg_volume = df['volume'].mean() if 'volume' in df.columns else 0
    price_range = (df['high'] - df['low']).mean() / df['close'].mean() * 100
    trend_strength = abs(df['close'].iloc[-1] / df['close'].iloc[0] - 1) * 100
    
    # Run backtest
    try:
        bt = ElliottICTBacktester(df, PARAMS)
        result = bt.run_backtest()
        total = result.wins + result.losses
        wr = result.win_rate if total > 0 else 0
        status = "PASS" if total >= 2 and wr >= 80 else "FAIL"
    except Exception as e:
        total, wr, status = 0, 0, "ERROR"
    
    results.append({
        'asset': asset,
        'status': status,
        'trades': total,
        'wr': wr,
        'volatility': volatility,
        'price_range': price_range,
        'trend': trend_strength,
        'bars': len(df)
    })

# Sort by status
results.sort(key=lambda x: (x['status'] != 'PASS', -x['wr']))

print(f"{'Asset':<10} {'Status':<6} {'Trades':<7} {'WR%':<6} {'Vol%':<8} {'Range%':<8} {'Trend%':<8} {'Bars'}")
print("=" * 80)

pass_vols = []
fail_vols = []
pass_ranges = []
fail_ranges = []

for r in results:
    print(f"{r['asset']:<10} {r['status']:<6} {r['trades']:<7} {r['wr']:<6.0f} {r['volatility']:<8.2f} {r['price_range']:<8.2f} {r['trend']:<8.1f} {r['bars']}")
    if r['status'] == 'PASS':
        pass_vols.append(r['volatility'])
        pass_ranges.append(r['price_range'])
    else:
        fail_vols.append(r['volatility'])
        fail_ranges.append(r['price_range'])

print("\n" + "=" * 80)
print("PATTERNS:")
print(f"  PASS avg volatility: {np.mean(pass_vols):.2f}%")
print(f"  FAIL avg volatility: {np.mean(fail_vols):.2f}%")
print(f"  PASS avg price range: {np.mean(pass_ranges):.2f}%")
print(f"  FAIL avg price range: {np.mean(fail_ranges):.2f}%")
