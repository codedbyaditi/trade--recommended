# Automated Trade Recommendation System

This project is a small prototype that computes technical indicators (RSI, MACD, moving averages) and provides simple BUY/SELL/HOLD suggestions. It integrates with Zerodha (Kite Connect) if you provide API credentials, or falls back to yfinance for demo runs.

## What is included

- `app.py` — Streamlit app (UI) to fetch data, compute indicators and show suggestions
- `indicators.py` — RSI, MACD, moving averages, and a simple recommendation function
- `zerodha_client.py` — Minimal KiteConnect wrapper (requires `kiteconnect` package and API credentials)
- `data_provider.py` — Fetch data from Zerodha (if configured) or yfinance fallback
- `requirements.txt` — Python dependencies
- `.env.example` — Example environment variables
- `tests/test_indicators.py` — Basic pytest for indicator functions

## Quick start

1. Create a virtual environment (recommended):

   ```powershell
   python -m venv .venv; .\.venv\Scripts\Activate.ps1
   ```

2. Install dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

3. (Optional) Configure Zerodha credentials

   - Create an app in your Zerodha developer console to get API key and secret.
   - Follow Kite Connect docs to generate a request token and exchange it for an access token.
   - Set `ZERODHA_API_KEY`, `ZERODHA_API_SECRET`, and `ZERODHA_ACCESS_TOKEN` in your environment or in a `.env` file (do NOT commit real keys).

4. Run the Streamlit app:

   ```powershell
   streamlit run app.py
   ```

5. In the sidebar: enter the symbol (e.g. `AAPL` or `RELIANCE.NS`), choose history and interval, then click "Fetch & Analyze".

## Notes & limitations

- The Zerodha wrapper is minimal: you must provide valid API credentials and an access token to fetch data from Zerodha.
- The indicator rules in `indicators.generate_simple_signal` are intentionally simple and designed as a starting point. Do not use this for production trading without backtesting and risk controls.
- yfinance is used as a convenient demo data source; it may use different ticker naming (e.g. NSE tickers need `.NS` suffix).

## Next steps (suggested)

- Add instrument mapping for Zerodha instrument tokens.
- Implement more indicators and parameter tuning.
- Add backtesting/simulation and transaction cost modeling.
- Persist user preferences and logs.

## Tests

Run unit tests:

```powershell
pytest -q
```

## Security

Never commit your actual API keys. Use environment variables or a secure secrets manager.


