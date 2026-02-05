from tqdm.autonotebook import tqdm
import os
import pandas as pd
import yfinance as yf
from config.config import DIR_PRICE_DATA

def fetch_daily_data(ticker: str) -> pd.DataFrame:
    """
    Fetches daily historical stock data from Yahoo Finance and returns it as a pandas DataFrame.

    Args:
        ticker (str): The stock ticker symbol (e.g., 'AAPL').
        start_date (str): The start date for the data in 'YYYY-MM-DD' format.
        end_date (str): The end date for the data in 'YYYY-MM-DD' format.

    Returns:
        pd.DataFrame: A pandas DataFrame containing the OHLCV data, with a 'Date' column.
                      Returns an empty DataFrame if the download fails or no data is found.
    """
    try:
        df = yf.Ticker(ticker).history(period='max', auto_adjust=False)
        if df.shape[0] == 0:
            df = yf.Ticker(ticker).history(period='5y', auto_adjust=False)
        df.index = pd.to_datetime(df.index)
        df.index = df.index.tz_localize(None)
        df.rename(
            columns={
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Adj Close': 'adjclose',
                'Volume': 'volume',
                'Dividends': 'dividends',
                'Stock Splits': 'stock_splits',
                'Capital Gains': 'capital_gains',
            }, 
            inplace=True
        )
        
        return df

    except Exception as e:
        print(f"An error occurred while fetching data for {ticker}: {e}")
        return pd.DataFrame()



def load_all_tickers(ticker_list: list[str], current_date: str=None) -> dict[str, pd.DataFrame]:
    """
    Loads daily historical stock data for a list of tickers.

    Args:
        ticker_list (list[str]): A list of stock ticker symbols.
    Returns:
        dict[str, pd.DataFrame]: A dictionary mapping each ticker to its corresponding DataFrame.
    """

    # Set current date for file naming
    CURRENT_DATE = current_date if current_date else pd.Timestamp.now().strftime('%Y-%m-%d')


    price_data = dict()
    for ticker in tqdm(ticker_list, desc="Loading Ticker Data"):
        # Check if data already exists locally
        if os.path.exists(os.path.join(DIR_PRICE_DATA, f'{ticker}_{CURRENT_DATE}.csv')):
            df = pd.read_csv(os.path.join(DIR_PRICE_DATA, f'{ticker}_{CURRENT_DATE}.csv'), index_col=0, parse_dates=True)
        else:
            df = fetch_daily_data(ticker)
            # save data locally
            df.to_csv(os.path.join(DIR_PRICE_DATA, f'{ticker}_{CURRENT_DATE}.csv'))
        # delete old files for the same ticker
        for file in os.listdir(os.path.join(DIR_PRICE_DATA)):
            if file.startswith(ticker + '_') and not file.endswith(f'{CURRENT_DATE}.csv'):
                os.remove(os.path.join(DIR_PRICE_DATA, file))
        price_data[ticker] = df


    for ticker in price_data:
        print(ticker)
        print(f"start date: {price_data[ticker].index.to_list()[0]}")
        print(f"end date:   {price_data[ticker].index.to_list()[-1]}")
    
    return price_data