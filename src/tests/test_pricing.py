"""Tests for pricing module."""

from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

import pytest

from mcp_analyst.schemas.pricing import QuoteData
from mcp_analyst.tools.pricing import _is_cache_valid, _normalize_ticker, fetch_quote


def test_normalize_ticker():
    """Test ticker normalization."""
    assert _normalize_ticker("uber") == "UBER"
    assert _normalize_ticker("  AAPL  ") == "AAPL"
    assert _normalize_ticker("MSFT") == "MSFT"


def test_is_cache_valid():
    """Test cache validation logic."""
    # Valid cache (recent)
    recent_time = datetime.now(timezone.utc) - timedelta(seconds=100)
    cached_data = {"as_of_utc": recent_time.isoformat(), "price": 100.0}
    assert _is_cache_valid(cached_data, ttl_seconds=600) is True

    # Expired cache
    old_time = datetime.now(timezone.utc) - timedelta(seconds=700)
    cached_data = {"as_of_utc": old_time.isoformat(), "price": 100.0}
    assert _is_cache_valid(cached_data, ttl_seconds=600) is False

    # Invalid cache (no timestamp)
    assert _is_cache_valid({}, ttl_seconds=600) is False


@patch("mcp_analyst.tools.pricing.yf.Ticker")
@patch("mcp_analyst.tools.pricing.get_cached")
@patch("mcp_analyst.tools.pricing.set_cached")
def test_fetch_quote_with_cache(mock_set_cached, mock_get_cached, mock_ticker):
    """Test that fetch_quote uses cache when valid."""
    # Mock cached data
    cached_time = datetime.now(timezone.utc) - timedelta(seconds=100)
    cached_quote = {
        "ticker": "UBER",
        "price": 80.0,
        "market_cap": 160000000000.0,
        "beta": 1.2,
        "as_of_utc": cached_time.isoformat(),
        "source": "yahoo_finance",
    }
    mock_get_cached.return_value = cached_quote

    quote = fetch_quote("UBER", ttl_seconds=600)

    # Should return cached data without calling yfinance
    assert quote.price == 80.0
    assert quote.market_cap == 160000000000.0
    assert quote.beta == 1.2
    mock_ticker.assert_not_called()


@patch("mcp_analyst.tools.pricing.yf.Ticker")
@patch("mcp_analyst.tools.pricing.get_cached")
@patch("mcp_analyst.tools.pricing.set_cached")
def test_fetch_quote_from_yahoo(mock_set_cached, mock_get_cached, mock_ticker):
    """Test that fetch_quote calls yfinance when cache is empty."""
    # No cache
    mock_get_cached.return_value = None

    # Mock yfinance response
    mock_ticker_obj = MagicMock()
    mock_fast_info = MagicMock()
    mock_fast_info.last_price = 81.5
    mock_fast_info.market_cap = 170000000000.0
    mock_fast_info.currency = "USD"
    mock_ticker_obj.fast_info = mock_fast_info

    mock_info = {
        "beta": 1.19,
        "sharesOutstanding": 2000000000.0,
    }
    mock_ticker_obj.info = mock_info
    mock_ticker.return_value = mock_ticker_obj

    quote = fetch_quote("UBER", ttl_seconds=600)

    # Should fetch from yfinance
    assert quote.price == 81.5
    assert quote.market_cap == 170000000000.0
    assert quote.beta == 1.19
    assert quote.currency == "USD"
    assert quote.shares_out == 2000000000.0
    mock_ticker.assert_called_once_with("UBER")
    mock_set_cached.assert_called_once()


@patch("mcp_analyst.tools.pricing.yf.Ticker")
@patch("mcp_analyst.tools.pricing.get_cached")
def test_fetch_quote_handles_errors(mock_get_cached, mock_ticker):
    """Test that fetch_quote handles errors gracefully."""
    # No cache
    mock_get_cached.return_value = None

    # Mock yfinance error
    mock_ticker.side_effect = Exception("Network error")

    quote = fetch_quote("UBER", ttl_seconds=600)

    # Should return quote with None fields but valid timestamp
    assert quote.ticker == "UBER"
    assert quote.price is None
    assert quote.market_cap is None
    assert quote.as_of_utc is not None
    assert quote.source == "yahoo_finance"

