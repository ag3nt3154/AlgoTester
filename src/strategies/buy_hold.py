from strategies.base import BaseStrategy

class BuyHoldStrategy(BaseStrategy):
    """Buy and hold strategy (100% SPY)"""
    
    def __init__(self):
        super().__init__()

    def next(self):
        super().next()
        target_position = int(self.broker.getvalue() / self.data.close[0])
        current_position = self.broker.getposition(self.data).size
        if target_position > current_position:
            self._submit_order(self.data._name, target_position - current_position, self.data.close[0])
        elif target_position < current_position:
            self._submit_order(self.data._name, target_position - current_position, self.data.close[0])