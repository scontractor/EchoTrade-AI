from __future__ import annotations

import logging
from typing import Any

import yfinance as yf

logger = logging.getLogger(__name__)

# BRK.B displays as BRK.B in the UI but Yahoo Finance uses BRK-B
SYMBOLS: list[tuple[str, str]] = [
    ("AAPL",  "AAPL"),
    ("MSFT",  "MSFT"),
    ("NVDA",  "NVDA"),
    ("AMZN",  "AMZN"),
    ("META",  "META"),
    ("GOOGL", "GOOGL"),
    ("BRK.B", "BRK-B"),
    ("TSM",   "TSM"),
    ("TSLA",  "TSLA"),
    ("JPM",   "JPM"),
    ("V",     "V"),
    ("UNH",   "UNH"),
    ("XOM",   "XOM"),
    ("BAC",   "BAC"),
    ("WMT",   "WMT"),
    ("HD",    "HD"),
    ("CVX",   "CVX"),
    ("MRK",   "MRK"),
]


def fetch_prices() -> list[dict[str, Any]]:
    """Fetch ~15-min delayed prices from Yahoo Finance via yfinance."""
    yahoo_symbols = [yf_sym for _, yf_sym in SYMBOLS]
    result: list[dict[str, Any]] = []
    try:
        tickers = yf.Tickers(" ".join(yahoo_symbols))
        for display_sym, yf_sym in SYMBOLS:
            try:
                info = tickers.tickers[yf_sym].fast_info
                price = info.last_price
                prev = info.previous_close
                if price is not None and prev:
                    chg_pct = round((price - prev) / prev * 100, 2)
                    result.append({"sym": display_sym, "price": round(float(price), 2), "chg_pct": chg_pct})
                else:
                    result.append({"sym": display_sym, "price": None, "chg_pct": None})
            except Exception:
                logger.warning("Price fetch failed for %s", yf_sym)
                result.append({"sym": display_sym, "price": None, "chg_pct": None})
    except Exception as exc:
        logger.error("yfinance batch fetch failed: %s", exc)
    return result
