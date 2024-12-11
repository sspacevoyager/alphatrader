# rmm.py

class RiskManager:
    def __init__(self, account_balance: float, risk_per_trade: float = 0.01, dynamic_position_sizing: bool = False, max_position_size: float = None):
        self.account_balance = account_balance
        self.risk_per_trade = risk_per_trade
        self.dynamic_position_sizing = dynamic_position_sizing
        self.max_position_size = max_position_size  # New parameter for maximum position size

    def calculate_position_size(self, entry_price: float, stop_loss_price: float, atr: float = None) -> float:
        risk_amount = self.account_balance * self.risk_per_trade
        stop_loss_distance = abs(entry_price - stop_loss_price)

        if self.dynamic_position_sizing and atr is not None:
            # Inverse ATR for position sizing
            position_size = risk_amount * (entry_price / atr)
        else:
            # Original fixed position sizing
            position_size = risk_amount / stop_loss_distance if stop_loss_distance != 0 else 0

        # Apply maximum position size cap if set
        if self.max_position_size is not None:
            position_size = min(position_size, self.max_position_size)

        return position_size

    def apply_stop_loss(self, entry_price: float, atr_value: float, multiplier: float = 2.0, is_short: bool = False) -> float:
        if is_short:
            return entry_price + (atr_value * multiplier)
        else:
            return entry_price - (atr_value * multiplier)

    def apply_take_profit(self, entry_price: float, atr_value: float, multiplier: float = 2.0, is_short: bool = False) -> float:
        if is_short:
            return entry_price - (atr_value * multiplier)
        else:
            return entry_price + (atr_value * multiplier)

    def apply_trailing_stop(self, entry_price: float, atr_value: float, multiplier: float = 2.0, is_short: bool = False) -> float:
        if is_short:
            return entry_price + (atr_value * multiplier)
        else:
            return entry_price - (atr_value * multiplier)

    def update_trailing_stop(self, current_price: float, atr_value: float, current_trailing_stop: float, multiplier: float = 2.0, is_short: bool = False) -> float:
        if is_short:
            new_trailing_stop = current_price + (atr_value * multiplier)
            return min(new_trailing_stop, current_trailing_stop)
        else:
            new_trailing_stop = current_price - (atr_value * multiplier)
            return max(new_trailing_stop, current_trailing_stop)

    def update_trailing_take_profit(self, current_price: float, atr_value: float, current_trailing_tp: float, multiplier: float = 2.0, is_short: bool = False) -> float:
        """
        Update trailing take-profit based on the current price and ATR.
        """
        if is_short:
            new_trailing_tp = current_price - (atr_value * multiplier)
            return max(new_trailing_tp, current_trailing_tp)
        else:
            new_trailing_tp = current_price + (atr_value * multiplier)
            return min(new_trailing_tp, current_trailing_tp)
