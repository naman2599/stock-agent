"""
Configuration: stock universe, thresholds, API keys.
Fill in ANTHROPIC_API_KEY / GROQ_API_KEY only if you want AI-written reasoning.
Without any key, the agent still works using rule-based technical + news scoring.
"""

import os

# --- Optional LLM keys (leave blank to run 100% free / rule-based) ---
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")  # groq.com has a generous free tier if you want an LLM for free

# --- Stock universe (NSE tickers, .NS suffix for yfinance) ---
# Starter list = 15 large-cap, liquid Nifty stocks. Kept deliberately small
# right now because Yahoo Finance rate-limits cloud IPs (GitHub Actions
# included) - fewer requests per run = far fewer failures. Once you've
# confirmed runs succeed reliably, expand this list gradually.
NIFTY50 = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "INFY.NS",
    "HINDUNILVR.NS", "ITC.NS", "SBIN.NS", "BHARTIARTL.NS", "BAJFINANCE.NS",
    "KOTAKBANK.NS", "LT.NS", "AXISBANK.NS", "ASIANPAINT.NS", "MARUTI.NS",
]

# Full Nifty 50 - swap this in once the smaller list is running reliably:
# NIFTY50 = [ ... paste the full 50 back in ... ]

# --- Screening thresholds ---
RSI_OVERSOLD = 35        # below this = potential buy zone
RSI_OVERBOUGHT = 70      # above this = avoid / potential sell zone
VOLUME_SPIKE_MULT = 1.5  # today's volume vs 20-day avg to flag unusual interest
TOP_N_DAILY = 5
TOP_N_WEEKLY = 8

OUTPUT_DIR = "output"