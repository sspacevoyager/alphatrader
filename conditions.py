# conditions.py

import pandas as pd

def crossover(series1: pd.Series, series2: pd.Series) -> pd.Series:
    return (series1 > series2) & (series1.shift(1) <= series2.shift(1))

def crossunder(series1: pd.Series, series2: pd.Series) -> pd.Series:
    return (series1 < series2) & (series1.shift(1) >= series2.shift(1))

def above_threshold(series: pd.Series, threshold: float) -> pd.Series:
    return series > threshold

def below_threshold(series: pd.Series, threshold: float) -> pd.Series:
    return series < threshold

def is_overbought(rsi_series: pd.Series, overbought_level: float = 70) -> pd.Series:
    return rsi_series > overbought_level

def is_oversold(rsi_series: pd.Series, oversold_level: float = 30) -> pd.Series:
    return rsi_series < oversold_level
