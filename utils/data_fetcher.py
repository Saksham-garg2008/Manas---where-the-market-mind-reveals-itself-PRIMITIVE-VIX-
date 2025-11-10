import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# -----------------------------
# Fetch data for Indian stocks
# -----------------------------
def get_stock_data(ticker: str, period: str = "6mo", interval: str = "1d") -> pd.DataFrame:
    """
    Fetch stock data from Yahoo Finance.
    Args:
        ticker (str): NSE ticker symbol, e.g., 'TCS.NS'
        period (str): time period (e.g. '1y', '6mo', '3mo')
        interval (str): data interval (e.g. '1d', '1h')
    Returns:
        pd.DataFrame: dataframe with Date, Open, High, Low, Close, Volume
    """
    df = yf.download(ticker, period=period, interval=interval, progress=False)
    df.reset_index(inplace=True)
    df.rename(columns={"Date": "date", "Open": "open", "High": "high", 
                       "Low": "low", "Close": "close", "Volume": "volume"}, inplace=True)
    return df
