"""
Technical indicators: RSI, MACD, moving averages
"""
from typing import Tuple
import pandas as pd
import numpy as np


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Relative Strength Index (RSI).

    Args:
        series: Price series (typically close prices).
        period: Lookback period, default 14.

    Returns:
        pd.Series of RSI values aligned to input index.
    """
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ma_up = up.ewm(com=period - 1, adjust=False).mean()
    ma_down = down.ewm(com=period - 1, adjust=False).mean()
    rs = ma_up / ma_down
    rsi = 100 - (100 / (1 + rs))
    return rsi


def macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    """Calculate MACD, signal and histogram.

    Returns DataFrame with columns: macd, signal, hist
    """
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    hist = macd_line - signal_line
    df = pd.DataFrame({"macd": macd_line, "signal": signal_line, "hist": hist})
    return df


def moving_averages(series: pd.Series, short_window: int = 9, long_window: int = 21) -> pd.DataFrame:
    """Return short and long simple moving averages."""
    sma_short = series.rolling(window=short_window, min_periods=1).mean()
    sma_long = series.rolling(window=long_window, min_periods=1).mean()
    return pd.DataFrame({"sma_short": sma_short, "sma_long": sma_long})


def bollinger_bands(series: pd.Series, window: int = 20, num_std: int = 2) -> pd.DataFrame:
    """Calculate Bollinger Bands.

    Args:
        series: Price series.
        window: Moving average window, default 20.
        num_std: Number of standard deviations, default 2.

    Returns:
        pd.DataFrame with columns: 'bb_ma', 'bb_upper', 'bb_lower'.
    """
    rolling_mean = series.rolling(window=window).mean()
    rolling_std = series.rolling(window=window).std()
    upper_band = rolling_mean + (rolling_std * num_std)
    lower_band = rolling_mean - (rolling_std * num_std)
    return pd.DataFrame({'bb_ma': rolling_mean, 'bb_upper': upper_band, 'bb_lower': lower_band})


def generate_simple_signal(df: pd.DataFrame) -> str:
    """Generate a basic Buy/Sell/Hold suggestion based on RSI, MACD, SMA, and Bollinger Bands.

    Contract:
    - Inputs: DataFrame with columns 'close', and optionally 'rsi', 'macd', 'signal', 'sma_short', 'sma_long', 'bb_lower', 'bb_upper'
    - Output: one of 'BUY', 'SELL', 'HOLD' and reason string
    """
    close = df["close"].iloc[-1]
    rsi_val = df["rsi"].iloc[-1] if "rsi" in df.columns else 50
    macd_val = df["macd"].iloc[-1] if "macd" in df.columns else 0
    signal_val = df["signal"].iloc[-1] if "signal" in df.columns else 0
    sma_short = df["sma_short"].iloc[-1] if "sma_short" in df.columns else close
    sma_long = df["sma_long"].iloc[-1] if "sma_long" in df.columns else close

    reasons = []
    score = 0

    # RSI rules
    if "rsi" in df.columns:
        if rsi_val < 30:
            score += 1
            reasons.append(f"RSI is low ({rsi_val:.1f}), indicating oversold.")
        elif rsi_val > 70:
            score -= 1
            reasons.append(f"RSI is high ({rsi_val:.1f}), indicating overbought.")

    # MACD crossover
    if {"macd", "signal"}.issubset(df.columns) and len(df) >= 2:
        macd_prev_signal_prev = df["macd"].iloc[-2] - df["signal"].iloc[-2]
        macd_curr_signal_curr = macd_val - signal_val
        if macd_prev_signal_prev < 0 and macd_curr_signal_curr > 0:
            score += 1.5  # Strong signal
            reasons.append("MACD line crossed above the signal line (bullish crossover).")
        elif macd_prev_signal_prev > 0 and macd_curr_signal_curr < 0:
            score -= 1.5  # Strong signal
            reasons.append("MACD line crossed below the signal line (bearish crossover).")

    # SMA trend
    if {"sma_short", "sma_long"}.issubset(df.columns):
        if sma_short > sma_long:
            score += 0.5
            reasons.append("Short-term moving average is above the long-term (uptrend).")
        else:
            score -= 0.5
            reasons.append("Short-term moving average is below the long-term (downtrend).")

    # Bollinger Bands
    if {"bb_lower", "bb_upper"}.issubset(df.columns):
        if close < df["bb_lower"].iloc[-1]:
            score += 1
            reasons.append("Price is below the lower Bollinger Band (potential bounce).")
        elif close > df["bb_upper"].iloc[-1]:
            score -= 1
            reasons.append("Price is above the upper Bollinger Band (potential pullback).")

    # Decide
    if not reasons:
        return "HOLD", "Not enough indicator data to form a signal."
        
    if score >= 1.5:
        return "BUY", "; ".join(reasons)
    elif score <= -1.5:
        return "SELL", "; ".join(reasons)
    else:
        return "HOLD", "; ".join(reasons)
