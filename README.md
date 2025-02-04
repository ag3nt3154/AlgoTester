# AlgoTester: Algorithmic Trading Framework

## Features
- Backtest strategies with customizable metrics/plots.
- Optimize parameters and resume from checkpoints.
- Live trading with simulated execution.


## Quick Start
- Data update:
``` python update_price_data.py --new-tickers SPY AAPL```
- Example Strategy
```python
class MovingAverageCross(bt.Strategy):
    params = (('fast', 10), ('slow', 30))
    def __init__(self):
        self.fast_ma = bt.ind.SMA(period=self.p.fast)
        self.slow_ma = bt.ind.SMA(period=self.p.slow)
    def next(self):
        if self.fast_ma > self.slow_ma:
            self.buy()
        elif self.fast_ma < self.slow_ma:
            self.sell()
```
- Backtest
```
bt = BackTester(price_data)
bt.add_strategy(YourStrategy)
results = bt.backtest()
print("Your Strategy Results:", {k: v for k, v in results.items() if k != 'returns'})
bt.plot_results()
```

## Development Plan & TODOs
- ~~Implement data_fetcher.py (Yahoo/FRED).~~
- ~~Add backtesting core with metrics/plots.~~
- ~~Create base_strategy.py with metrics/plots.~~
- ~~Add logging for backtest results.~~
- ~~Add buy and hold strategy.~~
- ~~Add static asset allocation strategy.~~
- ~~Add trend following strategy.~~
- ~~Add advanced trend following strategy.~~
- Optuna hyperparameter optimization.
- Add live trading