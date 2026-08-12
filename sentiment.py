"""
Two modes:
1. FREE rule-based keyword sentiment (default, no API key needed)
2. Optional LLM-written reasoning (Claude or Groq) if you set a key in config.py

Rule-based mode is fully free forever. LLM mode gives better written
"why" explanations but needs an API key (Groq's free tier works fine).
"""

import config

POSITIVE_WORDS = [
    "surge", "rally", "beat", "beats", "upgrade", "record", "strong",
    "growth", "profit rise", "outperform", "buy rating", "expansion",
    "order win", "bullish", "jump", "soar", "wins", "raises guidance",
]
NEGATIVE_WORDS = [
    "fall", "falls", "plunge", "downgrade", "miss", "misses", "weak",
    "decline", "loss", "probe", "investigation", "lawsuit", "bearish",
    "cut guidance", "sell rating", "layoffs", "fraud", "default",
]


def rule_based_sentiment(headlines: list) -> dict:
    pos, neg = 0, 0
    hits = []
    for h in headlines:
        title_lower = h["title"].lower()
        p = sum(1 for w in POSITIVE_WORDS if w in title_lower)
        n = sum(1 for w in NEGATIVE_WORDS if w in title_lower)
        pos += p
        neg += n
        if p or n:
            hits.append(h["title"])

    net = pos - neg
    if net >= 2:
        label = "positive"
    elif net <= -2:
        label = "negative"
    else:
        label = "neutral"

    return {
        "label": label,
        "positive_hits": pos,
        "negative_hits": neg,
        "flagged_headlines": hits[:3],
    }


def llm_reasoning(stock_name: str, indicators: dict, headlines: list, levels: dict) -> str:
    """
    Optional: calls Groq (free tier) or Anthropic if a key is set in config.py.
    Falls back to a template explanation if no key is configured.
    """
    headline_text = "\n".join(f"- {h['title']}" for h in headlines[:5]) or "No recent headlines found."

    prompt = f"""You are a cautious equity research assistant. Based only on the data below,
write a 3-sentence explanation of why {stock_name} was shortlisted, and one key risk to watch.
Do not invent facts not present in the data. Be concise and factual.

Technicals: {indicators}
Suggested levels: {levels}
Recent headlines:
{headline_text}
"""

    if config.GROQ_API_KEY:
        return _call_groq(prompt)
    if config.ANTHROPIC_API_KEY:
        return _call_anthropic(prompt)

    # Free fallback: template, no LLM call
    return (
        f"{stock_name} was shortlisted on technical setup (RSI {indicators.get('rsi')}, "
        f"price vs SMA20/50: {indicators.get('last_close')} vs {indicators.get('sma20')}/{indicators.get('sma50')}). "
        f"Recent news tone: see flagged headlines. Risk: technical scores can reverse quickly on broader market moves; "
        f"this is not a guarantee of direction."
    )


def _call_groq(prompt: str) -> str:
    import requests
    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {config.GROQ_API_KEY}"},
            json={
                "model": "llama-3.1-8b-instant",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 200,
            },
            timeout=15,
        )
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"(LLM reasoning unavailable: {e})"


def _call_anthropic(prompt: str) -> str:
    import requests
    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": config.ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-sonnet-4-6",
                "max_tokens": 200,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=15,
        )
        return r.json()["content"][0]["text"].strip()
    except Exception as e:
        return f"(LLM reasoning unavailable: {e})"
