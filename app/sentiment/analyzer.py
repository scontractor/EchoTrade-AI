"""
Sentiment layer: fetches recent news via Yahoo Finance RSS and scores it with TextBlob.
Falls back gracefully — a missing ticker or network error returns a neutral score.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import feedparser
from textblob import TextBlob

logger = logging.getLogger(__name__)

_YAHOO_RSS = "https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US"


@dataclass
class TickerSentiment:
    ticker: str
    score: float          # –1.0 (bearish) to +1.0 (bullish)
    label: str            # BULLISH | NEUTRAL | BEARISH
    headline_count: int
    top_headlines: list[str] = field(default_factory=list)


def _score_text(text: str) -> float:
    return TextBlob(text).sentiment.polarity


def analyze_ticker(ticker: str, max_headlines: int = 12) -> TickerSentiment:
    """Fetch RSS headlines for `ticker` and return an aggregate sentiment score."""
    try:
        feed = feedparser.parse(_YAHOO_RSS.format(ticker=ticker))
        entries = feed.entries[:max_headlines]
    except Exception as exc:
        logger.debug("RSS fetch failed for %s: %s", ticker, exc)
        entries = []

    if not entries:
        return TickerSentiment(ticker=ticker, score=0.0, label="NEUTRAL", headline_count=0)

    scores = [_score_text(e.get("title", "") + " " + e.get("summary", "")) for e in entries]
    avg = sum(scores) / len(scores)

    label = "BULLISH" if avg > 0.05 else "BEARISH" if avg < -0.05 else "NEUTRAL"
    headlines = [e.get("title", "") for e in entries[:3]]

    return TickerSentiment(
        ticker=ticker,
        score=round(avg, 3),
        label=label,
        headline_count=len(entries),
        top_headlines=headlines,
    )


def analyze_tickers(tickers: list[str]) -> dict[str, TickerSentiment]:
    return {t: analyze_ticker(t) for t in tickers}
