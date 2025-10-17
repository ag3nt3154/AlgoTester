import pandas as pd
import yfinance as yf
from datetime import datetime

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

if __name__ == '__main__':
    # Example usage:
    ticker_symbol = 'AAPL'
    start = '2020-01-01'
    end = datetime.now().strftime('%Y-%m-%d')

    print(f"Fetching data for {ticker_symbol} from {start} to {end}...")
    aapl_data = fetch_daily_data(ticker_symbol, start, end)

    if not aapl_data.empty:
        print("Successfully fetched data.")
        print(f"Total rows fetched: {len(aapl_data)}")
        print("Data fetching function is working correctly.")
