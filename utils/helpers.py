import numpy as np
from sklearn.model_selection import TimeSeriesSplit

def continuous_to_binary(arr, parameter, mode='percentile'):
    """
    Convert a continuous variable to a binary variable based on the specified mode and parameter.

    Parameters:
    arr (numpy array): The input array of continuous values.
    parameter (float): The threshold or percentile value depending on the mode.
    mode (str): The mode of operation. Can be 'percentile' or 'limit'.

    Returns:
    numpy array: A binary array where values are 0 or 1 based on the specified mode.
    """
    if mode == 'percentile':
        # Calculate the specified percentile of the array
        threshold = np.percentile(arr, parameter)
        binary_arr = np.where(arr > threshold, 1, 0)
    elif mode == 'limit':
        # Use the parameter as the threshold
        binary_arr = np.where(arr > parameter, 1, 0)
    else:
        raise ValueError("Invalid mode. Mode must be 'percentile' or 'limit'.")

    return binary_arr


def get_train_test_split(df, n):
    """
    Train Test split using Time Series Split
    """
    df = df.copy()
    
    tscv = TimeSeriesSplit(n_splits=n)

    data = []
    # Perform the time series split
    for train_index, test_index in tscv.split(df):
        train_data = df.iloc[train_index]
        test_data = df.iloc[test_index]
        
        data.append({
            'train': train_data,
            'test': test_data,
        })
    
    return data