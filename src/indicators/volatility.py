import pandas as pd
import numpy as np


def calculate_atr(df, period=14, high_col='high', low_col='low', close_col='close'):
    """
    Calculate the Average True Range (ATR) for a given DataFrame.

    Args:
        df: DataFrame containing price data
        period: ATR calculation period (default: 14)
        high_col: Name of the high price column
        low_col: Name of the low price column
        close_col: Name of the close price column

    Returns:
        DataFrame with 'TR' (True Range) and 'ATR' columns added
    """
    df = df.copy()
    # Calculate the previous close
    df['prev_close'] = df[close_col].shift(1)
    
    # Compute the three potential true ranges
    tr1 = df[high_col] - df[low_col]
    tr2 = (df[high_col] - df['prev_close']).abs()
    tr3 = (df[low_col] - df['prev_close']).abs()
    
    # Element-wise maximum of the three values gives the True Range (TR)
    df['TR'] = np.maximum(np.maximum(tr1, tr2), tr3)
    
    # Calculate the ATR using an exponential moving average (EMA) of TR
    df['ATR'] = df['TR'].ewm(span=period, adjust=False).mean()
    df['ATR'] = df['ATR'] / df['prev_close']
    
    return df['ATR'].to_list()


def calculate_forward_vol(df, period=21):
    """
    Calculate forward volatility given dataframe with close prices and period
    """
    df = df.copy()
    df['temp_ret'] = df['close'].pct_change()
    df['temp_vol'] = df['temp_ret'].rolling(period).apply(lambda x: np.std(x) * np.sqrt(252))
    df['temp_vol'] = df['temp_vol'].shift(-period + 1)
    return df['temp_vol'].to_list()