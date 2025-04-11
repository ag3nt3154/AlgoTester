import pandas as pd
import numpy as np



def calculate_forward_returns(df, period=21):
    """
    Calculate forward returns given dataframe with close prices and period
    """
    df = df.copy()
    if 'close' not in df.columns:
        raise ValueError('close column not in dataframe')
    df['temp_returns'] = df['close'].rolling(period).apply(lambda x: (x.iloc[-1] - x.iloc[0]) / x.iloc[0])
    df['temp_forward_returns'] = df['temp_returns'].shift(-period)
    return df['temp_forward_returns'].to_list()


def calculate_binary_forward_returns(df, period=21):
    """
    Calculate binary forward returns given dataframe with close prices and period
    """
    arr = calculate_forward_returns(df, period)
    output_arr = []
    for i in arr:
        if i >= 0:
            output_arr.append(1)
        elif i < 0:
            output_arr.append(-1)
        else:
            output_arr.append(np.nan)
    return output_arr


def calculate_returns(df, period):
    """
    Calculate returns given dataframe with close prices and period
    """
    df = df.copy()
    df['ret'] = df['close'].rolling(period).apply(lambda x: (x[-1] - x[0]) / x[0])
    return df['ret'].to_list()


def calculate_binary_returns(df, period):
    """
    Calculate binary returns given dataframe with close prices and period
    """
    df = df.copy()
    arr = calculate_returns(df, period)
    output_arr = []
    for i in arr:
        if i >= 0:
            output_arr.append(1)
        elif i < 0:
            output_arr.append(-1)
        else:
            output_arr.append(np.nan)
    return output_arr


def calculate_MA_returns(df, period):
    df = df.copy()
    df['temp_MA'] = df['close'].rolling(period).mean()
    df['ret_MA'] = df['close'] - df['temp_MA']  
    return df['ret_MA'].to_list()


def calculate_binary_MA_returns(df, period):
    df = df.copy()
    arr = calculate_MA_returns(df, period)
    output_arr = []
    for i in arr:
        if i >= 0:
            output_arr.append(1)
        elif i < 0:
            output_arr.append(-1)
        else:
            output_arr.append(np.nan)
    return output_arr