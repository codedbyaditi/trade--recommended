"""
Streamlit UI for the Automated Trade Recommendation System.

Usage:
  - Install requirements: pip install -r requirements.txt
  - Run: streamlit run app.py

The app uses Zerodha if configured via environment variables, otherwise falls back to yfinance for demo runs.
"""
import os
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

from indicators import rsi, macd, moving_averages, generate_simple_signal
from data_provider import fetch_data

st.set_page_config(page_title="Automated Trade Recommendation", layout="wide")

st.title("Automated Trade Recommendation System")

# Sidebar: configuration
st.sidebar.header("Data & Instrument")
use_zerodha = st.sidebar.checkbox("Use Zerodha (if configured)", value=False)
symbol = st.sidebar.text_input("Symbol / Ticker", value="AAPL")
period_days = st.sidebar.slider("History (days)", min_value=30, max_value=365, value=180, step=30)
interval = st.sidebar.selectbox("Interval", options=["1d", "1h", "1m"], index=0)

st.sidebar.header("Indicators")
show_rsi = st.sidebar.checkbox("RSI", True)
show_macd = st.sidebar.checkbox("MACD", True)
show_sma = st.sidebar.checkbox("SMA (short/long)", True)
show_bb = st.sidebar.checkbox("Bollinger Bands", True)

def run_analysis(symbol, period_days, interval, use_zerodha, show_rsi, show_macd, show_sma, show_bb):
    """Fetches data and displays the analysis and charts."""
    with st.spinner(f"Fetching data for {symbol}..."):
        try:
            df = fetch_data(symbol, period_days=period_days, interval=interval, use_zerodha=use_zerodha)
        except Exception as e:
            st.error(f"Failed to fetch data: {e}")
            st.stop()

    if df.empty:
        st.warning("No data returned. Check symbol and data provider configuration.")
        st.stop()

    # Ensure close exists
    if "close" not in df.columns:
        if "Close" in df.columns:
            df["close"] = df["Close"]
        else:
            st.error("No 'close' column in fetched data.")
            st.stop()

    df = df.sort_index()
    prices = df["close"].astype(float)

    # Compute indicators
    results = pd.DataFrame(index=prices.index)
    results["close"] = prices
    # Also need open, high, low for candlestick
    results = results.join(df[['open', 'high', 'low']])


    if show_rsi:
        results["rsi"] = rsi(prices)
    if show_macd:
        macd_df = macd(prices)
        results = results.join(macd_df)
    if show_sma:
        sma_df = moving_averages(prices)
        results = results.join(sma_df)
    if show_bb:
        from indicators import bollinger_bands
        bb_df = bollinger_bands(prices)
        results = results.join(bb_df)

    # Drop rows with NaNs for plotting convenience
    plot_df = results.dropna()

    if len(plot_df) < 2:
        st.warning("Not enough data to generate a signal after indicator calculation.")
        st.stop()

    # Generate suggestion
    suggestion, reason = generate_simple_signal(plot_df)

    # Layout: top KPIs and charts
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader(f"{symbol} — Last Close: {prices.iloc[-1]:.2f}")
        
        # Price chart
        fig_price = go.Figure()
        fig_price.add_trace(go.Candlestick(x=plot_df.index,
                                           open=plot_df['open'], high=plot_df['high'],
                                           low=plot_df['low'], close=plot_df['close'],
                                           name='Price'))
        if show_sma and "sma_short" in plot_df.columns:
            fig_price.add_trace(go.Scatter(x=plot_df.index, y=plot_df["sma_short"], name="SMA Short", line=dict(color="orange", width=1)))
            fig_price.add_trace(go.Scatter(x=plot_df.index, y=plot_df["sma_long"], name="SMA Long", line=dict(color="blue", width=1)))
        
        if show_bb and {"bb_upper", "bb_lower"}.issubset(plot_df.columns):
            fig_price.add_trace(go.Scatter(x=plot_df.index, y=plot_df['bb_upper'], name='BB Upper', line=dict(color='gray', width=1, dash='dash')))
            fig_price.add_trace(go.Scatter(x=plot_df.index, y=plot_df['bb_lower'], name='BB Lower', line=dict(color='gray', width=1, dash='dash')))

        fig_price.update_layout(title="Price and Overlays", xaxis_rangeslider_visible=False)
        st.plotly_chart(fig_price, use_container_width=True)

        # RSI chart
        if show_rsi and "rsi" in plot_df.columns:
            fig_rsi = go.Figure()
            fig_rsi.add_trace(go.Scatter(x=plot_df.index, y=plot_df["rsi"], name="RSI", line=dict(color="purple")))
            fig_rsi.update_layout(title="Relative Strength Index (RSI)", yaxis_title="RSI")
            fig_rsi.add_hline(y=70, line_dash="dash", line_color="red")
            fig_rsi.add_hline(y=30, line_dash="dash", line_color="green")
            st.plotly_chart(fig_rsi, use_container_width=True)

        # MACD chart
        if show_macd and {"macd", "signal"}.issubset(plot_df.columns):
            fig_macd = go.Figure()
            fig_macd.add_trace(go.Bar(x=plot_df.index, y=plot_df["hist"], name="MACD Hist", marker_color="gray"))
            fig_macd.add_trace(go.Scatter(x=plot_df.index, y=plot_df["macd"], name="MACD", line=dict(color="green")))
            fig_macd.add_trace(go.Scatter(x=plot_df.index, y=plot_df["signal"], name="Signal", line=dict(color="red")))
            fig_macd.update_layout(title="MACD")
            st.plotly_chart(fig_macd, use_container_width=True)

    with col2:
        st.metric("Suggestion", suggestion)
        st.write("Reason:")
        st.info(reason)

        st.markdown("---")
        st.write("Recent indicator values:")
        display_cols = [c for c in ["close", "rsi", "macd", "signal", "sma_short", "sma_long", "bb_lower", "bb_upper"] if c in plot_df.columns]
        st.dataframe(plot_df[display_cols].tail(5).style.format("{:.2f}"))

    st.session_state['analysis_complete'] = True

# --- Main App Logic ---

# Use session state to run analysis automatically on first load
if 'analysis_complete' not in st.session_state:
    st.session_state['analysis_complete'] = False

if st.sidebar.button("Fetch & Analyze", type="primary"):
    run_analysis(symbol, period_days, interval, use_zerodha, show_rsi, show_macd, show_sma, show_bb)
elif not st.session_state['analysis_complete']:
    # Automatically run for the default symbol on the first load
    run_analysis(symbol, period_days, interval, use_zerodha, show_rsi, show_macd, show_sma, show_bb)
else:
    st.info("Welcome! Change the settings in the sidebar and click 'Fetch & Analyze' to update the view.")
