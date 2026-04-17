"""Additional data sources recommended in the research doc:

    · ApeWisdom   — free WSB mention counts
    · StockTwits  — public stream with self-labeled Bull/Bear tags
    · SEC EDGAR   — filings (8-K, 10-K, Form 4)

All are pure REST and run fine on Vercel serverless.
"""
from __future__ import annotations
import os
from typing import List, Dict, Any
from datetime import datetime, timezone
import httpx

UA = "RhymeWatch/2.0 contact@rhymewatch.local"


def apewisdom(filter_: str = "wallstreetbets") -> List[Dict[str, Any]]:
    url = f"https://apewisdom.io/api/v1.0/filter/{filter_}"
    r = httpx.get(url, timeout=10, headers={"User-Agent": UA})
    r.raise_for_status()
    items = r.json().get("results", [])
    return [
        {
            "symbol": x.get("ticker"),
            "mentions": int(x.get("mentions", 0)),
            "mentions_prev": int(x.get("mentions_24h_ago", 0)),
            "rank": int(x.get("rank", 0)),
            "upvotes": int(x.get("upvotes", 0)),
            "name": x.get("name"),
        }
        for x in items
    ]


def stocktwits(symbol: str) -> Dict[str, Any]:
    url = f"https://api.stocktwits.com/api/2/streams/symbol/{symbol}.json"
    r = httpx.get(url, timeout=10, headers={"User-Agent": UA})
    if r.status_code != 200:
        return {"symbol": symbol, "messages": [], "bull": 0, "bear": 0}
    data = r.json()
    msgs = data.get("messages", []) or []
    bull = sum(1 for m in msgs if (m.get("entities", {}).get("sentiment") or {}).get("basic") == "Bullish")
    bear = sum(1 for m in msgs if (m.get("entities", {}).get("sentiment") or {}).get("basic") == "Bearish")
    return {
        "symbol": symbol,
        "messages": [{"body": m.get("body"), "created_at": m.get("created_at"),
                      "sentiment": (m.get("entities", {}).get("sentiment") or {}).get("basic")}
                     for m in msgs[:30]],
        "bull": bull,
        "bear": bear,
    }


def edgar_recent(cik: str, form: str = "8-K", count: int = 10) -> List[Dict[str, Any]]:
    """Fetch recent filings for a CIK via SEC EDGAR Atom feed. The SEC
    requires a real User-Agent; make sure to set SEC_USER_AGENT env var."""
    ua = os.getenv("SEC_USER_AGENT", UA)
    url = (
        f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}"
        f"&type={form}&dateb=&owner=include&count={count}&output=atom"
    )
    r = httpx.get(url, timeout=15, headers={"User-Agent": ua})
    r.raise_for_status()
    import feedparser
    feed = feedparser.parse(r.text)
    out = []
    for e in feed.entries:
        out.append({
            "title": e.get("title"),
            "updated": e.get("updated"),
            "link": e.get("link"),
            "summary": e.get("summary", "")[:200],
        })
    return out


def news_velocity(symbol: str, headlines: List[tuple]) -> Dict[str, float]:
    """Return a news-velocity signal based on recent article count vs. a
    30-day rolling baseline. `headlines` is a list of (title, datetime).
    """
    if not headlines:
        return {"symbol": symbol, "last_24h": 0, "avg_30d": 0.0, "z": 0.0}
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    last_24h = sum(1 for _, d in headlines if (now - d.replace(tzinfo=None)).total_seconds() < 86400)
    buckets: Dict[int, int] = {}
    for _, d in headlines:
        delta_days = (now - d.replace(tzinfo=None)).days
        buckets[delta_days] = buckets.get(delta_days, 0) + 1
    per_day = [buckets.get(i, 0) for i in range(30)]
    avg = sum(per_day) / max(len(per_day), 1)
    variance = sum((x - avg) ** 2 for x in per_day) / max(len(per_day), 1)
    sd = variance ** 0.5 or 1.0
    z = (last_24h - avg) / sd
    return {"symbol": symbol, "last_24h": last_24h, "avg_30d": avg, "z": z}
