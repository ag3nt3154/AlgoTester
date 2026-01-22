import numpy as np
import pandas as pd


def calculate_breakout(df, breakout_period=252, rebalance_period=21):
    """
    Calculate breakout signals based on max/min comparisons between two rolling windows.
    
    Args:
        df: DataFrame containing price data
        'close': Name of the price column
        breakout_period: Shorter window for potential breakout detection
        rebalance_period: Longer window for reference levels
    
    Returns:
        DataFrame with 'breakout' column containing signals (-1, 0, 1)
    """
    df = df.copy()
    # Convert periods to integers for safety
    breakout_period = int(breakout_period)
    rebalance_period = int(rebalance_period)
    
    # Calculate rolling max/min for both periods
    df['breakout_max'] = df['close'].rolling(breakout_period).max()
    df['rebalance_max'] = df['close'].rolling(rebalance_period).max()
    df['breakout_min'] = df['close'].rolling(breakout_period).min()
    df['rebalance_min'] = df['close'].rolling(rebalance_period).min()
    
    # Calculate breakout signals
    df['breakout_signal'] = np.where(
        df['breakout_max'] == df['rebalance_max'], 1,
        np.where(
            df['breakout_min'] == df['rebalance_min'], -1, 0
        )
    )
        
    return df['breakout_signal'].to_list()