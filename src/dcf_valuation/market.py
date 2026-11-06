"""An explicit, timestamped Yahoo quote or the versioned offline snapshot."""

from datetime import UTC, datetime, timedelta

from .model import load_data
from .validation import number


def validate_quote(quote: dict) -> dict:
    """Reject mismatched instruments, invalid prices and ambiguous timestamps."""
    if quote.get("ticker") != "WEGE3.SA" or quote.get("currency") != "BRL":
        raise ValueError("Expected WEGE3.SA quoted in BRL")
    if number(quote.get("price"), "quote.price", 0) == 0:
        raise ValueError("quote.price must be positive")
    for key in ("timestamp", "fetched_at"):
        try:
            stamp = datetime.fromisoformat(quote[key])
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(f"quote.{key} must be an ISO timestamp") from error
        if stamp.tzinfo is None:
            raise ValueError(f"quote.{key} needs a timezone")
    if datetime.fromisoformat(quote["timestamp"]) > (
        datetime.fromisoformat(quote["fetched_at"]) + timedelta(minutes=5)
    ):
        raise ValueError("Market timestamp is later than retrieval time")
    return quote


def get_quote(live: bool = False) -> dict:
    """Offline by default. A failed live request never silently returns old data."""
    if not live:
        return validate_quote({**load_data()["quote"], "mode": "snapshot"})
    import yfinance as yf

    try:
        metadata = yf.Ticker("WEGE3.SA").get_history_metadata()
        market_time = metadata["regularMarketTime"]
        if not isinstance(market_time, datetime):
            market_time = datetime.fromtimestamp(market_time, UTC)
        quote = {
            "ticker": metadata["symbol"],
            "currency": metadata["currency"],
            "price": metadata["regularMarketPrice"],
            "timestamp": market_time.isoformat(),
            "fetched_at": datetime.now(UTC).isoformat(),
            "source_url": "https://finance.yahoo.com/quote/WEGE3.SA/",
            "provider": "Yahoo Finance via yfinance; regularMarketPrice (may be delayed)",
            "mode": "live",
        }
        return validate_quote(quote)
    except Exception as error:
        raise ValueError(f"Could not obtain a valid current Yahoo quote: {error}") from error
