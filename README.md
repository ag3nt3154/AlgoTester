# AlgoTester: Algorithmic Trading Framework

The AlgoTester Trading Framework is a Python-based backtesting and trading strategy development platform. It provides a modular structure for implementing, testing, and optimizing trading strategies using historical price data. The framework is built on top of the backtrader library and includes utilities for data fetching, backtesting, and performance analysis.

## Project Structure
├── strategies/
│   ├── base.py                     # Base strategy class
│   ├── buy_hold.py                 # Buy-and-hold strategy
│   ├── static_allocation.py        # Static asset allocation strategy
│   └── trend_following.py          # Trend-following strategies
├── update_price_data.py            # Script to update price data
└── utils/
    ├── backtester.py               # Backtesting engine
    └── data_fetcher.py             # Data fetching utilities

## Key Features
1. Modular Strategy Design:
    - Strategies are implemented as Python classes inheriting from a base strategy class (BaseStrategy).
    - Supports multiple asset classes and portfolio-level strategies.
2. Backtesting Engine:
    - Built on backtrader for efficient backtesting.
    - Tracks portfolio performance, dividends, and position-level metrics.
3. Data Fetching:
    - Fetches historical price data from Yahoo Finance and macroeconomic data from FRED.
    - Automatically updates existing datasets.
4. Strategy Library:
    - Includes pre-built strategies such as:
    - Buy-and-Hold: Simple benchmark strategy.
    - Static Allocation: Fixed-weight portfolio allocation.
    - Trend Following: Momentum-based strategies with configurable lookback periods.
5. Performance Metrics:
    - Calculates key metrics such as CAGR, volatility, Sharpe ratio, and max drawdown.
    - Visualizes portfolio performance, drawdowns, and asset-level PnL.

## Getting Started

### Prerequisites
- Python 3.8+
- Required libraries: backtrader, pandas, numpy, matplotlib, yahoo_fin, fredapi

### Updating Price Data
To update price data for existing tickers or fetch new data:
```
python update_price_data.py --update  # Update existing data
python update_price_data.py --new-tickers AAPL MSFT  # Fetch new tickers
python update_price_data.py --new-macro SP500  # Fetch new macroeconomic data
```
### Running a Backtest
- Define a strategy in the strategies folder or use an existing one.
- Use the BackTester class in utils/backtester.py to run a backtest:
```
from utils.backtester import BackTester
from strategies.buy_hold import BuyHoldStrategy

# Load price data
price_data = {...}  # Dictionary of DataFrames with OHLCV data

# Initialize backtester
backtester = BackTester(price_data, cash=100000, commission=0.001)

# Add strategy
backtester.add_strategy(BuyHoldStrategy)

# Run backtest
metrics = backtester.backtest()

# Plot results
backtester.plot_results()
```

## Example Strategies
- Buy-and-Hold:
    - Allocates 100% of the portfolio to a single asset.
    - No rebalancing or trading.
- Static Allocation:
    - Allocates fixed weights to multiple assets.
    - Rebalances periodically (e.g., monthly).
- Trend Following:
    - Buys assets with positive momentum and sells assets with negative momentum.
    - Configurable lookback periods and weighting schemes.

## License
This project is licensed under the MIT License. See the LICENSE file for details.



## Development Plan & TODOs
- ~~Implement data_fetcher.py (Yahoo/FRED).~~
- ~~Add backtesting core with metrics/plots.~~
- ~~Create base_strategy.py with metrics/plots.~~
- ~~Add logging for backtest results.~~
- ~~Add buy and hold strategy.~~
- ~~Add static asset allocation strategy.~~
- ~~Add trend following strategy.~~
- ~~Add advanced trend following strategy.~~
- ~~Optuna hyperparameter optimization.~~
- Add live trading