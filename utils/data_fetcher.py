"""
Data Fetcher Module for Algotron Framework

Handles data acquisition from Yahoo Finance and FRED API with auto-update functionality.
"""

import os
import logging
from datetime import datetime, timedelta
import pandas as pd
from yahoo_fin import stock_info as si
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

# Ensure directories exist
os.makedirs(PRICE_DIR, exist_ok=True)
os.makedirs(MACRO_DIR, exist_ok=True)

# Initialize FRED client
fred = Fred(api_key=FRED_API_KEY)


class DataFetcher:
    """Main class handling data fetching and updating operations"""
    
    @staticmethod
    def get_last_date(file_path: str) -> datetime:
        """Get last available date from existing data file"""
        try:
            df = pd.read_csv(file_path, parse_dates=["Date"], nrows=1)
            return df["Date"].iloc[-1]
        except (FileNotFoundError, pd.errors.EmptyDataError, KeyError):
            return None

    @staticmethod
    def fetch_yahoo_data(ticker: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """Fetch OHLC data from Yahoo Finance"""
        try:
            logger.info(f"Fetching Yahoo data for {ticker}")
            df = si.get_data(ticker, start_date=start_date, end_date=end_date)
            df = df.reset_index().rename(columns={"index": "Date"})
            df["Date"] = pd.to_datetime(df["Date"])
            df = get_dividends(df)
            return df
        except Exception as e:
            logger.error(f"Error fetching {ticker}: {str(e)}")
            return pd.DataFrame()

    @staticmethod
    def fetch_fred_data(series_id: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """Fetch macroeconomic data from FRED"""
        try:
            logger.info(f"Fetching FRED data for {series_id}")
            series = fred.get_series(series_id, observation_start=start_date, observation_end=end_date)
            return series.reset_index().rename(columns={"index": "Date", 0: "Value"})
        except Exception as e:
            logger.error(f"Error fetching {series_id}: {str(e)}")
            return pd.DataFrame()

    def update_existing_data(self):
        """Update all existing datasets in raw directories"""
        self._update_price_data()
        self._update_macro_data()

    def _update_price_data(self):
        """Update existing price data files"""
        logger.info(f"Updating price data")
        for file in os.listdir(PRICE_DIR):
            if file.endswith(".csv"):
                ticker = file.split("_")[0]
                file_path = os.path.join(PRICE_DIR, file)
                self._update_dataset(ticker, file_path, "price")

    def _update_macro_data(self):
        """Update existing macroeconomic data files"""
        for file in os.listdir(MACRO_DIR):
            if file.endswith(".csv"):
                series_id = file.split("_")[0]
                file_path = os.path.join(MACRO_DIR, file)
                self._update_dataset(series_id, file_path, "macro")

    def _update_dataset(self, identifier: str, file_path: str, data_type: str):
        """Generic update function for both price and macro data"""
        last_date = self.get_last_date(file_path)
        start_date = (last_date + timedelta(days=1)).strftime("%Y-%m-%d") if last_date else None
        end_date = datetime.today().strftime("%Y-%m-%d")

        if data_type == "price":
            new_data = self.fetch_yahoo_data(identifier, start_date, end_date)
        else:
            new_data = self.fetch_fred_data(identifier, start_date, end_date)

        if not new_data.empty:
            # existing_data = pd.read_csv(file_path)
            # updated_data = pd.concat([existing_data, new_data], ignore_index=True)
            new_data.to_pickle(file_path)
            logger.info(f"Updated {identifier} with {len(new_data)} new records")

    def load_new_data(self, tickers: list = None, macro_series: list = None):
        """Load new datasets into raw directories"""
        if tickers:
            self._load_new_price_data(tickers)
        if macro_series:
            self._load_new_macro_data(macro_series)

    def _load_new_price_data(self, tickers: list):
        """Load new ticker data from Yahoo Finance"""
        for ticker in tickers:
            file_name = f"{ticker}_{datetime.today().strftime('%Y%m%d')}.pkl"
            file_path = os.path.join(PRICE_DIR, file_name)
            
            data = self.fetch_yahoo_data(ticker)
            if not data.empty:
                data.to_pickle(file_path)
                logger.info(f"Saved new price data: {file_path}")

    def _load_new_macro_data(self, macro_series: list):
        """Load new macroeconomic data from FRED"""
        for series_id in macro_series:
            file_name = f"{series_id}_{datetime.today().strftime('%Y%m%d')}.csv"
            file_path = os.path.join(MACRO_DIR, file_name)
            
            if not os.path.exists(file_path):
                data = self.fetch_fred_data(series_id)
                if not data.empty:
                    data.to_csv(file_path, index=False)
                    logger.info(f"Saved new macro data: {file_path}")


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
