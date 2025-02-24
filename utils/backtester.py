"""
Backtester Module for Algotron Framework
"""

import logging
import pickle
import itertools
from datetime import datetime
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import backtrader as bt
from backtrader import Cerebro

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BackTester:
    """Backtesting and optimization engine for trading strategies"""
    
    def __init__(self, price_data: dict, cash: float = 100000, commission: float = 0.001, margin: float = 0.01):
        """
        Initialize backtester
        :param data: Pandas DataFrame with DatetimeIndex and OHLCV columns
        :param cash: Initial portfolio value
        :param commission: Broker commission percentage
        """
        self.cerebro = Cerebro()
        self.price_data = price_data
        self.ticker_list = list(self.price_data.keys())
        for ticker in price_data:
            data = bt.feeds.PandasData(
                dataname=price_data[ticker],
                datetime=None,  # Use DataFrame index as datetime
                open='open',
                high='high',
                low='low',
                close='close',
                volume='volume',
                name=ticker,
            )
            self.cerebro.adddata(data)
        self.cerebro.broker.setcash(cash)
        self.cerebro.broker.setcommission(commission=commission, margin=margin)
        self.results = None
        self.optimization_results = []

    def add_strategy(self, strategy: bt.Strategy, **params):
        """Add trading strategy with parameters"""
        self.cerebro.addstrategy(strategy, **params)

    def backtest(self) -> dict:
        """Run backtest and return performance metrics"""
        self.results = self.cerebro.run()
        self.portfolio_tracker = pd.DataFrame(self.results[0].portfolio_tracker)
        self.portfolio_tracker.set_index('date', inplace=True)
        self.portfolio_tracker.index = pd.to_datetime(self.portfolio_tracker.index)
        self.portfolio_tracker['return'] = self.portfolio_tracker['portfolio_value'].pct_change()
        self.portfolio_tracker['cumulative_return'] = (self.portfolio_tracker['portfolio_value'] / self.portfolio_tracker['portfolio_value'].iloc[0] - 1)
        self.portfolio_tracker['drawdown'] = (self.portfolio_tracker['portfolio_value'].cummax() - self.portfolio_tracker['portfolio_value']) / self.portfolio_tracker['portfolio_value'].cummax()
        return self._calculate_metrics()

    def optimize_params(self, param_ranges: dict, max_combinations: int = 100):
        """
        Optimize strategy parameters using grid search
        :param param_ranges: Dictionary of parameter ranges {'param': [values]}
        :param max_combinations: Maximum number of parameter combinations to test
        """
        keys, values = zip(*param_ranges.items())
        combinations = list(itertools.product(*values))[:max_combinations]
        
        for i, combo in enumerate(combinations):
            params = dict(zip(keys, combo))
            logger.info(f"Testing combination {i+1}/{len(combinations)}: {params}")
            
            self.cerebro.optstrategy(
                self.cerebro.strats[0][0][0],  # Get first added strategy
                **params
            )
            
            results = self.cerebro.run(optreturn=True)
            metrics = self._process_optimization_results(results, params)
            self.optimization_results.append(metrics)
            
            self._save_checkpoint(metrics)

    def _calculate_metrics(self) -> dict:
        """Calculate performance metrics from backtest results"""
        portfolio_values = self.portfolio_tracker['portfolio_value'].to_list()
        # Calculate returns and metrics
        returns = self.portfolio_tracker['portfolio_value'].pct_change().dropna()
        returns = returns.to_frame('returns')
        cum_returns = (portfolio_values[-1] / portfolio_values[0]) - 1
        
        # Calculate metrics
        cagr = ((portfolio_values[-1] / portfolio_values[0]) ** (252 / len(portfolio_values)) - 1)
        
        volatility = returns['returns'].std() * np.sqrt(252)
        sharpe = cagr / volatility if volatility != 0 else 0
        
        max_drawdown = self.portfolio_tracker['drawdown'].max()
        
        return {
            'cagr': cagr,
            'volatility': volatility,
            'sharpe': sharpe,
            'max_drawdown': max_drawdown,
            'returns': returns,
            'cumulative_returns': cum_returns,
            # 'portfolio_values': portfolio_values
        }

    def _process_optimization_results(self, results, params: dict) -> dict:
        """Process optimization results and combine with parameters"""
        metrics = self._calculate_metrics()
        return {**params, **metrics}

    def _save_checkpoint(self, metrics: dict):
        """Save optimization checkpoint"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"checkpoint_{timestamp}.pkl"
        with open(filename, 'wb') as f:
            pickle.dump(metrics, f)
        logger.info(f"Saved checkpoint: {filename}")

    def plot_results(self):
        """Generate performance visualization plots"""
        if not self.results:
            raise ValueError("Run backtest first")
            
        fig, axs = plt.subplots(6 + len(self.price_data), 1, figsize=(20, 30 + len(self.price_data) * 5))
        
        # Portfolio Value
        axs[0].plot(self.portfolio_tracker.index, self.portfolio_tracker['portfolio_value'])
        axs[0].set_yscale('log')
        axs[0].set_title('Portfolio Value')

        # Cumulative Returns
        axs[1].plot(self.portfolio_tracker.index, self.portfolio_tracker['cumulative_return'] + 1, label='Portfolio cumulative return')
        if len(self.ticker_list) == 1:
            ticker = self.ticker_list[0]
            df_price = self.price_data[ticker]
            df_price = df_price.loc[df_price.index.isin(self.portfolio_tracker.index)].copy()
            axs[1].plot(df_price.index, df_price['adjclose'] / df_price['adjclose'].iloc[0], label='Asset cumulative return')
        axs[1].legend()
        axs[1].set_title('Cumulative Returns')
        
        # Drawdowns
        axs[2].plot(self.portfolio_tracker.index, self.portfolio_tracker['drawdown'])
        axs[2].set_title('Drawdowns')
        
        # Rolling 1-Month Volatility
        axs[3].plot(self.portfolio_tracker.index, self.portfolio_tracker['return'].rolling(21).std() * np.sqrt(252))
        axs[3].set_title('1-Month Volatility (Annualized)')
        
        # Individual Asset unrealized PnL
        for ticker in self.price_data:
            axs[4].plot(self.portfolio_tracker.index, self.portfolio_tracker[f'unrealized_pnl_{ticker}'], label=ticker)
        axs[4].legend()
        axs[4].set_title('Unrealized PnL')

        # Individual Asset realized PnL
        for ticker in self.price_data:
            axs[5].plot(self.portfolio_tracker.index, self.portfolio_tracker[f'realized_pnl_{ticker}'], label=ticker)
        axs[5].legend()
        axs[5].set_title('Realized PnL')

        # asset pnl vs asset price changes
        
        for i in range(len(self.ticker_list)):
            ticker = self.ticker_list[i]
            df_price = self.price_data[ticker]
            df_price = df_price.loc[df_price.index.isin(self.portfolio_tracker.index)].copy()
            axs_twin = axs[6 + i].twinx()
            axs_twin.plot(df_price.index, df_price['adjclose'], label=f'Price {ticker}', color='red')
            axs_twin.legend(loc='lower right')
            axs[6 + i].plot(self.portfolio_tracker.index, self.portfolio_tracker[f'unrealized_pnl_{ticker}'] + self.portfolio_tracker[f'realized_pnl_{ticker}'], label=f'PnL {ticker}')
            axs[6 + i].plot(self.portfolio_tracker.index, self.portfolio_tracker[f'realized_pnl_{ticker}'], label=f'realized PnL {ticker}')
            axs[6 + i].legend(loc='upper left')
            axs[6 + i].set_title(f'PnL {ticker}')

        plt.tight_layout()
        plt.show()

    def show_final_positions(self, current_capital: float, leverage: float = 1.0):
        """Show final positions"""
        print(f"Final Positions on date: {self.portfolio_tracker.index.to_list()[-1]}")
        portfolio_value = self.portfolio_tracker['portfolio_value'].iloc[-1]
        current_capital = current_capital * leverage
        for ticker in self.ticker_list:
            assert self.price_data[ticker].index.to_list()[-1] == self.portfolio_tracker.index.to_list()[-1]
            position_value = self.portfolio_tracker[f'position_value_{ticker}'].iloc[-1]
            position_weight = position_value / portfolio_value
            expected_position_size = int(position_weight * current_capital / self.price_data[ticker].iloc[-1]['close'])
            expected_position_value = expected_position_size * self.price_data[ticker].iloc[-1]['close']

            print(ticker)
            print(f"Position weight:    {position_weight * 100 :.2f}%")
            print(f"Expected size:      {expected_position_size}")
            print(f"Current price:      ${self.price_data[ticker].iloc[-1]['close']}")
            print(f"Position value:     ${expected_position_value:.2f}")
            
        