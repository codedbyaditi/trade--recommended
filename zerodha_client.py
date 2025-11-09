"""
Simple Zerodha (Kite Connect) wrapper.

This module provides a minimal wrapper for fetching historical data using KiteConnect.
It contains placeholder instructions — the user must set API keys and generate an access token.
"""
from typing import Optional
import os
import pandas as pd

try:
    from kiteconnect import KiteConnect
except Exception:
    KiteConnect = None  # graceful fallback if package not installed


class ZerodhaClient:
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None, access_token: Optional[str] = None):
        api_key = api_key or os.getenv("ZERODHA_API_KEY")
        api_secret = api_secret or os.getenv("ZERODHA_API_SECRET")
        access_token = access_token or os.getenv("ZERODHA_ACCESS_TOKEN")

        if KiteConnect is None:
            raise RuntimeError("kiteconnect package not installed. Install with `pip install kiteconnect` to use Zerodha integration.")

        if not api_key or not api_secret:
            raise ValueError("API key and API secret are required for Zerodha. See README for instructions.")

        self.kite = KiteConnect(api_key=api_key)
        if access_token:
            self.kite.set_access_token(access_token)
        
        self._instruments = None

    def _fetch_instruments(self, exchange="NSE"):
        """Fetch instruments and cache them."""
        if self._instruments is None:
            self._instruments = self.kite.instruments(exchange)

    def get_instrument_token(self, symbol: str, exchange: str = "NSE") -> Optional[int]:
        """Find instrument token for a given symbol."""
        self._fetch_instruments(exchange)
        if self._instruments:
            for instrument in self._instruments:
                if instrument['tradingsymbol'] == symbol.upper():
                    return instrument['instrument_token']
        return None

    def get_historical(self, symbol: str, from_date: str, to_date: str, interval: str = "day", exchange: str = "NSE") -> pd.DataFrame:
        """Fetch historical OHLC data using KiteConnect.historical_data.
        
        Automatically looks up instrument token for the given symbol.
        Parameters should be in the format accepted by KiteConnect (dates in YYYY-MM-DD HH:MM:SS or YYYY-MM-DD).

        Returns pandas DataFrame with columns: ['date','open','high','low','close','volume']
        """
        instrument_token = self.get_instrument_token(symbol, exchange)
        if not instrument_token:
            raise ValueError(f"Could not find instrument token for symbol {symbol} on exchange {exchange}.")
            
        data = self.kite.historical_data(instrument_token, from_date, to_date, interval)
        df = pd.DataFrame(data)
        if not df.empty and "date" in df.columns:
            df = df.set_index(pd.to_datetime(df["date"]))
            # Ensure timezone is removed for consistency
            df.index = df.index.tz_localize(None)
        return df


# NOTE: KiteConnect uses instrument tokens for exchanges; the mapping from tradingsymbol to token is out of scope here.
# See KiteConnect docs for instrument token list and login/access-token generation flow.
