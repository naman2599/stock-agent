"""
Computes technical indicators and a 0-100 momentum/setup score per stock.
Pure math, fully free, no external calls.
"""

import pandas as pd
import ta


def compute_indicators(df: pd.DataFrame) -> dict:
    # Defensive: drop any row where Close is NaN (e.g. an unfinished bar for
    # the current trading day). screener.py already does this before calling
    # in, but this guards the function too in case it's called from elsewhere.
    df = df[df["Close"].notna()]

    close = df["Close"]
    volume = df["Volume"]

    rsi = ta.momentum.RSIIndicator(close, window=14).rsi().iloc[-1]
    sma20 = close.rolling(20).mean().iloc[-1]
    sma50 = close.rolling(50).mean().iloc[-1]
    sma200 = close.rolling(200).mean().iloc[-1] if len(close) >= 200 else None

    last_close = close.iloc[-1]
    avg_vol20 = volume.rolling(20).mean().iloc[-1]
    today_vol = volume.iloc[-1]
    vol_ratio = today_vol / avg_vol20 if avg_vol20 else 1

    # 52-week high/low (or as much history as we have)
    high_52w = close.max()
    low_52w = close.min()

    # Recent momentum: % change over last 5 and 20 sessions
    chg_5d = (last_close / close.iloc[-6] - 1) * 100 if len(close) > 6 else 0
    chg_20d = (last_close / close.iloc[-21] - 1) * 100 if len(close) > 21 else 0

    return {
        "last_close": round(last_close, 2),
        "rsi": round(rsi, 1) if pd.notna(rsi) else None,
        "sma20": round(sma20, 2) if pd.notna(sma20) else None,
        "sma50": round(sma50, 2) if pd.notna(sma50) else None,
        "sma200": round(sma200, 2) if sma200 and pd.notna(sma200) else None,
        "volume_ratio_vs_20d_avg": round(vol_ratio, 2),
        "high_52w": round(high_52w, 2),
        "low_52w": round(low_52w, 2),
        "pct_change_5d": round(chg_5d, 2),
        "pct_change_20d": round(chg_20d, 2),
    }


def score_setup(indicators: dict) -> float:
    """
    Simple transparent scoring (0-100). Not a black box:
    + trend above key moving averages
    + healthy RSI (not overbought)
    + volume confirmation
    + positive but not overextended momentum
    """
    score = 50.0
    rsi = indicators.get("rsi")
    last = indicators["last_close"]
    sma20 = indicators.get("sma20")
    sma50 = indicators.get("sma50")
    vol_ratio = indicators.get("volume_ratio_vs_20d_avg", 1)

    if rsi is not None:
        if 40 <= rsi <= 60:
            score += 10   # healthy, room to run either way
        elif rsi < 35:
            score += 15   # oversold, potential bounce
        elif rsi > 70:
            score -= 20   # overbought, risky entry

    if sma20 and last > sma20:
        score += 10
    if sma50 and last > sma50:
        score += 10
    if sma20 and sma50 and sma20 > sma50:
        score += 5   # short-term trend above medium-term = uptrend intact

    if vol_ratio > 1.5:
        score += 10  # unusual volume = something's happening
    elif vol_ratio < 0.7:
        score -= 5   # dead volume, low conviction

    chg5 = indicators.get("pct_change_5d", 0)
    if 1 <= chg5 <= 8:
        score += 5   # steady climb
    elif chg5 > 15:
        score -= 10  # possibly overextended, chasing risk

    return max(0, min(100, round(score, 1)))


def suggest_levels(indicators: dict):
    """
    Rule-based entry/target/stop-loss suggestion.
    Target = based on 52w high or a conservative % move, whichever is nearer.
    Stop-loss = below recent support (sma20) with a buffer.
    THESE ARE HEURISTICS, NOT GUARANTEES.
    """
    last = indicators["last_close"]
    high_52w = indicators["high_52w"]
    sma20 = indicators.get("sma20") or last

    conservative_target = round(last * 1.08, 2)   # +8% swing target
    resistance_target = round(high_52w, 2) if high_52w > last else conservative_target
    target = min(conservative_target, resistance_target) if resistance_target > last else conservative_target

    stop_loss = round(min(sma20, last) * 0.96, 2)  # ~4% below support

    return {
        "suggested_entry_zone": f"{round(last * 0.99, 2)} - {round(last * 1.01, 2)}",
        "target_price": target,
        "stop_loss": stop_loss,
        "risk_reward": round((target - last) / max(last - stop_loss, 0.01), 2),
    }