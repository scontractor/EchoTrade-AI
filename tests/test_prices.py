from unittest.mock import MagicMock, patch

from app.prices import fetch_prices


def _make_fast_info(last_price, previous_close):
    fi = MagicMock()
    fi.last_price = last_price
    fi.previous_close = previous_close
    return fi


def _patch_tickers(fast_infos: dict):
    """Build a mock yf.Tickers object from {yahoo_sym: fast_info} mapping."""
    mock_tickers = MagicMock()
    mock_tickers.tickers = {sym: MagicMock(fast_info=fi) for sym, fi in fast_infos.items()}
    return mock_tickers


def test_happy_path():
    fi = {"AAPL": _make_fast_info(200.0, 195.0)}
    with patch("app.prices.yf.Tickers", return_value=_patch_tickers(fi)):
        results = fetch_prices()
    aapl = next(r for r in results if r["sym"] == "AAPL")
    assert aapl["price"] == 200.0
    assert aapl["chg_pct"] == round((200.0 - 195.0) / 195.0 * 100, 2)


def test_null_price_returned_when_yfinance_gives_none():
    fi = {"AAPL": _make_fast_info(None, None)}
    with patch("app.prices.yf.Tickers", return_value=_patch_tickers(fi)):
        results = fetch_prices()
    aapl = next(r for r in results if r["sym"] == "AAPL")
    assert aapl["price"] is None
    assert aapl["chg_pct"] is None


def test_single_symbol_failure_does_not_break_others():
    fi = {
        "AAPL": MagicMock(fast_info=MagicMock(side_effect=Exception("timeout"))),
        "MSFT": _make_fast_info(400.0, 395.0),
    }
    mock_tickers = MagicMock()
    mock_tickers.tickers = {
        "AAPL": MagicMock(**{"fast_info": MagicMock(side_effect=Exception("timeout"))}),
        "MSFT": MagicMock(fast_info=_make_fast_info(400.0, 395.0)),
    }
    with patch("app.prices.yf.Tickers", return_value=mock_tickers):
        results = fetch_prices()
    msft = next(r for r in results if r["sym"] == "MSFT")
    assert msft["price"] == 400.0


def test_all_symbols_present_in_output():
    # Even on total yfinance failure, every symbol gets a null entry
    with patch("app.prices.yf.Tickers", side_effect=Exception("network error")):
        results = fetch_prices()
    assert results == []  # batch failure returns empty; frontend falls back to ---
