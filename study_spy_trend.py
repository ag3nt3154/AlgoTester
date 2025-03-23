import pandas as pd
import numpy as np
import datetime
from tqdm import tqdm
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.linear_model import LinearRegression
import lightgbm as lgb
import optuna
from utils.helpers import get_train_test_split, continuous_to_binary
from indicators.returns import calculate_binary_forward_returns, calculate_binary_returns, calculate_binary_MA_returns, calculate_forward_returns, calculate_returns, calculate_MA_returns
from indicators.breakout import calculate_breakout
from indicators.volatility import calculate_atr, calculate_forward_vol
from indicators.volume import calculate_rel_volume
from indicators.trend import calculate_r2
from sklearn.metrics import roc_curve, auc, accuracy_score, confusion_matrix, root_mean_squared_error
from utils.data_fetcher import YahooDataFetcher
from sklearn.preprocessing import StandardScaler
from strategies.base import PositionDrivenRebalanceStrategy
from utils.backtester import BackTester


def main(params):
    ##############################################################
    # Load data
    ##############################################################

    # Fetch data from yahoo finance
    if params['update_data']:
        # Current date
        current_date = datetime.datetime.now().date()
        current_date = current_date.strftime("%Y%m%d")

        # Fetch daily price data from Yahoo Finance
        fetcher = YahooDataFetcher()
        ticker_list = ['SPY', '^VIX']
        fetcher.load_price_data(tickers=ticker_list)
    else:
        current_date = params['data_date']

    # Load data from pickle files
    df_raw = pd.read_pickle(f'data/raw/price/SPY_{current_date}.pkl')
    df_vix = pd.read_pickle(f'data/raw/price/^VIX_{current_date}.pkl')
    df_data = df_raw.copy()


    ##############################################################
    # Calculate forward_volatility for forecasting
    ##############################################################

    # Forward Volatility
    df_data['vol_forward'] = calculate_forward_vol(df_data, period=params['forward_vol_forecast']['vol_forward_period'])



    ##############################################################
    # Calculate independent variables
    ##############################################################

    # Calculate returns
    for period in tqdm(params['time_periods'], desc='Returns'):
        df_data[f'ret_{period}'] = calculate_returns(df_data, period=period)

    # Calculate binary returns
    for period in tqdm(params['time_periods'], desc='Binary Returns'):
        df_data[f'ret_binary_{period}'] = calculate_binary_returns(df_data, period=period)

    # Calculate MA returns
    for period in tqdm(params['time_periods'], desc='MA Returns'):
        df_data[f'ret_MA_{period}'] = calculate_MA_returns(df_data, period=period)

    # Calculate binary MA returns
    for period in tqdm(params['time_periods'], desc='Binary MA Returns'):
        df_data[f'ret_binary_MA_{period}'] = calculate_binary_MA_returns(df_data, period=period)
    
    # Calculate ATR
    for period in tqdm(params['time_periods'], desc='ATR'):
        df_data[f'atr_{period}'] = calculate_atr(df_data, period=period)
    
    # Calculate relative volume
    for period in tqdm(params['time_periods'], desc='Relative Volume'):
        df_data[f'vol_relative_{period}'] = calculate_rel_volume(df_data, current_period=10, ref_period=period)
    
    # Calculate R2
    for period in tqdm(params['time_periods'], desc='R2'):
        df_data[f'r2_{period}'] = calculate_r2(df_data, period=period)

    # Calculate breakout
    for period in tqdm(params['time_periods'], desc='Breakout'):
        df_data[f'breakout_{period}'] = calculate_breakout(df_data, breakout_period=period, rebalance_period=21)

    # Calculate VIX
    df_data['vix'] = df_vix['close']



    ##############################################################
    # Preprocessing
    ##############################################################

    # Drop rows with NaN values
    df_data.dropna(inplace=True)

    # Convert to binary

    # Train-Test Split
    data = get_train_test_split(df_data, params['num_splits'])



    ##############################################################
    # General Strategy
    ##############################################################
    # Use vix, atr to forecast forward volatility
    # Use forecasted forward volatility to adjust position size and trend period
    # Use trend period as parameter for trend following indicators



    ###############################################################
    # Forward Volatility Forecasting
    ###############################################################
    # Use linear regression / least squares to forecast forward volatility
    # Variables = vix, atr, relative volume, r2

    # Define X and y variables
    y_vars = ['vol_forward']
    X_vars = params['forward_vol_forecast']['x_vars']    
    evaluation_arr = []
    for i in tqdm(range(len(data))):
        X_train = data[i]['train'][X_vars]
        y_train = data[i]['train'][y_vars]
        X_test = data[i]['test'][X_vars]
        y_test = data[i]['test'][y_vars]

        # Fit scaler
        scaler = StandardScaler()
        X_train = scaler.fit_transform(X_train)
        X_test = scaler.transform(X_test)

        # Fit the model
        model = LinearRegression()
        model.fit(X_train, y_train)

        # Evaluate the model on the test set
        y_pred = model.predict(X_test)
        y_pred = np.clip(y_pred, 0, None)
        error = root_mean_squared_error(y_test, y_pred)
        coefficients = model.coef_.flatten()
        intercept = model.intercept_

        # save the predictions, coefficients, and intercept for this split
        evaluation_arr.append((y_test, y_pred, error, coefficients, intercept))

        # save model and results
        data[i]['model'] = model
        data[i]['test']['forward_vol_pred'] = y_pred
        data[i]['train']['forward_vol_pred'] = np.clip(model.predict(X_train), 0, None)


    # Plot error for each split
    plt.plot(range(len(evaluation_arr)), [e[2] for e in evaluation_arr])
    plt.xlabel('Split')
    plt.ylabel('Mean Absolute Error')
    plt.savefig('./plots/forward_vol_forecast_error.png')
    

    # Plot scatter plot of true vs predicted values
    plt.figure(figsize=(10, 10))

    # Generate a sequence of colors from the 'viridis' colormap
    colors = plt.cm.viridis(np.linspace(0, 1, len(evaluation_arr)))
    for i in range(len(evaluation_arr)):
        y_test, y_pred = evaluation_arr[i][0], evaluation_arr[i][1]
        plt.scatter(y_test, y_pred, color=colors[i], label=f'Split {i+1}', alpha=0.5)  # Use viridis colormap
    plt.plot([y_train.min(), y_train.max()], [y_train.min(), y_train.max()], 'k--', lw=4)
    plt.xlabel('True Values')
    plt.ylabel('Predictions')
    plt.title('True Values vs Predictions')
    plt.legend()
    plt.savefig('./plots/forward_vol_forecast_scatter.png')


    # Plot the feature importance
    features = X_vars
    colors = ['green' if coef > 0 else 'red' for coef in coefficients]
    plt.figure(figsize=(10, 10))
    plt.barh(features, coefficients, color=colors)  # Vertical bar chart
    plt.xlabel('Coefficient')
    plt.ylabel('Features')
    plt.title('Feature Importance (Linear Regression Coefficients)')
    plt.savefig('./plots/forward_vol_forecast_feature_importance.png')


    ###############################################################
    # Trend following with adjustments from forward volatility
    ###############################################################
    # 1. use forward volatility to adjust position size
    #   - parameters (0 to 1, linear factor) 
    # 2. use forward volatility to adjust trend period -> split into 2 cases -> optimize the weights of each period for each case
    #   - split_threshold (numerical)

    trend_x_var = params['trend_following']['x_vars']

    # 

    # use optuna to optimize parameters for trend following strategy
    def study(trial):
        weights = []
        for t in params['time_periods']:
            w = trial.suggest_float(f'w_{t}', -1, 1)

        df = price_data[ticker]
        # Initialize backtester
        bt = BackTester({ticker: df})

        # Example 1: Buy and Hold
        bt.add_strategy(BuyHoldStrategy, tickers=[ticker], price_data={ticker: df})
        results = bt.backtest()
        print("Buy and Hold Results:", {k: v for k, v in results.items() if k != 'returns'})
        bt.plot_results()











if __name__ == '__main__':
    
    # Parameters
    PARAMS = {
        'data_date': '20250321',
        'update_data': False,
        'num_splits': 10,
        'num_optuna_trials': 100,
        'rebalance_period': 21,
        'time_periods': [21, 50, 100, 200, 252],
        'forward_vol_forecast': {
            'vol_forward_period': 252,
            'x_vars': [
                'atr_21', 'atr_50', 'atr_100', 'atr_200', 'atr_252', #'atr_500', 
                'r2_21', 'r2_50', 'r2_100', 'r2_200', 'r2_252', #'r2_500', 
                'vix'
            ],
        },
        'trend_following': {
            'x_vars': [
                'ret_21', 'ret_50', 'ret_100', 'ret_200', 'ret_252', #'ret_500',
                'ret_MA_21', 'ret_MA_50', 'ret_MA_100', 'ret_MA_200', 'ret_MA_252', #'ret_MA_500',
                'vix',
                'breakout_21', 'breakout_50', 'breakout_100', 'breakout_200', 'breakout_252', #'breakout_500',
            ],
        },
        
    }

    

    # Run the main function
    main(params=PARAMS)