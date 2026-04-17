"""RhymeWatch 2.0 — FastAPI entry.

Single file so Vercel's @vercel/python adapter can route `/(.*) → app.py`.
All routes are prefixed with /api/* to match the frontend client.
"""
from __future__ import annotations
import os
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from rhymewatch import pipeline, sentiment, datasources, cache, __version__

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://rhymewatch.netlify.app",
    "https://rhymewatch.vercel.app",
]
extra = os.getenv("CORS_EXTRA_ORIGINS", "")
if extra:
    ALLOWED_ORIGINS.extend([o.strip() for o in extra.split(",") if o.strip()])

app = FastAPI(title="RhymeWatch API", version=__version__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "service": "rhymewatch",
        "version": __version__,
        "docs": "/docs",
        "methodology": "/api/methodology",
    }


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


@app.get("/api/health")
def health():
    return {"status": "ok", "version": __version__, "time": _now_iso()}


@app.get("/api/analyze")
def analyze(
    symbol: str = Query(..., description="Ticker symbol"),
    days: int = Query(180, ge=7, le=365),
):
    symbol = symbol.upper().strip()
    if not symbol.isalpha() or len(symbol) > 6:
        raise HTTPException(400, "invalid ticker")
    try:
        return pipeline.analyze(symbol, days)
    except Exception as e:
        raise HTTPException(500, f"analyze failed: {e}")


@app.get("/api/predict/{symbol}")
def predict(symbol: str):
    symbol = symbol.upper().strip()
    cached = cache.get(f"rw:predict:{symbol}")
    if cached:
        return cached
    data = pipeline.analyze(symbol, days=180)
    out = {"symbol": symbol, "nextDay": data["nextDay"],
           "generatedAt": data["generatedAt"]}
    cache.set(f"rw:predict:{symbol}", out, ex=12 * 3600)
    return out


@app.post("/api/sentiment")
def sentiment_endpoint(payload: dict):
    text = (payload or {}).get("text", "")
    if not text or not isinstance(text, str):
        raise HTTPException(400, "text required")
    result = sentiment.classify_one(
        text, force_escalate=bool((payload or {}).get("escalate"))
    )
    return result.to_dict()


@app.get("/api/movers")
def movers():
    cached = cache.get("rw:movers")
    if cached:
        return cached
    try:
        data = datasources.apewisdom("wallstreetbets")
    except Exception as e:
        raise HTTPException(502, f"apewisdom: {e}")
    cache.set("rw:movers", data, ex=15 * 60)
    return data


@app.get("/api/stocktwits/{symbol}")
def stocktwits_endpoint(symbol: str):
    symbol = symbol.upper().strip()
    return datasources.stocktwits(symbol)


@app.get("/api/methodology")
def methodology():
    return {
        "target": "next-day log returns (not prices)",
        "features": [
            "lagged log returns (1, 2, 5, 10, 21d)",
            "realized volatility (5, 21, 63d)",
            "RSI-14, MACD (macd+signal+hist), Bollinger bands, ATR-14, OBV",
            "volume z-score (21d)",
            "VIX level + delta",
            "sector relative strength",
            "news velocity z-score",
            "event flags (earnings ±2d, FOMC, OPEX, CPI)",
            "day of week",
        ],
        "validation": {
            "strategy": "walk-forward with embargo",
            "initial": 1000,
            "step": 21,
            "embargo": 5,
        },
        "metrics": [
            "MAE on returns",
            "directional accuracy (% sign match)",
            "Sharpe of signal, net 10bps round-trip",
        ],
        "disclaimers": [
            "Backtest only — does not guarantee future performance.",
            "We do not promise >55% directional on liquid US equities.",
            "Not investment advice.",
        ],
        "pipeline": {
            "sentiment_tiers": [
                "0: regex + WSB/emoji lexicon (<1ms)",
                "1: ONNX-int8 finbert-tone (~85MB, served from Vercel Blob)",
                "2: Gemini Flash-Lite escalation (sarcasm, multi-entity, aspects)",
            ],
            "prediction_model": "LightGBM on log returns · exported to ONNX",
        },
    }


@app.post("/api/cron/recompute")
def cron_recompute():
    """Called daily by Vercel Cron (22:00 UTC). Computes predictions for the
    configured watchlist and writes them to Upstash. Auth via a shared secret
    in the CRON_SECRET env var."""
    secret = os.getenv("CRON_SECRET")
    header = os.getenv("_VERCEL_CRON_SECRET_HEADER")  # local header check placeholder
    if secret and header and header != secret:
        raise HTTPException(401, "unauthorized")

    tickers = os.getenv(
        "RW_CRON_TICKERS",
        "AAPL,MSFT,NVDA,TSLA,AMZN,GOOGL,META,AMD,JPM,XOM,JNJ,WMT",
    ).split(",")
    updated, errors = [], []
    for t in tickers:
        t = t.strip().upper()
        if not t:
            continue
        try:
            data = pipeline.analyze(t, days=365)
            cache.set(f"rw:predict:{t}",
                      {"symbol": t, "nextDay": data["nextDay"],
                       "generatedAt": data["generatedAt"]},
                      ex=36 * 3600)
            updated.append(t)
        except Exception as e:
            errors.append({"symbol": t, "error": str(e)})
    return {"updated": updated, "errors": errors, "at": _now_iso()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
