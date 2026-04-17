"""Feature engineering for the LightGBM return-predictor.

Uses `pandas-ta` when available (~2MB, Vercel-compatible). Every feature is
lagged by ≥1 trading day to prevent lookahead. Target is the next-day log
return, not price.
"""
from __future__ import annotations
from typing import Optional
import numpy as np
import pandas as pd

try:
    import pandas_ta as ta
    _HAS_TA = True
except Exception:
    _HAS_TA = False


SECTOR_ETF = {
    "AAPL": "XLK", "MSFT": "XLK", "NVDA": "XLK", "AMD": "XLK", "GOOGL": "XLC",
    "META": "XLC", "AMZN": "XLY", "TSLA": "XLY", "JPM": "XLF", "BAC": "XLF",
    "XOM": "XLE", "CVX": "XLE", "JNJ": "XLV", "PFE": "XLV", "UNH": "XLV",
    "WMT": "XLP", "KO": "XLP", "PG": "XLP", "BA": "XLI", "CAT": "XLI",
}


def _fallback_rsi(close: pd.Series, length: int = 14) -> pd.Series:
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(length).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(length).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def _fallback_atr(high: pd.Series, low: pd.Series, close: pd.Series, length: int = 14) -> pd.Series:
    prev = close.shift(1)
    tr = pd.concat([high - low, (high - prev).abs(), (low - prev).abs()], axis=1).max(axis=1)
    return tr.rolling(length).mean()


def build_features(df: pd.DataFrame, vix: Optional[pd.Series] = None,
                   sector_series: Optional[pd.Series] = None,
                   news_velocity: Optional[pd.Series] = None,
                   event_flags: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """Build the feature matrix.

    Required df columns: open, high, low, close, volume. Index must be
    DatetimeIndex at daily frequency (trading days).
    """
    df = df.copy()
    df.columns = [c.lower() for c in df.columns]
    if "adj close" in df.columns and "close" not in df.columns:
        df["close"] = df["adj close"]

    close = df["close"]
    high = df["high"]
    low = df["low"]
    volume = df["volume"]

    f = pd.DataFrame(index=df.index)
    # log returns + lags
    f["ret_1"] = np.log(close / close.shift(1))
    for lag in (2, 5, 10, 21):
        f[f"ret_{lag}"] = np.log(close / close.shift(lag))
    # realized volatility
    for w in (5, 21, 63):
        f[f"rv_{w}"] = f["ret_1"].rolling(w).std()
    # technicals
    if _HAS_TA:
        f["rsi_14"] = ta.rsi(close, length=14)
        macd = ta.macd(close)
        if macd is not None:
            f["macd"] = macd.iloc[:, 0]
            f["macd_signal"] = macd.iloc[:, 1]
            f["macd_hist"] = macd.iloc[:, 2]
        bb = ta.bbands(close, length=20)
        if bb is not None:
            f["bb_lower"] = bb.iloc[:, 0]
            f["bb_upper"] = bb.iloc[:, 2]
            f["bb_pos"] = (close - bb.iloc[:, 0]) / (bb.iloc[:, 2] - bb.iloc[:, 0]).replace(0, np.nan)
        f["atr_14"] = ta.atr(high, low, close, length=14)
        f["obv"] = ta.obv(close, volume)
    else:
        f["rsi_14"] = _fallback_rsi(close, 14)
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        f["macd"] = ema12 - ema26
        f["macd_signal"] = f["macd"].ewm(span=9, adjust=False).mean()
        f["macd_hist"] = f["macd"] - f["macd_signal"]
        sma20 = close.rolling(20).mean()
        sd20 = close.rolling(20).std()
        f["bb_lower"] = sma20 - 2 * sd20
        f["bb_upper"] = sma20 + 2 * sd20
        f["bb_pos"] = (close - f["bb_lower"]) / (f["bb_upper"] - f["bb_lower"]).replace(0, np.nan)
        f["atr_14"] = _fallback_atr(high, low, close, 14)
        f["obv"] = (np.sign(close.diff()).fillna(0) * volume).cumsum()

    # volume z
    f["vol_z_21"] = (volume - volume.rolling(21).mean()) / volume.rolling(21).std()

    # VIX
    if vix is not None:
        vv = vix.reindex(df.index).ffill()
        f["vix"] = vv
        f["vix_delta"] = vv.diff()

    # sector relative strength
    if sector_series is not None:
        sec = sector_series.reindex(df.index).ffill()
        sec_ret = np.log(sec / sec.shift(1))
        f["sector_rs_1"] = f["ret_1"] - sec_ret

    # news velocity
    if news_velocity is not None:
        nv = news_velocity.reindex(df.index).fillna(0)
        baseline = nv.rolling(30).mean()
        f["news_velocity_z"] = (nv - baseline) / nv.rolling(30).std()

    # event flags
    if event_flags is not None:
        for col in event_flags.columns:
            f[col] = event_flags[col].reindex(df.index).fillna(0).astype(int)

    # calendar
    f["dow"] = df.index.dayofweek

    # **lag everything by 1 trading day** — critical to prevent lookahead
    out = f.shift(1)

    # target: next-day log return
    out["y_logret"] = f["ret_1"].shift(-1)
    return out.dropna()


FEATURE_COLS = [
    "ret_1", "ret_2", "ret_5", "ret_10", "ret_21",
    "rv_5", "rv_21", "rv_63",
    "rsi_14", "macd", "macd_signal", "macd_hist",
    "bb_pos", "atr_14", "obv",
    "vol_z_21", "dow",
]


def event_flags_for(dates: pd.DatetimeIndex, earnings: Optional[list] = None) -> pd.DataFrame:
    """Return a DataFrame of event flags. FOMC / OPEX / CPI are approximate —
    real cron computes exact dates from the ICS feeds."""
    df = pd.DataFrame(index=dates)
    # OPEX: third Friday of the month
    df["is_opex"] = [(d.weekday() == 4 and 15 <= d.day <= 21) for d in dates]
    # CPI: approximately second Wednesday
    df["is_cpi"] = [(d.weekday() == 2 and 8 <= d.day <= 14) for d in dates]
    # FOMC: rough — 8 per year, every ~6 weeks. Precise feed is better.
    df["is_fomc"] = False
    # earnings window ±2 trading days
    df["is_earnings_window"] = False
    if earnings:
        earn_set = set(pd.to_datetime(earnings).date)
        flags = []
        for d in dates:
            near = any(abs((d.date() - e).days) <= 2 for e in earn_set)
            flags.append(near)
        df["is_earnings_window"] = flags
    return df.astype(int)
