import numpy as np
from sklearn.model_selection import TimeSeriesSplit
from scipy.stats import percentileofscore
from scipy.optimize import nnls, lsq_linear
from scipy.stats import linregress

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
    


def constrained_linear_regression(X, y, fit_intercept=True, constrain_intercept=False):
    """
    Perform linear regression with non-negative coefficients.
    
    Parameters:
    X : array-like, shape (n_samples, n_features)
        Feature matrix.
    y : array-like, shape (n_samples,)
        Target vector.
    fit_intercept : bool, default=True
        Whether to fit an intercept term.
    constrain_intercept : bool, default=False
        Whether to constrain the intercept to be non-negative.
        Only relevant if fit_intercept=True.
        
    Returns:
    intercept : float
        Intercept term (0.0 if fit_intercept=False).
    coef : ndarray, shape (n_features,)
        Regression coefficients (non-negative).
    """
    X = np.array(X)
    y = np.array(y)
    
    if fit_intercept:
        # Add intercept column (all ones)
        A = np.column_stack([np.ones(X.shape[0]), X])
        n_features = X.shape[1]
        
        if constrain_intercept:
            # Use NNLS (all coefficients >= 0)
            coef_full, _ = nnls(A, y)
            intercept = coef_full[0]
            coef = coef_full[1:]
        else:
            # Set bounds: intercept unconstrained, others >= 0
            # Create bounds: (lower_bounds, upper_bounds) as arrays
            lb = [-np.inf] + [0] * n_features  # Intercept: -∞, features: 0
            ub = [np.inf] * (n_features + 1)   # All: +∞
            result = lsq_linear(A, y, bounds=(lb, ub))
            coef_full = result.x
            intercept = coef_full[0]
            coef = coef_full[1:]
    else:
        # No intercept; all coefficients >= 0
        coef, _ = nnls(X, y)
        intercept = 0.0
    
    return intercept, coef



def normalize_weights(weights):
    total_weight = sum(weights.values())
    normalized_weights = {ticker: weight / total_weight for ticker, weight in weights.items()}
    return normalized_weights

def gmean(arr):
    return np.exp(np.mean(np.log(arr)))

def hmean(arr):
    return 1 / np.mean(1 / arr)


def compute_r2(y):
    x = range(len(y))
    result = linregress(x, y)
    r_squared = result.rvalue ** 2
    return r_squared