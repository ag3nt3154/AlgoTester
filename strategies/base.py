import backtrader as bt
import pandas as pd





class BaseStrategy(bt.Strategy):
    """Base class for all trading strategies"""
    params = (
        ('tickers', []),  # Tickers within portfolio
        ('price_data', {})
    )
    def __init__(self):
        self.portfolio_tracker = []
        self.cost_basis = {ticker: 0 for ticker in self.params.tickers}
        self.unrealized_pnl = {ticker: 0 for ticker in self.params.tickers}
        self.realized_pnl = {ticker: 0 for ticker in self.params.tickers}
        self.position_size = {ticker: 0 for ticker in self.params.tickers}
        self.position_value = {ticker: 0 for ticker in self.params.tickers}

    def _track_portfolio(self):
        """Track portfolio value and dividends"""
        dividends = 0
        # track dividends
        for ticker in self.params.tickers:
            data = self.getdatabyname(ticker)
            price_data = self.params.price_data[ticker]
            dividend_per_share = price_data.loc[price_data.index == pd.to_datetime(self.data.datetime.date()), 'dividends'].values[0]
            asset_dividends = dividend_per_share * self.getposition(data).size
            
            # print(f"dividends: {asset_dividends}")
            dividends += asset_dividends
            self.broker.add_cash(asset_dividends)

            self.unrealized_pnl[ticker] = (data.close[0] - self.cost_basis[ticker]) * self.getposition(data).size
            self.position_size[ticker] = self.getposition(data).size
            self.position_value[ticker] = data.close[0] * self.getposition(data).size

            

        portfolio_state = {
            "date": self.data.datetime.date(),
            "portfolio_value": self.broker.getvalue(),
            "dividends": dividends,
            **{f"cost_basis_{ticker}": self.cost_basis[ticker] for ticker in self.params.tickers},
            **{f"unrealized_pnl_{ticker}": self.unrealized_pnl[ticker] for ticker in self.params.tickers},
            **{f"realized_pnl_{ticker}": self.realized_pnl[ticker] for ticker in self.params.tickers},
            **{f"position_size_{ticker}": self.position_size[ticker] for ticker in self.params.tickers},
            **{f"position_value_{ticker}": self.position_value[ticker] for ticker in self.params.tickers},
        }
        self.portfolio_tracker.append(portfolio_state)
    

    def _submit_order(self, ticker, quantity, price):
        """Submit order to broker"""
        if quantity > 0:
            order = self.buy(data=self.getdatabyname(ticker), size=quantity, exectype=bt.Order.Market)
        else:
            order = self.sell(data=self.getdatabyname(ticker), size=-quantity, exectype=bt.Order.Market)
        
        # update cost basis
        current_cost_basis = self.cost_basis[ticker]
        current_position = self.getposition(self.getdatabyname(ticker)).size
        cost_basis = get_cost_basis(
            current_cost_basis=current_cost_basis,
            current_quantity=current_position,
            new_quantity=quantity,
            new_price=price,
        )
        self.cost_basis[ticker] = cost_basis

        # update realized PnL
        if current_position > 0 and quantity < 0:
            self.realized_pnl[ticker] += (price - current_cost_basis) * min(-quantity, current_position)
        elif current_position < 0 and quantity > 0:
            self.realized_pnl[ticker] += (current_cost_basis - price) * min(quantity, -current_position)
            
        
        return order


    def next(self):
        self._track_portfolio()




def get_cost_basis(current_cost_basis: float, current_quantity: float, new_quantity: float, new_price: float) -> tuple:
    """
    Calculate the new cost basis and quantity after adding to or reducing a position.
    Handles both long and short positions, as well as partial closes and direction reversals.

    Parameters:
        current_cost_basis (float): The current average cost basis of the position.
        current_quantity (float): The current quantity of shares in the position.
        new_quantity (float): The quantity of shares in the new order.
        new_price (float): The price per share of the new order.

    Returns:
        tuple: A tuple containing:
            - new_cost_basis (float): The new cost basis of the position.
            - new_quantity (float): The new quantity of shares in the position.
    """
    # Determine if the current position is long or short
    is_long = current_quantity > 0
    is_short = current_quantity < 0

    # Determine if the new order is in the same or opposite direction
    if (new_quantity > 0 and is_long) or (new_quantity < 0 and is_short):
        # Adding to the position (same direction)
        total_value = current_cost_basis * abs(current_quantity) + new_price * abs(new_quantity)
        total_quantity = abs(current_quantity) + abs(new_quantity)
        new_cost_basis = total_value / total_quantity

    else:
        # Partially closing or reversing the position
        if abs(new_quantity) <= abs(current_quantity):
            # Partially closing the position
            new_cost_basis = current_cost_basis  # Cost basis remains the same
        else:
            # Reversing the position (e.g., from long to short or vice versa)
            # Calculate the cost basis for the new position
            new_cost_basis = new_price  # New cost basis is the price of the new order


    return new_cost_basis