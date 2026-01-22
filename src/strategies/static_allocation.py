from strategies.base import BaseStrategy
import backtrader as bt


class StaticAllocationStrategy(BaseStrategy):
    """Static allocation strategy amongst multiple assets"""
    
    params = (
        ('rebalance_period', 21),  # Default 1-month rebalance period (21 trading days)
        ('weights', {}), # Default empty weights
    )

    def __init__(self):
        super().__init__()
        self.rebalance_day = 0  # Counter to track the rebalance period
        if len(self.params.weights) == 0:
            self.params.weights = {ticker: 1 / len(self.params.tickers) for ticker in self.params.tickers}
        
            
        

        
    def next(self):
        super().next()
        
        # Check if it's time to rebalance
        if self.rebalance_day % self.params.rebalance_period == 0:
            self.rebalance_portfolio()
        
        self.rebalance_day += 1
    
    def rebalance_portfolio(self):

        # Get the total portfolio value
        portfolio_value = self.broker.getvalue()
        

        for ticker in self.params.tickers:
            weight = self.params.weights.get(ticker, 0)
            if weight == 0:
                continue  # Skip if the weight is zero

            # Calculate the target position based on the portfolio value and weight
            data = self.getdatabyname(ticker)
            target_value = portfolio_value * weight
            target_size = int(target_value / data.close[0])
            current_size = self.broker.getposition(data).size

            # Calculate the quantity to buy or sell
            quantity = target_size - current_size

            # Submit the order
            self._submit_order(ticker, quantity, data.close[0])

