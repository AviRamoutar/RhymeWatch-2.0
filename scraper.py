
import os, requests, datetime as dt
from typing import List, Tuple
from xml.etree import ElementTree as ET

NEWSAPI_KEY   = os.getenv("NEWSAPI_KEY",   "")       # sign up → newsapi.org
FINNHUB_KEY   = os.getenv("FINNHUB_KEY",   "")       # sign up → finnhub.io
USER_AGENT    = {"User-Agent": "Mozilla/5.0"}

def _newsapi(ticker:str, start:dt.date, end:dt.date) -> List[Tuple[str, dt.datetime]]:
    """Query NewsAPI /v2/everything (needs key)."""
    if not NEWSAPI_KEY: return []
    url = ("https://newsapi.org/v2/everything?q="
           f"{ticker}&from={start}&to={end}&language=en&pageSize=100&sortBy=publishedAt&apiKey={NEWSAPI_KEY}")
    try:
        js = requests.get(url, timeout=10).json()
        return [(a["title"], dt.datetime.fromisoformat(a["publishedAt"].replace("Z","")))
                for a in js.get("articles", [])]
    except Exception as e:
        print("[NewsAPI]", e); return []

def _finnhub(ticker:str, start:dt.date, end:dt.date) -> List[Tuple[str, dt.datetime]]:
    """Finnhub company-news endpoint (needs key)."""
    if not FINNHUB_KEY: return []
    url = (f"https://finnhub.io/api/v1/company-news?symbol={ticker}"
           f"&from={start}&to={end}&token={FINNHUB_KEY}")
    try:
        js = requests.get(url, timeout=10).json()
        return [(art["headline"], dt.datetime.fromtimestamp(art["datetime"])) for art in js]
    except Exception as e:
        print("[Finnhub]", e); return []

def _googlerss(ticker:str, days:int=7) -> List[Tuple[str, dt.datetime]]:
    """Google News RSS fallback (no key, limited to ~10-20 items)."""
    url = ( "https://news.google.com/rss/search?q="
            f"{ticker}+stock+when:{days}d&hl=en-US&gl=US&ceid=US:en")
    try:
        xml = requests.get(url, headers=USER_AGENT, timeout=10).text
        root = ET.fromstring(xml)
        items = root.findall(".//item")
        out=[]
        for it in items:
            title = it.find("title").text
            pub  = it.find("pubDate").text     # e.g. 'Fri, 05 Jul 2024 14:30:00 GMT'
            pub_dt = dt.datetime.strptime(pub, "%a, %d %b %Y %H:%M:%S %Z")
            out.append((title, pub_dt))
        return out
    except Exception as e:
        print("[GoogleRSS]", e); return []

# ---------- public API ----------
def get_headlines(ticker:str,
                  start_date:dt.datetime,
                  end_date:dt.datetime) -> List[Tuple[str, dt.datetime]]:
    """Returns list[(headline, datetime)] pulled from NewsAPI → Finnhub → GoogleRSS."""
    print(f"Fetching headlines for {ticker}  {start_date.date()} → {end_date.date()}")
    for fetch in (_newsapi, _finnhub):
        res = fetch(ticker, start_date.date(), end_date.date())
        if res: return res
    # google fallback uses relative window (days); pass span length
    span = max(1, (end_date.date() - start_date.date()).days)
    return _googlerss(ticker, days=min(span, 30))     # Google caps at 30d
