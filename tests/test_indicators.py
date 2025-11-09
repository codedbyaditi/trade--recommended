import pandas as pd
import numpy as np
from indicators import rsi, macd


def test_rsi_basic():
    prices = pd.Series([1,2,3,4,5,6,7,8,9,10,11,12,13,14,15])
    r = rsi(prices, period=5)
    assert isinstance(r, pd.Series)
    assert not r.isnull().all()


def test_macd_basic():
    prices = pd.Series(np.linspace(1, 100, 100))
    m = macd(prices)
    assert set(["macd","signal","hist"]).issubset(m.columns)
    assert len(m) == len(prices)
