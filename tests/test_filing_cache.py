import pytest

from app.edgar.cache import FilingCache

# In-memory SQLite — fast, isolated, discarded after each test
_DB = "sqlite://"

SNAPSHOT = {
    "accession_number": "0001234567-24-000001",
    "cik": "0000102909",
    "investor_name": "Test Fund",
    "period_of_report": "2024-03-31",
    "filing_date": "2024-05-15",
    "holdings": [
        {
            "cusip": "037833100",
            "company_name": "Apple Inc.",
            "title_of_class": "COM",
            "value_thousands": 500000,
            "shares": 3000000,
            "investment_discretion": "SOLE",
            "ticker": "AAPL",
            "put_call": None,
        }
    ],
}


def test_miss_returns_none():
    cache = FilingCache(_DB)
    assert cache.get("nonexistent-accession") is None


def test_put_then_get_round_trip():
    cache = FilingCache(_DB)
    cache.put(SNAPSHOT)
    result = cache.get(SNAPSHOT["accession_number"])

    assert result is not None
    assert result["investor_name"] == "Test Fund"
    assert result["period_of_report"] == "2024-03-31"
    assert len(result["holdings"]) == 1
    assert result["holdings"][0]["ticker"] == "AAPL"


def test_put_is_idempotent():
    cache = FilingCache(_DB)
    cache.put(SNAPSHOT)
    cache.put(SNAPSHOT)  # second put should not raise or duplicate
    result = cache.get(SNAPSHOT["accession_number"])
    assert result is not None
