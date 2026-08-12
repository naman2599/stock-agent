"""
All data sources here are FREE, no API key required:
- Price/volume history: yfinance (wraps Yahoo Finance)
- News headlines: Google News RSS (no key needed)

IMPORTANT: Yahoo Finance aggressively rate-limits/blocks requests from shared
cloud IPs (GitHub Actions runners included). This module works around that with:
  1. A browser-impersonating session (curl_cffi) - Yahoo blocks based partly
     on TLS/HTTP fingerprint, not just request volume
  2. A small delay between requests - avoids bursts that trigger blocks
  3. Longer backoff on retry - a 1-second retry is not enough once you're
     rate-limited; Yahoo needs real cooldown time
"""

import yfinance as yf
import feedparser
import urllib.parse
import time
import random

try:
    from curl_cffi import requests as curl_requests
    _SESSION = curl_requests.Session(impersonate="chrome")
except ImportError:
    _SESSION = None  # falls back to yfinance's default session


def get_price_history(ticker: str, period: str = "6mo"):
    """Fetch OHLCV history for a ticker. Returns a pandas DataFrame."""
    try:
        t = yf.Ticker(ticker, session=_SESSION) if _SESSION else yf.Ticker(ticker)
        df = t.history(period=period)
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


def get_price_with_retry(ticker: str, period: str = "6mo", retries: int = 3):
    for attempt in range(retries):
        df = get_price_history(ticker, period)
        if df is not None:
            return df
        # Exponential-ish backoff: 3s, 8s - a 1s retry does nothing once
        # you've actually been rate-limited.
        time.sleep(3 + attempt * 5)
    return None


def polite_delay():
    """Call between tickers in the screening loop to avoid bursty requests."""
    time.sleep(random.uniform(1.2, 2.5))