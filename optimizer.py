# optimizer.py

import itertools
import pandas as pd
from multiprocessing import Pool, cpu_count
import logging

class GridSearchOptimizer:
    def __init__(self, strategy_class, data, risk_manager_params, backtester_params):
        self.strategy_class = strategy_class
        self.data = data
        self.risk_manager_params = risk_manager_params
        self.backtester_params = backtester_params

    def optimize(self, param_grid, optimization_metric='Total Return (%)'):
        """
        Run grid search optimization with parallel processing.

        Args:
            param_grid (dict): Dictionary where keys are parameter names and values are lists of parameter values.
            optimization_metric (str): The performance metric to optimize.

        Returns:
            pd.DataFrame: DataFrame containing performance metrics for each parameter combination.
        """
        # Create a list of all parameter combinations
        keys = list(param_grid.keys())
        combinations = list(itertools.product(*param_grid.values()))
        total_combinations = len(combinations)
        logging.info(f"Total parameter combinations to test: {total_combinations}")

        # Prepare arguments for multiprocessing
        args_list = []
        for combination in combinations:
            params = dict(zip(keys, combination))
            args_list.append(params)

        # Use multiprocessing Pool
        with Pool(processes=cpu_count()) as pool:
            results = pool.map(self._run_backtest_wrapper, args_list)

        # Convert results to DataFrame
        results_df = pd.DataFrame(results)

        return results_df

    def _run_backtest_wrapper(self, params):
        """
        Wrapper function for running backtest with exception handling.

        Args:
            params (dict): Parameters for the strategy.

        Returns:
            dict: Dictionary containing parameters and performance metrics.
        """
        try:
            return self._run_backtest(params)
        except Exception as e:
            logging.error(f"Error with parameters {params}: {e}")
            # Return NaN for performance metrics if there is an error
            result = {**params}
            result.update({
                'Total Trades': float('nan'),
                'Winning Trades': float('nan'),
                'Losing Trades': float('nan'),
                'Win Rate (%)': float('nan'),
                'Total Return (%)': float('nan'),
                'Ending Balance': float('nan'),
                'Sharpe Ratio': float('nan'),
                'Max Drawdown (%)': float('nan'),
            })
            return result

    def _run_backtest(self, params):
        """
        Run a single backtest with the given parameters.

        Args:
            params (dict): Parameters for the strategy.

        Returns:
            dict: Dictionary containing parameters and performance metrics.
        """
        # Initialize strategy with current parameters
        strategy = self.strategy_class(params=params)

        # Initialize risk manager
        risk_manager = self._initialize_risk_manager()

        # Initialize backtester
        backtester = self._initialize_backtester(strategy, risk_manager)

        # Run backtest
        backtester.run_backtest()

        # Calculate performance
        performance = backtester.calculate_performance()

        # Store results
        result = {**params, **performance}

        return result

    def _initialize_risk_manager(self):
        """
        Initialize the RiskManager.

        Returns:
            RiskManager: An instance of the RiskManager.
        """
        from rmm import RiskManager
        return RiskManager(**self.risk_manager_params)

    def _initialize_backtester(self, strategy, risk_manager):
        """
        Initialize the Backtester.

        Args:
            strategy (StrategyBase): The trading strategy.
            risk_manager (RiskManager): The risk manager.

        Returns:
            Backtester: An instance of the Backtester.
        """
        from backtester import Backtester
        return Backtester(
            strategy=strategy,
            data=self.data,
            risk_manager=risk_manager,
            **self.backtester_params
        )
