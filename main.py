# run_strategy.py

from data import DataManager
from strategy import EMAMACDRSIStrategy
from rmm import RiskManager
from backtester import Backtester
import graphs
import logging
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    try:
        exchange_name = 'binance'
        data_manager = DataManager(exchange_name=exchange_name)
        pair = 'BTC/USDT'
        timeframes = ['1h', '4h']
        start_date = '2020-01-01'
        end_date = '2024-09-11'

        # Fetch and preprocess data for multiple timeframes
        raw_data = asyncio.run(data_manager.fetch_data(pair, timeframes, start_date, end_date))
        clean_data = {tf: data_manager.preprocess_data(raw_data[tf]) for tf in timeframes}

        # Validate data
        for tf in timeframes:
            if not data_manager.validate_data(clean_data[tf]):
                raise ValueError(f"Data validation failed for timeframe {tf}.")

        # Strategy parameters (you can adjust these as needed)
        strategy_params = {
            'ema_period': 21,
            'macd_fast_period': 12,
            'macd_slow_period': 26,
            'macd_signal_period': 9,
            'rsi_period': 14,
            'rsi_entry_level': 49,
            'rsi_exit_level': 51,
            'atr_period': 14,
            'atr_sl_multiplier': 2.0,  # Adjust as needed
            'atr_tp_multiplier': 4.0,  # Adjust as needed
            'higher_tf': '4h'
        }

        strategy = EMAMACDRSIStrategy(params=strategy_params)

        # Risk management setup
        account_balance = 10000
        risk_per_trade = 0.01
        dynamic_position_sizing = False  # Disable dynamic position sizing based on ATR
        risk_manager = RiskManager(
            account_balance=account_balance,
            risk_per_trade=risk_per_trade,
            dynamic_position_sizing=dynamic_position_sizing
        )

        # Slippage and commission settings
        slippage = 0.001  # 0.1% slippage
        commission_rate = 0.0005  # 0.05% commission per trade side

        # Initialize and run backtester with flexible exit logic
        backtester = Backtester(
            strategy=strategy,
            data=clean_data,
            risk_manager=risk_manager,
            trade_type='long',
            use_atr_exits=True,  # Enable ATR-based exits
            disable_indicator_exits=True,  # Completely disable MACD/RSI-based exits
            slippage=slippage,
            commission_rate=commission_rate
        )
        backtester.run_backtest()

        # Calculate and log performance metrics
        performance_metrics = backtester.calculate_performance()
        logging.info("\nPerformance Metrics:")
        for key, value in performance_metrics.items():
            logging.info(f"{key}: {value}")

        # Log trade history
        trade_history = backtester.get_trade_history()
        logging.info("\nTrade History:")
        logging.info(trade_history)

        # Plot results
        graphs.plot_price_chart(clean_data['1h'], trade_history)
        graphs.plot_equity_curve(backtester.get_equity_curve())
        graphs.plot_price_chart_with_equity(clean_data['1h'], trade_history, backtester.get_equity_curve())

    except ValueError as ve:
        logging.error(f"Validation error: {ve}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
