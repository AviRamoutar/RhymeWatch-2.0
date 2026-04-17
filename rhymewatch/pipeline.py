"""End-to-end per-ticker analyze pipeline."""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Dict, List
import pandas as pd

from . import scraper, sentiment, features, predictor, cache


def _ohlcv(symbol: str, days: int):
    try:
        import yfinance as yf
    except ImportError:
        return pd.DataFrame()
    hist = yf.Ticker(symbol).history(period=f"{days}d", auto_adjust=True)
    return hist


def _vix(days: int):
    try:
        import yfinance as yf
    except ImportError:
        return None
    try:
        hist = yf.Ticker("^VIX").history(period=f"{days}d", auto_adjust=True)
        return hist["Close"]
    except Exception:
        return None


def analyze(symbol: str, days: int = 180) -> Dict[str, Any]:
    key = f"rw:analyze:{symbol}:{days}"
    cached = cache.get(key)
    if cached:
        return cached

    # 1. headlines + sentiment
    headlines = scraper.get_headlines(symbol, days=min(days, 60))
    titles = [t for t, _ in headlines]
    dates = [d.isoformat() for _, d in headlines]
    results = sentiment.classify_many(titles)
    counts = sentiment.counts(results)

    # 2. prices + features + model
    hist = _ohlcv(symbol, days)
    price_history: List[float] = []
    volume_history: List[float] = []
    report = None

    if not hist.empty:
        price_history = hist["Close"].round(4).tolist()
        volume_history = hist["Volume"].fillna(0).astype(int).tolist()
        try:
            vix = _vix(days)
            feat = features.build_features(hist, vix=vix)
            if len(feat) >= 60:
                _, report = predictor.train_and_report(feat)
        except Exception as e:
            print(f"features/predictor failed for {symbol}: {e}")

    news = [
        {
            "headline": titles[i],
            "date": dates[i],
            "sentiment": results[i].label,
            "confidence": round(results[i].confidence, 3),
            "tier": results[i].tier,
        }
        for i in range(len(titles))
    ]

    payload = {
        "symbol": symbol,
        "days_analyzed": days,
        "news": news,
        "total_headlines": len(news),
        "sentimentCounts": {
            "positive": counts.get("positive", 0),
            "neutral": counts.get("neutral", 0),
            "negative": counts.get("negative", 0),
        },
        "escalations": counts.get("escalations", 0),
        "sentimentModel": "finbert-tone-int8 + gemini-flash-lite escalation",
        "priceHistory": price_history,
        "volumeHistory": volume_history,
        "nextDay": {
            "direction": report.direction if report else "—",
            "expectedReturn": (report.expected_return * 100) if report else None,
            "directionalAccuracy": (report.directional_accuracy * 100) if report else None,
            "sharpe": f"{report.sharpe_net_10bps:.2f}" if report else "—",
            "mae": report.mae if report else None,
            "features": (f"{report.features} (technicals + sentiment + event flags)"
                         if report else None),
            "model": report.model if report else None,
            "trainedAt": report.trained_at if report else None,
            "nPredictions": report.n_predictions if report else None,
        },
        "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
    }
    cache.set(key, payload, ex=1800)
    return payload
