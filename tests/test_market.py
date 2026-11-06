from datetime import UTC, datetime

import pytest

from dcf_valuation.market import get_quote, validate_quote


def test_snapshot_has_traceable_price_and_never_calls_network(monkeypatch):
    import yfinance

    monkeypatch.setattr(yfinance, "Ticker", lambda _: pytest.fail("offline used network"))
    quote = get_quote()
    assert quote["mode"] == "snapshot"
    assert quote["price"] > 0
    assert quote["source_url"].startswith("https://finance.yahoo.com/")


@pytest.mark.parametrize("patch", [
    {"price": float("nan")}, {"price": 0}, {"price": True},
    {"currency": "USD"}, {"ticker": "PETR4.SA"},
    {"timestamp": "2026-11-06"}, {"timestamp": "bad"},
    {"timestamp": "2099-01-01T00:00:00+00:00"},
])
def test_invalid_quote(patch):
    with pytest.raises(ValueError):
        validate_quote({**get_quote(), **patch})


@pytest.mark.parametrize("timestamp", [datetime.now(UTC), datetime.now(UTC).timestamp()])
def test_live_quote_and_failed_live_request_are_explicit(monkeypatch, timestamp):
    import yfinance

    class Ticker:
        def get_history_metadata(self):
            return {
                "symbol": "WEGE3.SA", "currency": "BRL", "regularMarketPrice": 48.0,
                "regularMarketTime": timestamp,
            }

    monkeypatch.setattr(yfinance, "Ticker", lambda _: Ticker())
    assert get_quote(live=True)["mode"] == "live"
    monkeypatch.setattr(Ticker, "get_history_metadata", lambda _: {})
    with pytest.raises(ValueError, match="Could not obtain"):
        get_quote(live=True)
