from abc import ABC, abstractmethod
import pandas as pd
import indicators
import conditions

class StrategyBase(ABC):
    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        pass

class EMAMACDRSIStrategy(StrategyBase):
    def __init__(self, params):
        self.params = params  # Dictionary of strategy parameters

    def generate_signals(self, data: dict) -> pd.DataFrame:
        # Extract parameters
        ema_period = self.params.get('ema_period', 9)
        macd_fast_period = self.params.get('macd_fast_period', 12)
        macd_slow_period = self.params.get('macd_slow_period', 26)
        macd_signal_period = self.params.get('macd_signal_period', 9)
        rsi_period = self.params.get('rsi_period', 14)
        rsi_entry_level = self.params.get('rsi_entry_level', 50)
        rsi_exit_level = self.params.get('rsi_exit_level', 51)
        atr_period = self.params.get('atr_period', 14)
        atr_sl_multiplier = self.params.get('atr_sl_multiplier', 2.0)
        atr_tp_multiplier = self.params.get('atr_tp_multiplier', 4.0)
        higher_tf = self.params.get('higher_tf', '4h')  # Higher timeframe

        # Calculate indicators on primary timeframe
        primary_data = data['1h']
        primary_data['ema'] = indicators.calculate_ema(primary_data['close'], period=ema_period)
        macd_primary = indicators.calculate_macd(
            primary_data['close'],
            fast_period=macd_fast_period,
            slow_period=macd_slow_period,
            signal_period=macd_signal_period
        )
        primary_data = primary_data.join(macd_primary)
        primary_data['rsi'] = indicators.calculate_rsi(primary_data['close'], period=rsi_period)
        primary_data['atr'] = indicators.calculate_atr(primary_data, period=atr_period)

        # Calculate indicators on higher timeframe
        higher_data = data[higher_tf]
        higher_data['ema'] = indicators.calculate_ema(higher_data['close'], period=ema_period)
        macd_higher = indicators.calculate_macd(
            higher_data['close'],
            fast_period=macd_fast_period,
            slow_period=macd_slow_period,
            signal_period=macd_signal_period
        )
        higher_data = higher_data.join(macd_higher)
        higher_data['rsi'] = indicators.calculate_rsi(higher_data['close'], period=rsi_period)

        # Drop rows with NaN values resulting from indicator calculations
        primary_data.dropna(inplace=True)
        higher_data.dropna(inplace=True)

        # Entry Conditions
        ema_condition = primary_data['close'] > primary_data['ema']
        higher_ema_condition = primary_data['close'] > higher_data['ema'].reindex(primary_data.index, method='ffill')

        macd_condition = (primary_data['MACD'] > primary_data['Signal']) & (primary_data['MACD'] > 0)
        higher_macd_condition = (higher_data['MACD'] > higher_data['Signal']).reindex(primary_data.index, method='ffill') & (higher_data['MACD'] > 0).reindex(primary_data.index, method='ffill')

        rsi_condition = primary_data['rsi'] > rsi_entry_level
        higher_rsi_condition = higher_data['rsi'].reindex(primary_data.index, method='ffill') > rsi_entry_level

        buy_signal = ema_condition & higher_ema_condition & macd_condition & higher_macd_condition & rsi_condition & higher_rsi_condition

        # Calculate ATR-based stop-loss and take-profit levels
        primary_data['atr_sl'] = primary_data['close'] - (primary_data['atr'] * atr_sl_multiplier)
        primary_data['atr_tp'] = primary_data['close'] + (primary_data['atr'] * atr_tp_multiplier)

        # Exit Conditions
        macd_exit_condition = conditions.crossunder(primary_data['MACD'], primary_data['Signal'])
        rsi_exit_condition = primary_data['rsi'] < rsi_exit_level

        sell_signal = macd_exit_condition | rsi_exit_condition

        # Generate signals
        primary_data['signal'] = 0
        primary_data.loc[buy_signal, 'signal'] = 1    # Buy
        primary_data.loc[sell_signal, 'signal'] = -1  # Sell

        return primary_data
