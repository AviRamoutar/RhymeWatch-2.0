import requests
from bs4 import BeautifulSoup

from datetime import datetime, timedelta

# Yahoo Finance Scraper
def scrape_yahoo_headlines(ticker: str):
    """Scrape latest news headlines and relative times from Yahoo Finance for the given ticker.
    Returns a list of (headline, time_str) tuples."""
    headlines = []
    # Construct Yahoo Finance URL for the ticker's news section
    # Example: https://finance.yahoo.com/quote/AAPL?p=AAPL (the news is included on the quote page)
    url = f"https://finance.yahoo.com/quote/{ticker}?p={ticker}"
    try:
        # Use a realistic User-Agent to avoid blocking
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return headlines
        soup = BeautifulSoup(response.text, "html.parser")
        # Yahoo Finance news items: find div that has an h3 tag with a link (<h3><a>...headline...</a></h3>)
        news_items = soup.select('div:has(>h3>a)')
        for item in news_items:
            # Headline text
            h3 = item.find('h3')
            if h3 and h3.text:
                title = h3.text.strip()
            else:
                continue
            # Time/source info might be in a sibling span or small tag
            # Yahoo Finance typically has something like: <span class="C(#959595) Fz(11px) ...">Source • X hours ago</span>
            time_span = item.find('span')
            time_text = time_span.text.strip() if time_span else ""
            headlines.append((title, time_text))
    except Exception as e:
        print(f"Error scraping Yahoo Finance: {e}")
    return headlines

# MarketWatch Scraper
def scrape_marketwatch_headlines(ticker: str):
    """Scrape latest news headlines and times from MarketWatch for the given ticker.
    Returns a list of (headline, time_str) tuples."""
    headlines = []
    # MarketWatch search URL: We'll use MarketWatch's search to find articles for the ticker
    # This uses the MarketWatch search query for the ticker symbol.
    query_url = f"https://www.marketwatch.com/search?q={ticker}"
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(query_url, headers=headers, timeout=10)
        if response.status_code != 200:
            return headlines
        soup = BeautifulSoup(response.text, "html.parser")
        # In MarketWatch search results, articles are in <div class="searchresult"> (if search returns news)
        results = soup.find_all("div", class_="searchresult")
        for res in results:
            # Each result might have a headline and a date/time
            title_tag = res.find("a", class_="link")  # 'a.link' contains the headline text in some MW pages
            time_tag = res.find("span", class_="published-date")  # possibly the time info
            if not title_tag:
                continue
            title = title_tag.text.strip()
            # Get time text if available; MarketWatch might show absolute date/time like "Jan 5, 2025 10:00 AM ET"
            time_text = ""
            if time_tag:
                time_text = time_tag.text.strip()
            headlines.append((title, time_text))
    except Exception as e:
        print(f"Error scraping MarketWatch: {e}")
    return headlines
