"""
Insider trade signal scorer.

Scoring philosophy:
  - Open Market Purchase (Code P) with NO 10b5-1 plan is the highest-conviction signal.
    Insiders are putting their own capital at risk with no obligation to do so.
  - Option Exercises (Code M) are routinely scheduled and carry minimal signal.
  - 10b5-1 plan sales are noise — pre-arranged for tax/diversification, not conviction.
  - Cluster Buying (≥2 distinct insiders buying the same ticker within 48 hours) amplifies signal.

Signal scale:
  STRONG_BUY  conviction ≥ 7.0
  BUY         conviction ≥ 4.0
  NEUTRAL     conviction ≥ 1.5
  SELL        conviction ≥ 0.5 (net disposition)
  STRONG_SELL conviction < 0.5
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional

from app.insiders.models import InsiderTrade, InsiderTradeOut, InsiderSignal

# Base conviction multipliers by transaction code
_CODE_WEIGHT: dict[str, float] = {
    "P": 3.0,   # Open market purchase — highest signal
    "A": 0.2,   # Grant/award — noise (company gave it)
    "M": 0.3,   # Option exercise — scheduled, low signal
    "C": 0.3,   # Conversion — structural
    "S": -1.5,  # Open market sale
    "D": -0.5,  # Disposition to issuer
    "F": -0.2,  # Tax withholding (sell to cover)
    "G": 0.1,   # Gift
    "W": 0.1,   # Inheritance
}


def _parse_date(date_str: str) -> Optional[datetime]:
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y%m%d"):
        try:
            return datetime.strptime(date_str, fmt)
        except (ValueError, TypeError):
            continue
    return None


def _value_score(total_value: Optional[float]) -> float:
    """Log-scale score based on dollar value of the transaction."""
    if not total_value or total_value <= 0:
        return 0.5
    if total_value >= 5_000_000:
        return 3.0
    if total_value >= 1_000_000:
        return 2.0
    if total_value >= 500_000:
        return 1.5
    if total_value >= 100_000:
        return 1.0
    return 0.5


def _role_multiplier(trade: InsiderTrade) -> float:
    """CEO/CFO/Chairman buys carry more weight than a minor director."""
    title = (trade.officer_title or "").upper()
    if any(t in title for t in ("CEO", "CHIEF EXEC", "CHAIRMAN", "PRESIDENT")):
        return 1.4
    if any(t in title for t in ("CFO", "CHIEF FIN", "CHIEF OPERATING", "COO")):
        return 1.25
    if trade.owner_is_officer:
        return 1.1
    if trade.owner_is_director:
        return 1.0
    if trade.owner_is_ten_pct:
        return 0.9
    return 0.8


def _detect_cluster(trades: list[InsiderTrade]) -> tuple[bool, Optional[str]]:
    """Cluster = ≥2 distinct insiders making open-market buys within 48h."""
    buys = [
        t for t in trades
        if t.transaction_code == "P" and not t.is_10b51_plan and t.transaction_date
    ]
    if len(buys) < 2:
        return False, None

    # Group by date and find overlapping 48h windows
    by_date = defaultdict(set)
    for b in buys:
        d = _parse_date(b.transaction_date)
        if d:
            for key_d in (d - timedelta(days=1), d, d + timedelta(days=1)):
                by_date[key_d.strftime("%Y-%m-%d")].add(b.owner_name)

    for date_key, owners in by_date.items():
        if len(owners) >= 2:
            names = ", ".join(sorted(owners))
            total = sum(t.total_value or 0 for t in buys)
            return True, (
                f"Cluster buying detected: {len(owners)} insiders "
                f"({names}) bought near {date_key} — "
                f"combined value ${total:,.0f}"
            )
    return False, None


def score_trades(trades: list[InsiderTrade]) -> InsiderSignal:
    """Aggregate a list of InsiderTrade rows into a single InsiderSignal."""
    if not trades:
        ticker = "UNKNOWN"
        return InsiderSignal(
            ticker=ticker,
            signal_type="NEUTRAL",
            conviction_score=0.0,
            rationale="No trades found.",
            trades=[],
        )

    ticker = trades[0].issuer_ticker
    raw_score = 0.0
    rationale_parts: list[str] = []

    for t in trades:
        base = _CODE_WEIGHT.get(t.transaction_code, 0.0)
        # Non-plan buys are the alpha signal
        if t.transaction_code == "P" and not t.is_10b51_plan:
            base *= 1.5
            rationale_parts.append(
                f"Non-plan open-market buy by {t.owner_name} "
                f"(${(t.total_value or 0):,.0f}) on {t.transaction_date}"
            )
        elif t.transaction_code in ("S", "D") and not t.is_10b51_plan:
            rationale_parts.append(
                f"Non-plan sale by {t.owner_name} "
                f"(${(t.total_value or 0):,.0f}) on {t.transaction_date}"
            )
        elif t.is_10b51_plan:
            rationale_parts.append(
                f"10b5-1 plan transaction by {t.owner_name} (reduced weight)"
            )

        contribution = base * _value_score(t.total_value) * _role_multiplier(t)
        raw_score += contribution

    # Normalise to 0–10
    conviction = max(0.0, min(10.0, raw_score))

    cluster, cluster_desc = _detect_cluster(trades)
    if cluster:
        conviction = min(10.0, conviction * 1.3)  # Boost for cluster
        rationale_parts.insert(0, cluster_desc or "")

    if conviction >= 7.0:
        signal_type = "STRONG_BUY"
    elif conviction >= 4.0:
        signal_type = "BUY"
    elif conviction <= -4.0:
        signal_type = "STRONG_SELL"
    elif conviction <= -1.5:
        signal_type = "SELL"
    else:
        signal_type = "NEUTRAL"

    trade_outs = [
        InsiderTradeOut.model_validate(t, from_attributes=True)
        for t in trades
    ]

    return InsiderSignal(
        ticker=ticker,
        signal_type=signal_type,
        conviction_score=round(conviction, 2),
        rationale=" | ".join(rationale_parts[:5]) or "Mixed / routine transactions.",
        trades=trade_outs,
        cluster_detected=cluster,
        cluster_description=cluster_desc,
    )
