from app.insiders.models import InsiderTrade
from app.insiders.scorer import score_trades

_DEFAULTS = dict(
    accession_number="0001-26-000001",
    filing_date="2026-08-01",
    issuer_cik="0000123",
    issuer_ticker="ACME",
    issuer_name="Acme Corp",
    owner_cik="0000456",
    owner_name="Jane Doe",
    owner_is_director=False,
    owner_is_officer=False,
    owner_is_ten_pct=False,
    officer_title=None,
    transaction_sequence=1,
    transaction_date="2026-08-01",
    security_title="Common Stock",
    transaction_code="P",
    transaction_code_label="Open Market Purchase",
    acquired_or_disposed="A",
    shares=1000.0,
    price_per_share=50.0,
    total_value=50_000.0,
    shares_owned_after=5000.0,
    is_10b51_plan=False,
    plan_adoption_date=None,
)


def _trade(**overrides) -> InsiderTrade:
    return InsiderTrade(**{**_DEFAULTS, **overrides})


def test_no_trades_returns_neutral_placeholder():
    signal = score_trades([])

    assert signal.ticker == "UNKNOWN"
    assert signal.signal_type == "NEUTRAL"
    assert signal.conviction_score == 0.0
    assert signal.rationale == "No trades found."
    assert signal.trades == []


def test_large_non_plan_ceo_buy_is_strong_buy():
    trade = _trade(
        owner_name="CEO Jane",
        officer_title="Chief Executive Officer",
        owner_is_officer=True,
        transaction_code="P",
        is_10b51_plan=False,
        total_value=6_000_000.0,
    )

    signal = score_trades([trade])

    assert signal.ticker == "ACME"
    assert signal.signal_type == "STRONG_BUY"
    assert signal.conviction_score >= 7.0
    assert "Non-plan open-market buy" in signal.rationale
    assert signal.cluster_detected is False


def test_10b51_plan_sale_is_flagged_as_reduced_weight():
    # Edge case: pre-arranged 10b5-1 sales are noise, not a conviction signal —
    # the rationale should say so even though the raw score is negative.
    trade = _trade(
        owner_name="VP Bob",
        officer_title="VP Engineering",
        owner_is_officer=True,
        transaction_code="S",
        is_10b51_plan=True,
        total_value=200_000.0,
    )

    signal = score_trades([trade])

    assert "10b5-1 plan transaction" in signal.rationale
    assert "reduced weight" in signal.rationale


def test_large_non_plan_ceo_sale_is_strong_sell():
    # Regression: conviction used to be floored at 0.0 before the signal_type
    # thresholds were checked, so STRONG_SELL/SELL were unreachable dead code —
    # every net-sell trade resolved to NEUTRAL regardless of size.
    trade = _trade(
        owner_name="CEO Jane",
        officer_title="Chief Executive Officer",
        owner_is_officer=True,
        transaction_code="S",
        is_10b51_plan=False,
        total_value=6_000_000.0,
    )

    signal = score_trades([trade])

    assert signal.signal_type == "STRONG_SELL"
    assert signal.conviction_score > 0  # magnitude is always unsigned/positive
    assert "Non-plan sale" in signal.rationale


def test_moderate_non_plan_sale_is_sell():
    trade = _trade(
        owner_name="Director Bob",
        officer_title="Director of Sales",
        owner_is_officer=True,
        transaction_code="S",
        is_10b51_plan=False,
        total_value=150_000.0,
    )

    signal = score_trades([trade])

    assert signal.signal_type == "SELL"
    assert signal.conviction_score > 0


def test_cluster_buying_across_two_insiders_boosts_conviction():
    alice = _trade(owner_name="Alice", transaction_date="2026-08-01", total_value=200_000.0)
    bob = _trade(owner_name="Bob", transaction_date="2026-08-02", total_value=200_000.0)

    solo_signal = score_trades([alice])
    cluster_signal = score_trades([alice, bob])

    assert cluster_signal.cluster_detected is True
    assert "Alice" in cluster_signal.cluster_description
    assert "Bob" in cluster_signal.cluster_description
    # cluster boost (x1.3) should push combined conviction above what one buyer alone would produce
    assert cluster_signal.conviction_score > solo_signal.conviction_score


def test_same_insider_buying_twice_is_not_a_cluster():
    # Edge case: cluster requires >=2 *distinct* insiders, not just >=2 trades.
    first = _trade(owner_name="Alice", transaction_date="2026-08-01")
    second = _trade(owner_name="Alice", transaction_date="2026-08-02")

    signal = score_trades([first, second])

    assert signal.cluster_detected is False
    assert signal.cluster_description is None
