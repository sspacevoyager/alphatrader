# optimize_strategy.py

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from optimizer import GridSearchOptimizer
from strategy import EMAMACDRSIStrategy
from data import DataManager
import logging
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def plot_heatmap(results_df, x_param, y_param, metric):
    """
    Plot heatmap of the optimization results.

    Args:
        results_df (pd.DataFrame): DataFrame containing optimization results.
        x_param (str): Parameter name to plot on the x-axis.
        y_param (str): Parameter name to plot on the y-axis.
        metric (str): Performance metric to visualize.
    """
    pivot_table = results_df.pivot(index=y_param, columns=x_param, values=metric)
    plt.figure(figsize=(12, 8))
    sns.heatmap(pivot_table, annot=True, fmt=".2f", cmap="viridis")
    plt.title(f"Optimization Heatmap: {metric}")
    plt.xlabel(x_param)
    plt.ylabel(y_param)
    plt.show()

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

        # Define parameter grid with 8 values for each multiplier
        atr_sl_multipliers = [i * 0.5 for i in range(1, 9)]  # [0.5, 1.0, ..., 4.0]
        atr_tp_multipliers = [i * 0.5 for i in range(1, 9)]  # [0.5, 1.0, ..., 4.0]

        param_grid = {
            'ema_period': [21],  # Fixed value
            'macd_fast_period': [12],  # Fixed value
            'macd_slow_period': [26],  # Fixed value
            'macd_signal_period': [9],  # Fixed value
            'rsi_period': [14],  # Fixed value
            'rsi_entry_level': [49],  # Fixed value
            'rsi_exit_level': [51],  # Fixed value
            'atr_period': [14],  # Fixed value
            'atr_sl_multiplier': atr_sl_multipliers,
            'atr_tp_multiplier': atr_tp_multipliers,
            'higher_tf': ['4h']  # Fixed value
        }

        # Risk management parameters
        risk_manager_params = {
            'account_balance': 10000,
            'risk_per_trade': 0.01,
            'dynamic_position_sizing': False
        }

        # Backtester parameters
        backtester_params = {
            'trade_type': 'long',
            'use_atr_exits': True,
            'disable_indicator_exits': True,
            'slippage': 0.001,
            'commission_rate': 0.0005
        }

        # Initialize optimizer
        optimizer = GridSearchOptimizer(
            strategy_class=EMAMACDRSIStrategy,
            data=clean_data,
            risk_manager_params=risk_manager_params,
            backtester_params=backtester_params
        )

        # Run optimization
        results_df = optimizer.optimize(param_grid, optimization_metric='Total Return (%)')

        # Find the best parameters
        best_result = results_df.sort_values(by='Total Return (%)', ascending=False).iloc[0]
        logging.info(f"\nBest parameters:\n{best_result}")

        # Save results to CSV
        results_df.to_csv('optimization_results.csv', index=False)

        # Plot heatmap of Total Return
        plot_heatmap(
            results_df,
            x_param='atr_sl_multiplier',
            y_param='atr_tp_multiplier',
            metric='Total Return (%)'
        )

        # Optionally, plot heatmap of Sharpe Ratio
        plot_heatmap(
            results_df,
            x_param='atr_sl_multiplier',
            y_param='atr_tp_multiplier',
            metric='Sharpe Ratio'
        )

    except ValueError as ve:
        logging.error(f"Validation error: {ve}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
