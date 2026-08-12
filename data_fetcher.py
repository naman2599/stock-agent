"""
All data sources here are FREE, no API key required:
- Price/volume history: yfinance (wraps Yahoo Finance)
- News headlines: Google News RSS (no key needed)
"""

import yfinance as yf
import feedparser
import urllib.parse
import time


def get_price_history(ticker: str, period: str = "6mo"):
    """Fetch OHLCV history for a ticker. Returns a pandas DataFrame."""
    try:
        df = yf.Ticker(ticker).history(period=period)
        if df.empty:
            return None
        return df
    except Exception as e:
        print(f"[price fetch error] {ticker}: {e}")
        return None


def get_news_headlines(stock_name: str, max_items: int = 6):
    """
    Free news via Google News RSS. No API key, no rate-limit auth needed.
    Returns list of {title, link, published}.
    """
    query = urllib.parse.quote(f"{stock_name} NSE India stock")
    url = f"https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"
    try:
        feed = feedparser.parse(url)
        items = []
        for entry in feed.entries[:max_items]:
            items.append({
                "title": entry.title,
                "link": entry.link,
                "published": entry.get("published", ""),
            })
        return items
    except Exception as e:
        print(f"[news fetch error] {stock_name}: {e}")
        return []


def get_price_with_retry(ticker: str, period: str = "6mo", retries: int = 2):
    for attempt in range(retries):
        df = get_price_history(ticker, period)
        if df is not None:
            return df
        time.sleep(1)
    return None
