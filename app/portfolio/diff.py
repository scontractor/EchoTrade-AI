"""Quarter-over-quarter portfolio diff engine."""

from __future__ import annotations

from app.edgar.client import FilingSnapshot
from app.portfolio.models import HoldingChange, DiffOut, DiffSummary

_ACTION_ORDER = {"NEW": 0, "INCREASED": 1, "DECREASED": 2, "EXITED": 3, "UNCHANGED": 4}


def compute_diff(current: FilingSnapshot, previous: FilingSnapshot) -> DiffOut:
    curr_map = {h.cusip: h for h in current.holdings}
    prev_map = {h.cusip: h for h in previous.holdings}

    total_curr = current.total_value_thousands or 1
    total_prev = previous.total_value_thousands or 1
    total_change_pct = round((total_curr - total_prev) / total_prev * 100, 2)

    changes: list[HoldingChange] = []

    for cusip in set(curr_map) | set(prev_map):
        ch = curr_map.get(cusip)
        ph = prev_map.get(cusip)
        ref = ch or ph

        if ch and not ph:
            action = "NEW"
        elif ph and not ch:
            action = "EXITED"
        elif ch and ph:
            pct = ((ch.shares - ph.shares) / ph.shares * 100) if ph.shares else 0
            if pct > 5:
                action = "INCREASED"
            elif pct < -5:
                action = "DECREASED"
            else:
                action = "UNCHANGED"
        else:
            continue

        shares_chg = None
        val_chg = None
        if ch and ph:
            if ph.shares:
                shares_chg = round((ch.shares - ph.shares) / ph.shares * 100, 1)
            if ph.value_thousands:
                val_chg = round((ch.value_thousands - ph.value_thousands) / ph.value_thousands * 100, 1)

        changes.append(HoldingChange(
            cusip=cusip,
            company_name=ref.company_name,
            ticker=ref.ticker,
            action=action,
            prev_shares=ph.shares if ph else None,
            curr_shares=ch.shares if ch else None,
            shares_change_pct=shares_chg,
            prev_value_thousands=ph.value_thousands if ph else None,
            curr_value_thousands=ch.value_thousands if ch else None,
            value_change_pct=val_chg,
            curr_pct_of_portfolio=round(ch.value_thousands / total_curr * 100, 2) if ch else None,
            prev_pct_of_portfolio=round(ph.value_thousands / total_prev * 100, 2) if ph else None,
        ))

    changes.sort(key=lambda c: (
        _ACTION_ORDER.get(c.action, 5),
        -(c.curr_value_thousands or c.prev_value_thousands or 0),
    ))

    summary = DiffSummary(
        new_positions=sum(1 for c in changes if c.action == "NEW"),
        exited_positions=sum(1 for c in changes if c.action == "EXITED"),
        increased_positions=sum(1 for c in changes if c.action == "INCREASED"),
        decreased_positions=sum(1 for c in changes if c.action == "DECREASED"),
        unchanged_positions=sum(1 for c in changes if c.action == "UNCHANGED"),
    )

    return DiffOut(
        investor_name=current.investor_name,
        current_period=current.period_of_report,
        previous_period=previous.period_of_report,
        total_value_change_pct=total_change_pct,
        summary=summary,
        changes=changes,
    )


def clone_portfolio(snapshot: FilingSnapshot, capital_usd: float, top_n: int = 20) -> list[dict]:
    """Proportionally allocate `capital_usd` across the top_n holdings."""
    top = snapshot.holdings[:top_n]
    top_total = sum(h.value_thousands for h in top) or 1

    return [
        {
            "ticker": h.ticker,
            "company_name": h.company_name,
            "allocation_pct": round(h.value_thousands / top_total * 100, 2),
            "allocation_usd": round(capital_usd * h.value_thousands / top_total, 2),
            "institutional_value_millions": round(h.value_thousands / 1000, 1),
        }
        for h in top
    ]
