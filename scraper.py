import requests
from datetime import datetime, timedelta
import feedparser
from typing import List, Tuple
import os
from dotenv import load_dotenv

# Load environment variables from my own doc
load_dotenv('PersonalKeys.env')

def get_headlines(symbol: str, days: int = 60) -> List[Tuple[str, datetime]]:
    """Fetch news headlines for a given stock symbol."""
    headlines_with_dates = []

    # Try Finnhub first
    try:
        headlines_with_dates.extend(get_finnhub_news(symbol, days))
    except Exception as e:
        print(f"Finnhub error: {e}")

    # Try Google News RSS
    try:
        headlines_with_dates.extend(get_google_news(symbol, days))
    except Exception as e:
        print(f"Google News error: {e}")

    # Tries NewsAPI but chilling if 426 kicks
    try:
        headlines_with_dates.extend(get_newsapi_headlines(symbol, days))
    except Exception as e:
        print(f"NewsAPI error: {e}")

    # Remove dupes
    unique_headlines = {}
    for headline, date in headlines_with_dates:
        if headline not in unique_headlines:
            unique_headlines[headline] = date

    sorted_headlines = sorted(unique_headlines.items(), key=lambda x: x[1], reverse=True)
    return sorted_headlines

def get_finnhub_news(symbol: str, days: int) -> List[Tuple[str, datetime]]:
    """Fetch news from Finnhub."""
    api_key = os.getenv('FINNHUB_KEY')
    if not api_key:
        print("Warning: FINNHUB_KEY not found in environment variables")
        return []

    from_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    to_date = datetime.now().strftime('%Y-%m-%d')

    url = f"https://finnhub.io/api/v1/company-news?symbol={symbol}&from={from_date}&to={to_date}&token={api_key}"

    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            headlines = []
            for article in data[:50]:  # Limit to 50 articles
                if article.get('headline'):
                    date = datetime.fromtimestamp(article['datetime'])
                    headlines.append((article['headline'], date))
            print(f"Found {len(headlines)} articles from Finnhub")
            return headlines
        else:
            print(f"Finnhub API error: {response.status_code}")
    except Exception as e:
        print(f"Finnhub error: {e}")

    return []

def get_google_news(symbol: str, days: int) -> List[Tuple[str, datetime]]:
    """Fetch news from Google News RSS feed."""
    company_names = {
        'AAPL': 'Apple',
        'GOOGL': 'Google',
        'MSFT': 'Microsoft',
        'AMZN': 'Amazon',
        'TSLA': 'Tesla',
        'META': 'Meta',
        'NVDA': 'NVIDIA',
        'AMD': 'Advanced Micro Devices',
        'ABBV': 'AbbVie',
        'ABC': 'AmerisourceBergen',
        'ABMD': 'Abiomed',
        'ABNB': 'Airbnb',
    }

    query = company_names.get(symbol, symbol) + " stock"
    url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"

    try:
        feed = feedparser.parse(url)
        headlines = []
        cutoff_date = datetime.now() - timedelta(days=days)

        for entry in feed.entries[:30]:  # Limit 30 articles
            try:
                pub_date = datetime(*entry.published_parsed[:6])
                if pub_date >= cutoff_date:
                    headlines.append((entry.title, pub_date))
            except:
                continue

        print(f"Found {len(headlines)} articles from Google News")
        return headlines
    except Exception as e:
        print(f"Google News error: {e}")

    return []

def get_newsapi_headlines(symbol: str, days: int) -> List[Tuple[str, datetime]]:
    """Fetch news from NewsAPI."""
    api_key = os.getenv('NEWSAPI_KEY')
    if not api_key:
        print("Warning: NEWSAPI_KEY not found in environment variables")
        return []

    from_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

    url = "https://newsapi.org/v2/everything"
    params = {
        'q': symbol,
        'from': from_date,
        'sortBy': 'relevancy',
        'apiKey': api_key,
        'language': 'en'
    }

    try:
        response = requests.get(url, params=params, timeout=10)

        # Handled 426
        if response.status_code == 426:
            print("NewsAPI requires upgrade to paid plan - skipping NewsAPI and using other sources")
            return []

        if response.status_code == 200:
            data = response.json()
            headlines = []
            for article in data.get('articles', [])[:30]:
                if article.get('title') and article['title'] != '[Removed]':
                    date = datetime.fromisoformat(article['publishedAt'].replace('Z', '+00:00'))
                    headlines.append((article['title'], date))
            print(f"Found {len(headlines)} articles from NewsAPI")
            return headlines
        else:
            print(f"NewsAPI error: {response.status_code}")
    except Exception as e:
        print(f"NewsAPI error: {e}")

    return []