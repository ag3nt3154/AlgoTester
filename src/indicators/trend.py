import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score


def calculate_r2(df, period=21):
    """
    Calculate R2 given dataframe with close prices and period
    """
    df = df.copy()
    r2_arr = []
    for i in range(df.shape[0]):
        if i < period:
           r2_arr.append(np.nan)
        else:
            # r2 is the R2 error term for a linear regression of log prices
            # We fit a linear regression of the log prices over unit time and then calculate the R2 with sklearn r2_score
            # R2 denotes how closely the log prices follow a linear trend
            close_prices_arr = df[i - period: i]['close'].to_numpy()
            assert close_prices_arr.shape[0] == period
            log_prices_arr = np.log(close_prices_arr)
            model = LinearRegression()
            model.fit(np.arange(period).reshape(-1, 1), log_prices_arr)
            r2 = r2_score(log_prices_arr, model.predict(np.arange(period).reshape(-1, 1)))
            r2_arr.append(r2)
    
    return r2_arr


def calculate_supertrend(df, period=14, multiplier=3):
    """
    Calculate SuperTrend indicator
    Args:
        df: DataFrame with columns ['high', 'low', 'close']
        period: ATR period (default: 14)
        multiplier: ATR multiplier (default: 3)
    Returns:
        DataFrame with 'supertrend', 'direction', 'upper_band', 'lower_band' columns
    """
    df = df.copy()
    
    # Calculate HL2
    df['hl2'] = (df['high'] + df['low']) / 2
    
    # Calculate ATR
    df['tr'] = pd.concat([
        df['high'] - df['low'],
        abs(df['high'] - df['close'].shift()),
        abs(df['low'] - df['close'].shift())
    ], axis=1).max(axis=1)
    df['atr'] = df['tr'].rolling(period).mean()
    
    # Calculate basic bands
    df['basic_upper'] = df['hl2'] + multiplier * df['atr']
    df['basic_lower'] = df['hl2'] - multiplier * df['atr']
    
    # Initialize final bands
    df['upper_band'] = df['basic_upper']
    df['lower_band'] = df['basic_lower']
    df['supertrend'] = 0.0
    df['direction'] = 'down'  # Initial direction
    
    for i in range(1, len(df)):
        # Update upper band
        if (df['basic_upper'].iloc[i] < df['upper_band'].iloc[i-1]) or \
           (df['close'].iloc[i-1] > df['upper_band'].iloc[i-1]):
            df['upper_band'].iat[i] = df['basic_upper'].iloc[i]
        else:
            df['upper_band'].iat[i] = df['upper_band'].iloc[i-1]
            
        # Update lower band
        if (df['basic_lower'].iloc[i] > df['lower_band'].iloc[i-1]) or \
           (df['close'].iloc[i-1] < df['lower_band'].iloc[i-1]):
            df['lower_band'].iat[i] = df['basic_lower'].iloc[i]
        else:
            df['lower_band'].iat[i] = df['lower_band'].iloc[i-1]
            
        # Determine trend direction
        if df['close'].iloc[i] > df['upper_band'].iloc[i]:
            df['direction'].iat[i] = 'up'
        elif df['close'].iloc[i] < df['lower_band'].iloc[i]:
            df['direction'].iat[i] = 'down'
        else:
            df['direction'].iat[i] = df['direction'].iloc[i-1]
            
        # Set SuperTrend value
        df['supertrend'].iat[i] = (
            df['lower_band'].iloc[i] if df['direction'].iloc[i] == 'up'
            else df['upper_band'].iloc[i]
        )
    
    # Cleanup intermediate columns
    df.drop(['hl2', 'tr', 'basic_upper', 'basic_lower'], axis=1, inplace=True)
    return df