import numpy as np
from sklearn.model_selection import TimeSeriesSplit
import numpy as np
from scipy.stats import percentileofscore

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




class PercentileScaler:
    """
    Scales data to [0, 1] based on percentiles of the fitted data.
    
    Methods:
        fit(X): Compute percentiles for scaling.
        transform(X): Scale data based on fitted percentiles.
        fit_transform(X): Fit and transform in one step.
    """
    
    def __init__(self):
        self.reference_values = None
    
    def fit(self, X):
        """
        Compute reference percentiles from input array X.
        
        Args:
            X (array-like): Input data to compute percentiles from.
        """
        X = np.asarray(X)
        self.reference_values = np.sort(X.flatten())  # Store sorted values for percentile calculation
        return self
    
    def transform(self, X):
        """
        Scale input values to [0, 1] based on fitted percentiles.
        
        Args:
            X (array-like or scalar): Values to transform.
            
        Returns:
            Scaled values in [0, 1].
        """
        if self.reference_values is None:
            raise ValueError("Scaler has not been fitted yet. Call fit() first.")
        
        X = np.asarray(X)
        is_scalar = np.isscalar(X)
        X = np.array([X]) if is_scalar else X
        
        # Calculate percentile for each value
        scaled = np.array([percentileofscore(self.reference_values, x, kind='mean') / 100.0 
                          for x in X.flatten()])
        
        if is_scalar:
            return scaled[0]
        return scaled.reshape(X.shape)
    
    def fit_transform(self, X):
        """Fit and transform in one step."""
        return self.fit(X).transform(X)