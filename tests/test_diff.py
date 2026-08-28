from app.edgar.client import FilingSnapshot, Holding
from app.portfolio.diff import clone_portfolio, compute_diff


def _snapshot(investor_name, period, holdings):
    return FilingSnapshot(
        cik="0000123",
        investor_name=investor_name,
        period_of_report=period,
        filing_date="2026-08-01",
        accession_number="0001-26-000001",
        holdings=holdings,
    )


def _holding(cusip, ticker, shares, value_thousands, company_name=None):
    return Holding(
        cusip=cusip,
        company_name=company_name or ticker,
        title_of_class="COM",
        value_thousands=value_thousands,
        shares=shares,
        investment_discretion="SOLE",
        ticker=ticker,
    )


def test_happy_path_classifies_every_action():
    previous = _snapshot("Acme Capital", "2026-06-30", [
        _holding("AAPL_CUSIP", "AAPL", 100, 1000),   # will increase >5%
        _holding("MSFT_CUSIP", "MSFT", 200, 2000),   # will decrease >5%
        _holding("TSLA_CUSIP", "TSLA", 50, 500),     # will exit
    ])
    current = _snapshot("Acme Capital", "2026-09-30", [
        _holding("AAPL_CUSIP", "AAPL", 150, 1500),   # +50% shares
        _holding("MSFT_CUSIP", "MSFT", 180, 1800),   # -10% shares
        _holding("GOOG_CUSIP", "GOOG", 30, 3000),    # brand new
    ])

    result = compute_diff(current, previous)

    by_cusip = {c.cusip: c for c in result.changes}
    assert by_cusip["AAPL_CUSIP"].action == "INCREASED"
    assert by_cusip["AAPL_CUSIP"].shares_change_pct == 50.0
    assert by_cusip["MSFT_CUSIP"].action == "DECREASED"
    assert by_cusip["TSLA_CUSIP"].action == "EXITED"
    assert by_cusip["TSLA_CUSIP"].curr_shares is None
    assert by_cusip["GOOG_CUSIP"].action == "NEW"
    assert by_cusip["GOOG_CUSIP"].prev_shares is None

    assert result.summary.new_positions == 1
    assert result.summary.exited_positions == 1
    assert result.summary.increased_positions == 1
    assert result.summary.decreased_positions == 1
    assert result.summary.unchanged_positions == 0

    # total value: prev 3500, curr 6300 -> +80%
    assert result.total_value_change_pct == 80.0

    # NEW sorts ahead of INCREASED, which sorts ahead of DECREASED/EXITED
    actions_in_order = [c.action for c in result.changes]
    assert actions_in_order.index("NEW") < actions_in_order.index("INCREASED")
    assert actions_in_order.index("INCREASED") < actions_in_order.index("DECREASED")


def test_small_share_change_within_5pct_is_unchanged():
    previous = _snapshot("Acme Capital", "2026-06-30", [_holding("A", "AAA", 1000, 10000)])
    current = _snapshot("Acme Capital", "2026-09-30", [_holding("A", "AAA", 1020, 10200)])  # +2%

    result = compute_diff(current, previous)

    assert result.changes[0].action == "UNCHANGED"
    assert result.summary.unchanged_positions == 1


def test_zero_previous_shares_does_not_crash():
    # Edge case: a previous filing reporting zero shares (e.g. options-only line)
    # must not raise ZeroDivisionError; the diff engine guards with `if ph.shares`.
    previous = _snapshot("Acme Capital", "2026-06-30", [_holding("A", "AAA", 0, 0)])
    current = _snapshot("Acme Capital", "2026-09-30", [_holding("A", "AAA", 500, 5000)])

    result = compute_diff(current, previous)

    change = result.changes[0]
    assert change.action == "UNCHANGED"  # pct falls back to 0 when ph.shares is falsy
    assert change.shares_change_pct is None


def test_empty_previous_portfolio_does_not_crash():
    # Edge case: no previous holdings at all (e.g. investor's first-ever 13F).
    previous = _snapshot("New Fund", "2026-06-30", [])
    current = _snapshot("New Fund", "2026-09-30", [_holding("A", "AAA", 100, 1000)])

    result = compute_diff(current, previous)

    assert result.changes[0].action == "NEW"
    assert result.total_value_change_pct > 0  # guarded by `total_prev or 1`, no ZeroDivisionError


def test_clone_portfolio_allocates_proportionally():
    snapshot = _snapshot("Acme Capital", "2026-09-30", [
        _holding("A", "AAA", 100, 3000),
        _holding("B", "BBB", 100, 1000),
    ])

    allocations = clone_portfolio(snapshot, capital_usd=10_000, top_n=20)

    by_ticker = {a["ticker"]: a for a in allocations}
    assert by_ticker["AAA"]["allocation_pct"] == 75.0
    assert by_ticker["AAA"]["allocation_usd"] == 7500.0
    assert by_ticker["BBB"]["allocation_pct"] == 25.0
    assert by_ticker["BBB"]["allocation_usd"] == 2500.0


def test_clone_portfolio_respects_top_n_and_handles_empty():
    snapshot = _snapshot("Acme Capital", "2026-09-30", [
        _holding("A", "AAA", 100, 3000),
        _holding("B", "BBB", 100, 1000),
    ])

    top_one = clone_portfolio(snapshot, capital_usd=10_000, top_n=1)
    assert len(top_one) == 1
    assert top_one[0]["ticker"] == "AAA"
    assert top_one[0]["allocation_pct"] == 100.0

    empty_snapshot = _snapshot("Empty Fund", "2026-09-30", [])
    assert clone_portfolio(empty_snapshot, capital_usd=10_000) == []
