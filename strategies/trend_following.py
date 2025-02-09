from strategies.base import BaseStrategy
import backtrader as bt


class TrendFollowingStrategy(BaseStrategy):
    """Trend following strategy with configurable lookback period"""
    
    params = (
        ('lookback', 21),  # Default 1-month lookback (21 trading days)
    )

    def __init__(self):
        super().__init__()
        self.returns = bt.indicators.PercentChange(self.data.close, period=self.p.lookback)

        
    def next(self):
        super().next()
        current_position = self.getposition(self.data).size
        if self.returns[0] > 0:
            target_position = self.broker.getvalue() / self.data.close[0]
            
        else:
            target_position = 0
        
        self._submit_order(self.data._name, target_position - current_position, self.data.close[0])


class DualLookbackTrendFollowing(BaseStrategy):
    """Trend following strategy with configurable lookback periods"""

    params = (
        ('fast_lookback', 21),  # Default 1-month lookback (21 trading days)
        ('slow_lookback', 50),  # Default 4-month lookback (50 trading days)
        ('rebound_fast_weight', 0.5),
        ('correction_fast_weight', 0.5),
    )

    def __init__(self):
        super().__init__()
        self.fast_returns = bt.indicators.PercentChange(self.data.close, period=self.p.fast_lookback)
        self.slow_returns = bt.indicators.PercentChange(self.data.close, period=self.p.slow_lookback)

    def next(self):
        super().next()

        current_position = self.getposition(self.data).size
        if self.fast_returns[0] >= 0:
            fast_position = 1
        else:
            fast_position = 0
        if self.slow_returns[0] >= 0:
            slow_position = 1
        else:
            slow_position = 0

        if self.fast_returns[0] >= 0 and self.slow_returns[0] < 0:
            target_position = (self.params.rebound_fast_weight * fast_position) + ((1 - self.params.rebound_fast_weight) * slow_position)
        elif self.fast_returns[0] < 0 and self.slow_returns[0] >= 0:
            target_position = (self.params.correction_fast_weight * fast_position) + ((1 - self.params.correction_fast_weight) * slow_position)
        else:
            target_position = fast_position

        target_position *= self.broker.getvalue() / self.data.close[0]

        self._submit_order(self.data._name, target_position - current_position, self.data.close[0])


class DualPeriodSMAStrategy(BaseStrategy):
    """Trend following strategy with configurable lookback periods"""
    params = (
        ('fast_lookback', 21),  # Default 1-month lookback (21 trading days)
        ('slow_lookback', 50),  # Default 4-month lookback (50 trading days)
        ('rebound_fast_weight', 0.5),
        ('correction_fast_weight', 0.5),
    )

    def __init__(self):
        super().__init__()
        
        self.fast_returns = bt.indicators.SMA(self.data.close, period=self.p.fast_lookback) - bt.indicators.SMA(self.data.close, period=self.p.slow_lookback)
        self.slow_returns = bt.indicators.SMA(self.data.close, period=self.p.slow_lookback) - self.data.close
        

    def next(self):
        super().next()

        current_position = self.getposition(self.data).size
        if self.fast_returns[0] >= 0:
            fast_position = 1
        else:
            fast_position = 0
        if self.slow_returns[0] >= 0:
            slow_position = 1
        else:
            slow_position = 0

        if self.fast_returns[0] >= 0 and self.slow_returns[0] < 0:
            target_position = (self.params.rebound_fast_weight * fast_position) + ((1 - self.params.rebound_fast_weight) * slow_position)
        elif self.fast_returns[0] < 0 and self.slow_returns[0] >= 0:
            target_position = (self.params.correction_fast_weight * fast_position) + ((1 - self.params.correction_fast_weight) * slow_position)
        else:
            target_position = fast_position

        target_position *= self.broker.getvalue() / self.data.close[0]

        self._submit_order(self.data._name, target_position - current_position, self.data.close[0])




class AdvancedTrendFollowingStrategy(BaseStrategy):
    """Trend following strategy with configurable lookback period"""

    params = (
        ('fast_lookback', {}),
        ('slow_lookback', {}),
        ('rebalance_period', 21),
        ('atr_period', 21),
        ('atr_smoothing', 0.5),
        ('correction_fast_weight', {}),
        ('rebound_fast_weight', {}),
        ('sma_trend_periods', (21, 252)),
    )

    def __init__(self):
        super().__init__()
        self.indicators = {}

        for ticker in self.params.tickers:
            data = self.getdatabyname(ticker)
            self.indicators[ticker] = {
                'fast_returns': bt.indicators.PercentChange(data.close, period=self.params.fast_lookback.get(ticker, 21)),
                'slow_returns': bt.indicators.PercentChange(data.close, period=self.params.slow_lookback.get(ticker, 252)),
                'atr': bt.indicators.AverageTrueRange(data, period=self.params.atr_period),
                'sma_trend': bt.indicators.SMA(data.close, period=self.params.sma_trend_periods[0]) - bt.indicators.SMA(data.close, period=self.params.sma_trend_periods[1]),
            }
        
        self.correction_fast_weight = self.params.correction_fast_weight
        self.rebound_fast_weight = self.params.rebound_fast_weight
        self.rebalance_day = 0

    def next(self):
        super().next()
        if self.rebalance_day % self.p.rebalance_period == 0:
            self.rebalance_portfolio()
        
        self.rebalance_day += 1

    def rebalance_portfolio(self):
        # print(f'------- rebalancing {self.data.datetime.date(0)} -------')
        
        # Get the total portfolio value
        portfolio_value = self.broker.getvalue()

        asset_atr_weights = self._calculate_atr_weights()
        # for ticker in self.params.tickers:
            # print(ticker, asset_atr_weights[ticker])

        for ticker in self.params.tickers:
            # print(ticker)
            data = self.getdatabyname(ticker)
            atr_weight = asset_atr_weights[ticker]

            
            fast_returns = self.indicators[ticker]['fast_returns'][0]
            slow_returns = self.indicators[ticker]['slow_returns'][0]

            # print('fast return', fast_returns)
            # print('slow return', slow_returns)

            if self.indicators[ticker]['sma_trend'][0] >= 0:
                long_target = 1
                short_target = 0
            else:
                long_target = 0
                short_target = -1

            # print('long short target', long_target, short_target)

            rebound_fast_weight = self.rebound_fast_weight.get(ticker, 0.5)
            correction_fast_weight = self.correction_fast_weight.get(ticker, 0.5)

            # print('target weights', rebound_fast_weight, correction_fast_weight)

            if fast_returns >= 0:
                if slow_returns >= 0:
                    # print('uptrend')
                    target_weight = long_target
                    # print('target weight', target_weight)
                else:
                    # print('rebound')
                    target_weight = (rebound_fast_weight * long_target + (1 - rebound_fast_weight) * short_target)
                    # print(f'target weight = ({rebound_fast_weight} * {long_target} + ({1 - rebound_fast_weight}) * {short_target}) = {target_weight}')
            else:
                if slow_returns < 0:
                    # print('downtrend')
                    target_weight = short_target
                    # print('target weight', target_weight)
                else:
                    # print('correction')
                    target_weight = (correction_fast_weight * short_target + (1 - correction_fast_weight) * long_target)
                    # print(f'target weight = ({correction_fast_weight} * {short_target} + ({1 - correction_fast_weight}) * {long_target}) = {target_weight}')
            
            
            target_weight = target_weight * atr_weight
            target_position = int(target_weight * portfolio_value / data.close[0])
            current_position = self.getposition(data).size

            # print(f'target position {target_position} - current position {current_position} = {target_position - current_position}')
            quantity = target_position - current_position
            self._submit_order(ticker, quantity, data.close[0])



    def _calculate_atr_weights(self):
        """Calculate the ATR-based weights for each asset"""

        asset_inverse_atr = {}
        asset_atr_weights = {}
        total_pnl = max(0, sum(self.unrealized_pnl.values()) + sum(self.realized_pnl.values())) + 1
        for ticker in self.params.tickers:
            # asset_inverse_atr[ticker] = (1 / self.indicators[ticker]['atr']) ** self.params.atr_smoothing
            # asset_inverse_atr[ticker] = (self.indicators[ticker]['atr']) ** self.params.atr_smoothing
            # asset_inverse_atr[ticker] = 1 ** self.params.atr_smoothing
            asset_inverse_atr[ticker] = max(0, (self.unrealized_pnl[ticker] + self.realized_pnl[ticker])) / total_pnl + 1
        
        for ticker in self.params.tickers:
            atr_weight = asset_inverse_atr[ticker] / sum(asset_inverse_atr.values())
            asset_atr_weights[ticker] = atr_weight
        return asset_atr_weights
            


class MovingAverageCrossoverStrategy(BaseStrategy):
    params = (
        ('short_window', 10),  # Short-term moving average window
        ('long_window', 50),   # Long-term moving average window
        ('rebalance_period', 21),  # Rebalance period in days
    )

    def __init__(self):
        super().__init__()
        self.sma_short = bt.indicators.SimpleMovingAverage(self.data.close, period=self.params.short_window)
        self.sma_long = bt.indicators.SimpleMovingAverage(self.data.close, period=self.params.long_window)
        self.rebalance_date = 0

        
    def next(self):
        super().next()

        # check if it's time to rebalance
        if self.rebalance_date % self.params.rebalance_period == 0:
            self.rebalance_date = 0

            # find current position
            current_position = self.getposition(self.data).size
            if self.sma_short[0] - self.sma_long[0] >= 0:
                target_position = self.broker.getvalue() / self.data.close[0]
            else:
                target_position = 0
            
            self._submit_order(self.data._name, target_position - current_position, self.data.close[0])
        
        self.rebalance_date += 1



class MultiAssetMovingAverageCrossoverStrategy(BaseStrategy):
    params = (
        ('ticker_list', []),
        ('short_window', 10),  # Short-term moving average window
        ('long_window', 50),   # Long-term moving average window
        ('rebalance_period', 21),  # Rebalance period in days
        ('weights', {}),  # ATR period
    )

    def __init__(self):
        super().__init__()
        self.sma_short = {}
        self.sma_long = {}

        for ticker in self.params.ticker_list:
            data = self.getdatabyname(ticker)
            self.sma_short[ticker] = bt.indicators.SimpleMovingAverage(data.close, period=self.params.short_window)
            self.sma_long[ticker] = bt.indicators.SimpleMovingAverage(data.close, period=self.params.long_window)

        self.rebalance_date = 0

    def next(self):
        super().next()
        # check if it's time to rebalance
        if self.rebalance_date % self.params.rebalance_period == 0:
            self.rebalance_date = 0
            self.rebalance()
        self.rebalance_date += 1
    

    def rebalance(self):

        current_value = self.broker.getvalue()
        # calculate weights based on inverse ATR
        weights = self.params.weights
        
        # normalize weights
        total_weight = sum(weights.values())
        for ticker in self.params.ticker_list:
            weights[ticker] /= total_weight
        
        # calculate target positions
        target_positions = {}
        for ticker in self.params.ticker_list:
            
            data = self.getdatabyname(ticker)
            current_position = self.getposition(data).size
            target_positions[ticker] = 0

            if self.sma_short[ticker][0] - self.sma_long[ticker][0] >= 0:
                target_positions[ticker] = 1
            target_positions[ticker] = target_positions[ticker] * weights[ticker] * current_value / data.close[0]

            difference = target_positions[ticker] - current_position
            if difference != 0:
                self._submit_order(ticker, difference, data.close[0])


class MAMACStrategy(BaseStrategy):
    params = (
        ('ticker_list', []),
        ('short_window', 21),  # Short-term moving average window
        ('long_window', 252),   # Long-term moving average window
        ('rebalance_period', 21),  # Rebalance period in days
        ('weights', {}),
    )

    def __init__(self):
        super().__init__()
        self.sma_short = {}
        self.sma_long = {}

        for ticker in self.params.ticker_list:
            data = self.getdatabyname(ticker)
            self.sma_short[ticker] = bt.indicators.SimpleMovingAverage(data.close, period=self.params.short_window)
            self.sma_long[ticker] = bt.indicators.SimpleMovingAverage(data.close, period=self.params.long_window)

        self.rebalance_date = 0

    def next(self):
        super().next()
        # check if it's time to rebalance
        if self.rebalance_date % self.params.rebalance_period == 0:
            self.rebalance_date = 0
            self.rebalance()
        self.rebalance_date += 1
    

    def rebalance(self):

        current_portfolio_value = self.broker.getvalue()
        # calculate weights based on inverse ATR
        weights = self.params.weights
        
        # normalize weights
        total_weight = sum(weights.values())
        for ticker in weights:
            weights[ticker] /= total_weight
    
        
        # calculate target positions
        target_values = {}
        target_sizes = {}
        for ticker in self.params.ticker_list:
            if ticker == "SHV": continue
            
            data = self.getdatabyname(ticker)
            current_position = self.getposition(data).size
            target_position = 0

            if self.sma_short[ticker][0] - self.sma_long[ticker][0] >= 0:
                target_position = 1
            target_values[ticker] = target_position * weights[ticker] * current_portfolio_value

            target_sizes[ticker] = target_values[ticker] / data.close[0]

            difference = target_sizes[ticker] - current_position
            if difference != 0:
                self._submit_order(ticker, difference, data.close[0])
            
        if 'SHV' in self.params.ticker_list:
            data = self.getdatabyname('SHV')
            current_position = self.getposition(data).size
            target_value = current_portfolio_value - sum(target_values.values())

            target_size = target_value / data.close[0]
            difference = target_size - current_position
            if difference != 0:
                self._submit_order('SHV', difference, data.close[0])
        

