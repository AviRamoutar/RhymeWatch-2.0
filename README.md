# RhymeWatch 2.0

Walk-forward back-tested signals across 8,000 US tickers. Sentiment and
technicals with disclosed directional accuracy — no promises that don't
survive an honest backtest.

## What's new in 2.0

- Hand-crafted Bloomberg-terminal-meets-Linear UI in amber on warm stone.
  No glassmorphism, no gradients, no purple.
- Three-tier sentiment pipeline:
  - Tier 0 — regex/lexicon for WSB slang and emoji (<1ms).
  - Tier 1 — ONNX-int8 `finbert-tone` (~85 MB) served from Vercel Blob.
  - Tier 2 — Gemini 2.5 Flash-Lite escalation for sarcasm, multi-entity
    text, and aspect analysis.
- LightGBM on **log returns** (not prices) with 21 features from `pandas-ta`
  plus VIX, sector relative strength, news velocity, and event flags.
- **Walk-forward cross-validation with embargo** — replaces the classic
  `train_test_split(shuffle=True)` that inflates reported accuracy 5–15pp.
- Honest metrics published per ticker: MAE on returns, directional accuracy,
  Sharpe net of 10 bps round-trip.
- ⌘K command palette + F1–F4 function-key navigation.
- `requirements.txt` trimmed from ~950 MB (with `torch`) to ~170 MB so the
  whole backend fits Vercel's 250 MB Python limit.

## Layout

```
app.py                 FastAPI entry · routes are /api/*
vercel.json            @vercel/python adapter + daily cron at 22:00 UTC
requirements.txt       ~170 MB installed
rhymewatch/            backend package
  sentiment.py         three-tier pipeline
  lexicon.py           Tier 0
  onnx_sentiment.py    Tier 1 (loads from Vercel Blob)
  llm.py               Tier 2 (Gemini Flash-Lite)
  predictor.py         LightGBM on log returns
  features.py          pandas-ta features + lag discipline
  validation.py        walk-forward + embargo + honest metrics
  scraper.py           Finnhub / Google News / NewsAPI
  datasources.py       ApeWisdom / StockTwits / SEC EDGAR / news velocity
  cache.py             Upstash Redis with in-memory fallback
  pipeline.py          end-to-end per-ticker analyze
frontend/              React 18 + Tailwind v3 + cmdk
  src/App.js           router + ⌘K + function-key nav
  src/routes/          Watchlist, Ticker, Movers, Sentiment, Methodology, Changelog
  src/components/      TickerCard, DataTable, CommandPalette, Sparkline, ...
  src/lib/api.js       typed client for /api/*
```

## Running locally

```bash
# Backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload --port 8000

# Frontend
cd frontend && npm install && npm start
```

## Environment variables

```
FINNHUB_KEY                    # news (free)
NEWSAPI_KEY                    # optional, 426s on free tier
GEMINI_API_KEY                 # tier-2 sentiment (free tier: 1500 req/day)
ONNX_SENTIMENT_MODEL_URL       # Vercel Blob URL for the quantized model
ONNX_SENTIMENT_TOKENIZER_URL   # Vercel Blob URL for tokenizer.json
UPSTASH_REDIS_REST_URL
UPSTASH_REDIS_REST_TOKEN
CRON_SECRET                    # optional bearer for /api/cron/recompute
SEC_USER_AGENT                 # required by SEC EDGAR
RW_CRON_TICKERS                # comma-separated watchlist for cron (default 12 tickers)
```

## Methodology

See `/methodology` in the app — it documents target variable, every feature,
the walk-forward validation, the metrics we report, and everything we do not
promise. Summary:

- Target: next-day log return, never raw price.
- Validation: walk-forward with an embargo window to prevent leakage.
- Metrics: MAE on returns, directional accuracy, Sharpe net 10 bps.
- Current aggregate: **53.4% directional · Sharpe 0.41 · walk-forward · 5 yr**.

We don't promise more than 55% directional because no honest backtest of
liquid US equities produces more than 55% directional. Not investment advice.
