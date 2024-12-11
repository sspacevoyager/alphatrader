# backtester.py

import pandas as pd
import numpy as np
from strategy import StrategyBase
from rmm import RiskManager
import logging

class Backtester:
    def __init__(
        self,
        strategy: StrategyBase,
        data: dict,  # Changed from pd.DataFrame to dict to match data structure
        risk_manager: RiskManager,
        trade_type: str = 'long',
        use_atr_exits: bool = False,
        disable_indicator_exits: bool = False,
        use_trailing_sl_tp: bool = False,
        slippage: float = 0.0,  # Slippage in fraction (e.g., 0.001 for 0.1%)
        commission_rate: float = 0.0  # Commission rate in fraction (e.g., 0.001 for 0.1%)
    ):
        """
        Initialize the Backtester.

        Args:
            strategy (StrategyBase): The strategy to test.
            data (dict): Market data for backtesting.
            risk_manager (RiskManager): Risk management configuration.
            trade_type (str): 'long', 'short', or 'both'.
            use_atr_exits (bool): Enable ATR-based exits (SL/TP).
            disable_indicator_exits (bool): Disable indicator-based exits.
            use_trailing_sl_tp (bool): Enable trailing SL/TP logic.
            slippage (float): Slippage as a fraction of price (e.g., 0.001 for 0.1%).
            commission_rate (float): Commission rate as a fraction of trade value.
        """
        self.strategy = strategy
        self.data = data
        self.risk_manager = risk_manager
        self.trade_history = []
        self.equity_curve = []
        self.initial_balance = risk_manager.account_balance
        self.current_balance = self.initial_balance
        self.trade_type = trade_type.lower()  # 'long', 'short', or 'both'
        self.use_atr_exits = use_atr_exits  # Enable ATR-based exits
        self.disable_indicator_exits = disable_indicator_exits  # Disable indicator-based exits
        self.use_trailing_sl_tp = use_trailing_sl_tp  # Enable trailing SL/TP logic
        self.slippage = slippage  # Slippage fraction
        self.commission_rate = commission_rate  # Commission rate fraction
        logging.info("Backtester initialized.")

    def run_backtest(self):
        """
        Run the backtest on the given strategy and data.
        """
        logging.info("Running backtest")
        data_with_signals = self.strategy.generate_signals(self.data)
        position = 0  # Positive for long, negative for short
        entry_price = 0
        stop_loss_price = None
        take_profit_price = None

        for index, row in data_with_signals.iterrows():
            signal = row['signal']
            atr = row['atr'] if 'atr' in row else None  # Handle missing ATR

            # Entry Logic
            if position == 0:
                if signal == 1 and self.trade_type in ['long', 'both']:
                    # Adjust entry price for slippage (slippage increases buy price)
                    entry_price = row['close'] * (1 + self.slippage)

                    # Set ATR-based SL/TP if enabled
                    if self.use_atr_exits and 'atr_sl' in row and 'atr_tp' in row:
                        stop_loss_price = row['atr_sl']
                        take_profit_price = row['atr_tp']
                    else:
                        # Define default stop-loss and take-profit prices
                        stop_loss_price = entry_price * 0.98  # 2% stop-loss
                        take_profit_price = entry_price * 1.02  # 2% take-profit

                    # Calculate position size
                    position_size = self.risk_manager.calculate_position_size(
                        entry_price, stop_loss_price, atr=atr
                    )

                    # Deduct entry commission
                    entry_commission = entry_price * position_size * self.commission_rate
                    self.current_balance -= entry_commission

                    position = position_size

                    self.trade_history.append({
                        'entry_date': index,
                        'entry_price': entry_price,
                        'position_size': position_size,
                        'stop_loss': stop_loss_price,
                        'take_profit': take_profit_price,
                        'exit_date': None,
                        'exit_price': None,
                        'exit_reason': None,
                        'trade_direction': 'long',
                        'commission': entry_commission,  # Entry commission
                        'pnl': 0
                    })
                    logging.info(f"Opened long position at {entry_price} on {index}")

            # Exit Logic
            elif position != 0:
                current_trade = self.trade_history[-1]
                exit_price = None
                exit_reason = None

                # ATR-based exits with trailing logic
                if self.use_atr_exits and stop_loss_price and take_profit_price:
                    if position > 0:  # Long position
                        # Update trailing SL/TP if enabled
                        if self.use_trailing_sl_tp and atr is not None:
                            new_trailing_stop = self.risk_manager.update_trailing_stop(
                                row['close'], atr, stop_loss_price, multiplier=1.5
                            )
                            if new_trailing_stop > stop_loss_price:
                                stop_loss_price = new_trailing_stop

                            new_trailing_tp = self.risk_manager.update_trailing_take_profit(
                                row['close'], atr, take_profit_price, multiplier=3.0
                            )
                            if new_trailing_tp < take_profit_price:
                                take_profit_price = new_trailing_tp

                        # Check for ATR or trailing SL/TP exits
                        if row['low'] <= stop_loss_price:
                            # Adjust exit price for slippage (slippage decreases sell price)
                            exit_price = stop_loss_price * (1 - self.slippage)
                            exit_reason = 'Trailing Stop Loss' if self.use_trailing_sl_tp else 'Stop Loss'
                        elif row['high'] >= take_profit_price:
                            # Adjust exit price for slippage (slippage decreases sell price)
                            exit_price = take_profit_price * (1 - self.slippage)
                            exit_reason = 'Trailing Take Profit' if self.use_trailing_sl_tp else 'Take Profit'

                # Indicator-based exits (if not disabled)
                if not self.disable_indicator_exits and signal == -1 and exit_price is None:
                    if position > 0:  # Long position
                        # Adjust exit price for slippage (slippage decreases sell price)
                        exit_price = row['close'] * (1 - self.slippage)
                        exit_reason = 'Strategy Exit'

                # Close the position if an exit condition is met
                if exit_price is not None:
                    # Calculate PnL
                    pnl = (exit_price - entry_price) * position

                    # Deduct exit commission
                    exit_commission = exit_price * position * self.commission_rate
                    self.current_balance += pnl
                    self.current_balance -= exit_commission

                    current_trade.update({
                        'exit_date': index,
                        'exit_price': exit_price,
                        'exit_reason': exit_reason,
                        'pnl': pnl - exit_commission,  # Net PnL after exit commission
                        'commission': current_trade['commission'] + exit_commission  # Total commission
                    })
                    logging.info(f"Closed position at {exit_price} on {index} due to {exit_reason}")

                    # Reset position and stops
                    position = 0
                    stop_loss_price = None
                    take_profit_price = None

                # Update equity curve at each time step
                self.equity_curve.append({'date': index, 'equity': self.current_balance})

            else:
                # Update equity curve even when no position is open
                self.equity_curve.append({'date': index, 'equity': self.current_balance})

    def calculate_performance(self) -> dict:
        """
        Calculate performance metrics for the backtest.
        """
        total_trades = len(self.trade_history)
        winning_trades = [trade for trade in self.trade_history if 'pnl' in trade and trade['pnl'] > 0]
        losing_trades = [trade for trade in self.trade_history if 'pnl' in trade and trade['pnl'] <= 0]
        total_return = ((self.current_balance - self.initial_balance) / self.initial_balance) * 100

        # Calculate Sharpe Ratio
        equity_curve_df = pd.DataFrame(self.equity_curve)
        equity_curve_df.set_index('date', inplace=True)
        equity_curve_df['returns'] = equity_curve_df['equity'].pct_change()

        # Adjust periods per year for hourly data
        periods_per_year = 365 * 24  # 8760 hours per year
        sharpe_ratio = (equity_curve_df['returns'].mean() / equity_curve_df['returns'].std()) * np.sqrt(periods_per_year) if equity_curve_df['returns'].std() != 0 else 0

        # Calculate Maximum Drawdown
        equity_curve_df['cum_max'] = equity_curve_df['equity'].cummax()
        equity_curve_df['drawdown'] = (equity_curve_df['equity'] - equity_curve_df['cum_max']) / equity_curve_df['cum_max']
        max_drawdown = equity_curve_df['drawdown'].min() * 100  # Expressed as percentage

        performance = {
            'Total Trades': total_trades,
            'Winning Trades': len(winning_trades),
            'Losing Trades': len(losing_trades),
            'Win Rate (%)': (len(winning_trades) / total_trades * 100) if total_trades > 0 else 0,
            'Total Return (%)': total_return,
            'Ending Balance': self.current_balance,
            'Sharpe Ratio': sharpe_ratio,
            'Max Drawdown (%)': max_drawdown
        }
        logging.info("Performance calculation complete.")
        return performance

    def get_trade_history(self) -> pd.DataFrame:
        """
        Get the trade history as a DataFrame.
        """
        return pd.DataFrame(self.trade_history)

    def get_equity_curve(self) -> pd.DataFrame:
        """
        Get the equity curve as a DataFrame.
        """
        return pd.DataFrame(self.equity_curve)
