import os, requests, datetime as dt
from typing import List, Tuple
from xml.etree import ElementTree as ET
from dotenv import load_dotenv

load_dotenv()

NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")
FINNHUB_KEY = os.getenv("FINNHUB_KEY", "")
USER_AGENT = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

def fetch_newsapi_headlines(ticker: str, start: dt.date, end: dt.date) -> List[Tuple[str, dt.datetime]]:
    if not NEWSAPI_KEY:
        return []

    url = (f"https://newsapi.org/v2/everything?q={ticker}&from={start}&to={end}"
           f"&language=en&pageSize=100&sortBy=publishedAt&apiKey={NEWSAPI_KEY}")

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        js = response.json()

        articles = []
        for article in js.get("articles", []):
            if article.get("title") and article.get("publishedAt"):
                title = article["title"]
                pub_date = article["publishedAt"].replace("Z", "+00:00")
                pub_dt = dt.datetime.fromisoformat(pub_date).replace(tzinfo=None)
                articles.append((title, pub_dt))

        return articles
    except Exception as e:
        print(f"[NewsAPI] Error: {e}")
        return []

def fetch_finnhub_headlines(ticker: str, start: dt.date, end: dt.date) -> List[Tuple[str, dt.datetime]]:
    if not FINNHUB_KEY:
        return []

    url = (f"https://finnhub.io/api/v1/company-news?symbol={ticker}"
           f"&from={start}&to={end}&token={FINNHUB_KEY}")

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        js = response.json()

        articles = []
        for article in js:
            if article.get("headline") and article.get("datetime"):
                title = article["headline"]
                pub_dt = dt.datetime.fromtimestamp(article["datetime"])
                articles.append((title, pub_dt))

        return articles
    except Exception as e:
        print(f"[Finnhub] Error: {e}")
        return []

def fetch_google_rss_headlines(ticker: str, days: int = 7) -> List[Tuple[str, dt.datetime]]:
    url = (f"https://news.google.com/rss/search?q={ticker}+stock"
           f"&hl=en-US&gl=US&ceid=US:en")

    try:
        response = requests.get(url, headers=USER_AGENT, timeout=10)
        response.raise_for_status()
        xml_content = response.text

        root = ET.fromstring(xml_content)
        items = root.findall(".//item")

        articles = []
        cutoff_date = dt.datetime.now() - dt.timedelta(days=days)

        for item in items:
            title_elem = item.find("title")
            pub_elem = item.find("pubDate")

            if title_elem is not None and pub_elem is not None:
                title = title_elem.text
                pub_date_str = pub_elem.text

                try:
                    pub_dt = dt.datetime.strptime(pub_date_str, "%a, %d %b %Y %H:%M:%S %Z")

                    if pub_dt >= cutoff_date:
                        articles.append((title, pub_dt))
                except ValueError:
                    continue

        return articles
    except Exception as e:
        print(f"[GoogleRSS] Error: {e}")
        return []

def get_headlines(ticker: str, days: int = 60) -> List[Tuple[str, dt.datetime]]:
    end_date = dt.datetime.now()
    start_date = end_date - dt.timedelta(days=days)

    print(f"Fetching headlines for {ticker} from {start_date.date()} to {end_date.date()}")

    articles = fetch_newsapi_headlines(ticker, start_date.date(), end_date.date())
    if articles:
        print(f"Found {len(articles)} articles from NewsAPI")
        return articles

    articles = fetch_finnhub_headlines(ticker, start_date.date(), end_date.date())
    if articles:
        print(f"Found {len(articles)} articles from Finnhub")
        return articles

    articles = fetch_google_rss_headlines(ticker, days=min(days, 30))
    if articles:
        print(f"Found {len(articles)} articles from Google RSS")
        return articles

    print(f"No articles found for {ticker}")
    return []