"""
Data Fetcher Module for Algotron Framework

Handles data acquisition from Yahoo Finance and FRED API with auto-update functionality.
"""

import os
import logging
from datetime import datetime, timedelta
import pandas as pd
from yahoo_fin import stock_info as si
import yfinance as yf
from fredapi import Fred
from config import FRED_API_KEY  # API key from configuration

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Path configuration
BASE_DIR = os.path.dirname(".")
DATA_RAW = os.path.join(BASE_DIR, "data", "raw")
PRICE_DIR = os.path.join(DATA_RAW, "price")
MACRO_DIR = os.path.join(DATA_RAW, "macro")
ARCHIVE_DIR = os.path.join(DATA_RAW, "price_archive")  # New archive directory

# Ensure directories exist
os.makedirs(PRICE_DIR, exist_ok=True)
os.makedirs(MACRO_DIR, exist_ok=True)
os.makedirs(ARCHIVE_DIR, exist_ok=True)

# Initialize FRED client
fred = Fred(api_key=FRED_API_KEY)

class YahooDataFetcher:
    """Class for fetching data from Yahoo Finance"""

    @staticmethod
    def fetch_data_with_yahoo_fin(ticker: str) -> pd.DataFrame:
        """Fetch OHLC data from Yahoo Finance"""
        
        logger.info(f"Fetching data for {ticker} with yahoo_fin")
        df = si.get_data(ticker)
        df = df.reset_index().rename(columns={"index": "Date"})
        df["Date"] = pd.to_datetime(df["Date"])
        df.index = df["Date"]
        df = get_dividends(df)
        return df

    
    @staticmethod
    def fetch_data_with_yfinance(ticker: str) -> pd.DataFrame:
        """Fetch OHLC data from Yahoo Finance using yfinance"""
        
        logger.info(f"Fetching data for {ticker} with yfinance")
        # Download historical data with yfinance
        df = yf.Ticker(ticker).history(period='max', auto_adjust=False)
        df.index = pd.to_datetime(df.index)
        df.rename(
            columns={
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Adj Close': 'adj_close',
                'Volume': 'volume',
                'Dividends': 'dividends',
                'Stock Splits': 'stock_splits',
            }, 
            inplace=True
        )
        return df
    
    
    def fetch_data_from_yahoo(self, ticker: str) -> pd.DataFrame:
        """Fetch OHLC data from Yahoo Finance"""

        try:
            df = self.fetch_data_with_yfinance(ticker)
            return df
        except:
            df = self.fetch_data_with_yahoo_fin(ticker)
            return df

    
    def load_price_data(self, tickers: list[str]):
        current_date = datetime.today().strftime('%Y%m%d')
        for ticker in tickers:
            # Fetch data
            df = self.fetch_data_from_yahoo(ticker)

            # Create new file
            file_name = f"{ticker}_{datetime.today().strftime('%Y%m%d')}.pkl"
            file_path = os.path.join(PRICE_DIR, file_name)

            df.to_pickle(file_path)
            

            # Check for existing files for this ticker
            existing_files = [f for f in os.listdir(PRICE_DIR) if f.startswith(ticker)]
            

            # Move existing files to archive
            for existing_file in existing_files:
                if current_date in existing_file:
                    continue
                old_path = os.path.join(PRICE_DIR, existing_file)
                archive_path = os.path.join(ARCHIVE_DIR, existing_file)
                
                # Remove older archive files for this ticker
                archive_files = [f for f in os.listdir(ARCHIVE_DIR) if f.startswith(ticker)]
                for archive_file in archive_files:
                    os.remove(os.path.join(ARCHIVE_DIR, archive_file))
                
                # Move current file to archive
                os.rename(old_path, archive_path)
                logger.info(f"Moved {existing_file} to archive")





def get_dividends(data: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate dividends based on the relationship between close and adjusted close prices.

    Parameters:
        data (pd.DataFrame): Input DataFrame with columns 'close' and 'adjclose'.

    Returns:
        pd.DataFrame: DataFrame with an additional 'dividends' column showing dividends for each day.
    """
    # Ensure required columns exist
    if not {'close', 'adjclose'}.issubset(data.columns):
        raise ValueError("Input DataFrame must contain 'close' and 'adjclose' columns.")

    # Calculate daily returns for close and adjclose
    close_returns = data['close'].pct_change()
    adjclose_returns = data['adjclose'].pct_change()

    # Calculate dividends using the formula:
    # (close[i] + dividend[i] - close[i-1]) / close[i-1] = (adjclose[i] - adjclose[i-1]) / adjclose[i-1]
    # Rearranged to solve for dividend[i]:
    # dividend[i] = close[i-1] * (adjclose_returns[i] - close_returns[i])
    data['dividends'] = data['close'].shift(1) * (adjclose_returns - close_returns)

    # Handle the first row (no previous close)
    data.loc[data.index[0], 'dividends'] = 0

    # Ensure dividends are non-negative
    data['dividends'] = data['dividends'].apply(lambda x: max(0, x))

    return data
