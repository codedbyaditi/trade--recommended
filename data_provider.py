"""
Unified data provider: tries Zerodha (if configured), otherwise falls back to yfinance for demo mode.
"""
from typing import Optional
import os
import pandas as pd
from datetime import datetime, timedelta
import streamlit as st


def fetch_with_yfinance(symbol: str, period_days: int = 90, interval: str = "1d") -> pd.DataFrame:
    """Fallback data fetch using yfinance (no API keys required)."""
    try:
        import yfinance as yf
    except Exception as e:
        raise RuntimeError("yfinance not installed. Install requirements or configure Zerodha keys.") from e

    end = datetime.now()
    start = end - timedelta(days=period_days)
    ticker = yf.Ticker(symbol)
    df = ticker.history(start=start, end=end, interval=interval)
    if df.empty:
        return df
    # ensure columns: open, high, low, close, volume
    df = df.rename(columns={"Close": "close", "Open": "open", "High": "high", "Low": "low", "Volume": "volume"})
    # yfinance sometimes returns data with timezone, which can cause issues with plotly
    df.index = df.index.tz_localize(None)
    df = df[["open", "high", "low", "close", "volume"]]
    df.index.name = "date"
    return df


def fetch_data(symbol: str, period_days: int = 90, interval: str = "1d", use_zerodha: bool = True) -> pd.DataFrame:
    """Fetch historical OHLC data. If Zerodha is configured and use_zerodha True, attempt it; otherwise fallback to yfinance.

    Symbol semantics:
    - For Zerodha you may need to pass instrument token or exchange-specific identifier.
    - For yfinance, use ticker like 'AAPL' or 'RELIANCE.NS'.
    """
    if use_zerodha:
        try:
            from .zerodha_client import ZerodhaClient
            api_key = os.getenv("ZERODHA_API_KEY")
            api_secret = os.getenv("ZERODHA_API_SECRET")
            access_token = os.getenv("ZERODHA_ACCESS_TOKEN")
            if api_key and api_secret and access_token:
                client = ZerodhaClient(api_key=api_key, api_secret=api_secret, access_token=access_token)
                # basic date formatting
                end = datetime.now().strftime("%Y-%m-%d")
                start = (datetime.now() - timedelta(days=period_days)).strftime("%Y-%m-%d")
                df = client.get_historical(symbol, start, end, interval=interval)
                # Zerodha gives OHLC, let's ensure column names are consistent
                df = df.rename(columns={"date": "date", "open": "open", "high": "high", "low": "low", "close": "close", "volume": "volume"})
                return df
        except Exception as e:
            # fallback to yfinance with a gentle degradation
            st.warning(f"Could not fetch from Zerodha: {e}. Falling back to yfinance.")
            pass

    # fallback
    return fetch_with_yfinance(symbol, period_days=period_days, interval=interval)
