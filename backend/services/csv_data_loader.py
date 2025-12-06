"""
CSV Data Loader for Cryptocurrency Historical Prices

This module loads historical cryptocurrency data from a pre-downloaded CSV file
instead of making API calls to yfinance. This provides:
- Faster training (no API rate limits)
- More historical data (11+ years for major coins)
- Daily (1d) candles for better trend detection
- Consistent data source across all training runs
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import os

# Path to the CSV data file
CSV_DATA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "cryptocurrency-historical-prices-top-100-2025",
    "Crypto_historical_data.csv",
)

# Cache for loaded data to avoid re-reading the CSV multiple times
_data_cache: Optional[pd.DataFrame] = None


def get_csv_path() -> str:
    """Get the path to the CSV data file"""
    return CSV_DATA_PATH


def load_full_csv() -> pd.DataFrame:
    """
    Load the full CSV file into memory (cached)

    Returns:
        DataFrame with all cryptocurrency data
    """
    global _data_cache

    if _data_cache is not None:
        return _data_cache

    if not os.path.exists(CSV_DATA_PATH):
        raise FileNotFoundError(
            f"CSV data file not found at: {CSV_DATA_PATH}\n"
            "Please ensure the cryptocurrency historical data CSV is downloaded."
        )

    print(f"Loading CSV data from: {CSV_DATA_PATH}")

    # Read CSV with proper date parsing
    df = pd.read_csv(
        CSV_DATA_PATH,
        parse_dates=["Date"],
        dtype={
            "Open": float,
            "High": float,
            "Low": float,
            "Close": float,
            "Volume": float,
            "ticker": str,
            "name": str,
        },
    )

    # Remove timezone info if present and convert to datetime
    df["Date"] = pd.to_datetime(df["Date"]).dt.tz_localize(None)

    # Sort by ticker and date
    df = df.sort_values(["ticker", "Date"]).reset_index(drop=True)

    print(f"✅ Loaded {len(df):,} rows for {df['ticker'].nunique()} cryptocurrencies")

    _data_cache = df
    return df


def get_available_symbols() -> List[str]:
    """
    Get list of available cryptocurrency symbols in the CSV

    Returns:
        List of ticker symbols (e.g., ['BTC-USD', 'ETH-USD', ...])
    """
    df = load_full_csv()
    return sorted(df["ticker"].unique().tolist())


def get_symbol_data(
    symbol: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    days_back: Optional[int] = None,
) -> pd.DataFrame:
    """
    Get historical data for a specific symbol in yfinance-compatible format

    Args:
        symbol: Cryptocurrency ticker (e.g., 'BTC-USD')
        start_date: Start date for data range (optional)
        end_date: End date for data range (optional, defaults to latest available)
        days_back: Number of days to look back from end_date (alternative to start_date)

    Returns:
        DataFrame with columns: Open, High, Low, Close, Volume
        Index: DatetimeIndex (like yfinance output)
    """
    df = load_full_csv()

    # Filter by symbol
    symbol_data = df[df["ticker"] == symbol].copy()

    if len(symbol_data) == 0:
        raise ValueError(
            f"Symbol '{symbol}' not found in CSV data.\n"
            f"Available symbols: {', '.join(get_available_symbols()[:20])}..."
        )

    # Set date as index (like yfinance)
    symbol_data.set_index("Date", inplace=True)
    symbol_data.sort_index(inplace=True)

    # Apply date filters
    if end_date is None:
        end_date = symbol_data.index.max()

    if days_back is not None:
        start_date = end_date - timedelta(days=days_back)
    elif start_date is None:
        start_date = symbol_data.index.min()

    # Filter by date range
    symbol_data = symbol_data[
        (symbol_data.index >= start_date) & (symbol_data.index <= end_date)
    ]

    # Select only OHLCV columns (like yfinance format)
    result = symbol_data[["Open", "High", "Low", "Close", "Volume"]].copy()

    print(f"✅ Retrieved {len(result)} daily candles for {symbol}")
    print(f"   Date range: {result.index.min().date()} to {result.index.max().date()}")

    return result


def get_symbol_date_range(symbol: str) -> Dict:
    """
    Get the date range available for a symbol

    Args:
        symbol: Cryptocurrency ticker (e.g., 'BTC-USD')

    Returns:
        Dictionary with 'start_date', 'end_date', 'total_days', 'total_records'
    """
    df = load_full_csv()
    symbol_data = df[df["ticker"] == symbol]

    if len(symbol_data) == 0:
        raise ValueError(f"Symbol '{symbol}' not found in CSV data.")

    return {
        "symbol": symbol,
        "start_date": symbol_data["Date"].min(),
        "end_date": symbol_data["Date"].max(),
        "total_days": (symbol_data["Date"].max() - symbol_data["Date"].min()).days,
        "total_records": len(symbol_data),
    }


def get_multiple_symbols_data(
    symbols: List[str],
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    days_back: Optional[int] = None,
) -> Dict[str, pd.DataFrame]:
    """
    Get historical data for multiple symbols

    Args:
        symbols: List of cryptocurrency tickers
        start_date: Start date for data range
        end_date: End date for data range
        days_back: Number of days to look back

    Returns:
        Dictionary mapping symbol to DataFrame
    """
    result = {}
    for symbol in symbols:
        try:
            result[symbol] = get_symbol_data(
                symbol, start_date=start_date, end_date=end_date, days_back=days_back
            )
        except ValueError as e:
            print(f"⚠️  Warning: {e}")

    return result


def clear_cache():
    """Clear the data cache to free memory"""
    global _data_cache
    _data_cache = None
    print("✅ CSV data cache cleared")


# Convenience function matching yfinance API
def download(
    symbol: str,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    interval: str = "1d",
    progress: bool = False,
) -> pd.DataFrame:
    """
    Drop-in replacement for yfinance.download() that uses CSV data

    Note: interval parameter is ignored (CSV only has daily data)

    Args:
        symbol: Cryptocurrency ticker
        start: Start date
        end: End date
        interval: Ignored (data is daily)
        progress: Ignored

    Returns:
        DataFrame with OHLCV data
    """
    if interval != "1d":
        print(f"⚠️  Warning: CSV data only supports 1d interval, ignoring '{interval}'")

    return get_symbol_data(symbol, start_date=start, end_date=end)


if __name__ == "__main__":
    # Test the module
    print("Testing CSV Data Loader\n" + "=" * 50)

    # Get available symbols
    symbols = get_available_symbols()
    print(f"\nAvailable symbols ({len(symbols)} total):")
    print(symbols[:20])

    # Test loading BTC data
    print("\n" + "=" * 50)
    print("Testing BTC-USD data loading:")
    btc_data = get_symbol_data("BTC-USD")
    print(f"\nBTC-USD data shape: {btc_data.shape}")
    print(f"\nFirst 5 rows:\n{btc_data.head()}")
    print(f"\nLast 5 rows:\n{btc_data.tail()}")

    # Test date range
    print("\n" + "=" * 50)
    print("Date ranges for major coins:")
    for coin in ["BTC-USD", "ETH-USD", "SOL-USD"]:
        info = get_symbol_date_range(coin)
        print(
            f"{coin}: {info['start_date'].date()} to {info['end_date'].date()} ({info['total_records']} records)"
        )
