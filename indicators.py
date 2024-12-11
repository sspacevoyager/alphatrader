# indicators.py

import pandas as pd
import numpy as np

# SMA Calculation
def calculate_sma(data: pd.Series, period: int) -> pd.Series:
    return data.rolling(window=period).mean()

# EMA Calculation
def calculate_ema(data: pd.Series, period: int) -> pd.Series:
    return data.ewm(span=period, adjust=False).mean()

# RSI Calculation
def calculate_rsi(data: pd.Series, period: int) -> pd.Series:
    delta = data.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    average_gain = gain.rolling(window=period).mean()
    average_loss = loss.rolling(window=period).mean()
    rs = average_gain / average_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# MACD Calculation
def calculate_macd(data: pd.Series, fast_period=12, slow_period=26, signal_period=9) -> pd.DataFrame:
    ema_fast = calculate_ema(data, fast_period)
    ema_slow = calculate_ema(data, slow_period)
    macd_line = ema_fast - ema_slow
    signal_line = calculate_ema(macd_line, signal_period)
    histogram = macd_line - signal_line
    return pd.DataFrame({'MACD': macd_line, 'Signal': signal_line, 'Histogram': histogram})

# ATR Calculation
def calculate_atr(data: pd.DataFrame, period: int = 14) -> pd.Series:
    high_low = data['high'] - data['low']
    high_close = np.abs(data['high'] - data['close'].shift())
    low_close = np.abs(data['low'] - data['close'].shift())
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = true_range.rolling(window=period).mean()
    return atr

# ADX Calculation
def calculate_adx(data: pd.DataFrame, period: int = 14) -> pd.Series:
    high = data['high']
    low = data['low']
    close = data['close']

    plus_dm = high.diff()
    minus_dm = low.diff()

    plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0.0)
    minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0.0)

    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low - close.shift()).abs()
    ], axis=1).max(axis=1)

    atr = tr.rolling(window=period).mean()

    plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)

    dx = 100 * (abs(plus_di - minus_di) / (plus_di + minus_di))
    adx = dx.rolling(window=period).mean()

    return adx

# VWAP Calculation
def calculate_vwap(data: pd.DataFrame) -> pd.Series:
    typical_price = (data['high'] + data['low'] + data['close']) / 3
    cumulative_tp_vol = (typical_price * data['volume']).cumsum()
    cumulative_vol = data['volume'].cumsum()
    vwap = cumulative_tp_vol / cumulative_vol
    return vwap


