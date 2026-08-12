"""
Main orchestration. Run directly for a one-off screen, or import run_screen()
from api.py / a scheduler.

Usage:
    python screener.py daily
    python screener.py weekly
"""

import sys
import json
import os
from datetime import datetime

import config
from data_fetcher import get_price_with_retry, get_news_headlines
from technical_analysis import compute_indicators, score_setup, suggest_levels
from sentiment import rule_based_sentiment, llm_reasoning


def screen_stock(ticker: str):
    df = get_price_with_retry(ticker, period="6mo")
    if df is None or len(df) < 25:
        return None

    indicators = compute_indicators(df)
    score = score_setup(indicators)
    levels = suggest_levels(indicators)

    stock_name = ticker.replace(".NS", "")
    headlines = get_news_headlines(stock_name)
    sentiment = rule_based_sentiment(headlines)

    # sentiment nudges the technical score
    if sentiment["label"] == "positive":
        score = min(100, score + 8)
    elif sentiment["label"] == "negative":
        score = max(0, score - 15)

    return {
        "ticker": ticker,
        "name": stock_name,
        "score": score,
        "indicators": indicators,
        "levels": levels,
        "sentiment": sentiment,
        "headlines": headlines[:5],
    }


def run_screen(mode: str = "daily", use_llm_reasoning: bool = False):
    universe = config.NIFTY50
    top_n = config.TOP_N_DAILY if mode == "daily" else config.TOP_N_WEEKLY

    results = []
    for ticker in universe:
        r = screen_stock(ticker)
        if r:
            results.append(r)

    results.sort(key=lambda x: x["score"], reverse=True)
    shortlist = results[:top_n]

    if use_llm_reasoning:
        for stock in shortlist:
            stock["reasoning"] = llm_reasoning(
                stock["name"], stock["indicators"], stock["headlines"], stock["levels"]
            )

    output = {
        "generated_at": datetime.now().isoformat(),
        "mode": mode,
        "disclaimer": (
            "Informational / decision-support only. Not financial advice. "
            "Based on technical indicators and public news headlines at generation time. "
            "Markets carry risk of loss; verify independently before trading."
        ),
        "shortlist": shortlist,
    }

    _save_with_history(mode, output)
    return output


def _save_with_history(mode: str, output: dict):
    """
    Writes three things so the frontend never has to call an API to view data:
    1. output/{mode}/{date}.json   - permanent dated snapshot (this IS the history)
    2. output/{mode}/latest.json   - always the most recent run, for quick load
    3. output/index.json           - list of every date available, per mode, for the frontend dropdown
    """
    mode_dir = f"{config.OUTPUT_DIR}/{mode}"
    os.makedirs(mode_dir, exist_ok=True)

    today = datetime.now().strftime("%Y-%m-%d")
    dated_path = f"{mode_dir}/{today}.json"
    latest_path = f"{mode_dir}/latest.json"

    with open(dated_path, "w") as f:
        json.dump(output, f, indent=2)
    with open(latest_path, "w") as f:
        json.dump(output, f, indent=2)

    index_path = f"{config.OUTPUT_DIR}/index.json"
    index = {"daily": [], "weekly": []}
    if os.path.exists(index_path):
        with open(index_path) as f:
            index = json.load(f)

    if today not in index[mode]:
        index[mode].append(today)
        index[mode].sort(reverse=True)  # newest first

    with open(index_path, "w") as f:
        json.dump(index, f, indent=2)

    print(f"Wrote {len(output['shortlist'])} stocks to {dated_path} (+ latest.json, index.json updated)")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "daily"
    run_screen(mode)
