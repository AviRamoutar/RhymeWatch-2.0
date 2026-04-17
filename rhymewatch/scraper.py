"""News headline aggregation across Finnhub / Google News / NewsAPI.

Moved here unchanged in behavior from the old top-level scraper.py, but the
env file is now `.env` (not `PersonalKeys.env`) so it works in standard
`python-dotenv` setups.
"""
from __future__ import annotations
import os
from datetime import datetime, timedelta, timezone
from typing import List, Tuple

import httpx
import feedparser
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


def get_headlines(symbol: str, days: int = 60) -> List[Tuple[str, datetime]]:
    out: List[Tuple[str, datetime]] = []
    for fn in (_finnhub, _google_rss, _newsapi):
        try:
            out.extend(fn(symbol, days))
        except Exception as e:
            print(f"{fn.__name__}: {e}")
    uniq: dict[str, datetime] = {}
    for t, d in out:
        if t not in uniq:
            uniq[t] = d
    return sorted(uniq.items(), key=lambda x: x[1], reverse=True)


def _finnhub(symbol: str, days: int) -> List[Tuple[str, datetime]]:
    key = os.getenv("FINNHUB_KEY")
    if not key:
        return []
    now = datetime.now(timezone.utc)
    f = (now - timedelta(days=days)).strftime("%Y-%m-%d")
    t = now.strftime("%Y-%m-%d")
    url = f"https://finnhub.io/api/v1/company-news?symbol={symbol}&from={f}&to={t}&token={key}"
    r = httpx.get(url, timeout=10)
    r.raise_for_status()
    items = r.json() or []
    return [
        (a["headline"], datetime.fromtimestamp(a["datetime"], tz=timezone.utc))
        for a in items[:50] if a.get("headline")
    ]


COMPANY = {
    "AAPL": "Apple", "GOOGL": "Google", "MSFT": "Microsoft", "AMZN": "Amazon",
    "TSLA": "Tesla", "META": "Meta", "NVDA": "NVIDIA", "AMD": "Advanced Micro Devices",
    "ABBV": "AbbVie", "ABNB": "Airbnb",
}


def _google_rss(symbol: str, days: int) -> List[Tuple[str, datetime]]:
    q = COMPANY.get(symbol, symbol) + " stock"
    url = f"https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en"
    feed = feedparser.parse(url)
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    out = []
    for e in feed.entries[:30]:
        try:
            d = datetime(*e.published_parsed[:6], tzinfo=timezone.utc)
            if d >= cutoff:
                out.append((e.title, d))
        except Exception:
            continue
    return out


def _newsapi(symbol: str, days: int) -> List[Tuple[str, datetime]]:
    key = os.getenv("NEWSAPI_KEY")
    if not key:
        return []
    f = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    r = httpx.get(
        "https://newsapi.org/v2/everything",
        params={"q": symbol, "from": f, "sortBy": "relevancy",
                "apiKey": key, "language": "en"},
        timeout=10,
    )
    if r.status_code == 426:
        return []
    r.raise_for_status()
    out = []
    for a in r.json().get("articles", [])[:30]:
        if a.get("title") and a["title"] != "[Removed]":
            out.append((a["title"], datetime.fromisoformat(a["publishedAt"].replace("Z", "+00:00"))))
    return out
