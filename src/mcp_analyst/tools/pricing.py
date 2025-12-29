"""Price and market cap fetch wrapper."""

from typing import Optional

from mcp_analyst.tools.cache import get_cached, set_cached


def fetch_current_price(ticker: str) -> Optional[float]:
    """
    Fetch current stock price.

    Args:
        ticker: Stock ticker symbol

    Returns:
        Current price or None if unavailable

    Note:
        This is a placeholder. In production, integrate with:
        - Alpha Vantage API
        - Yahoo Finance API
        - IEX Cloud
        - Polygon.io
    """
    cache_key = f"price_{ticker}"
    cached = get_cached(cache_key)
    if cached:
        return cached

    # TODO: Implement actual pricing provider
    # For now, return None (will show as N/A in Excel)
    return None


def fetch_market_cap(ticker: str) -> Optional[float]:
    """
    Fetch market capitalization.

    Args:
        ticker: Stock ticker symbol

    Returns:
        Market cap or None if unavailable
    """
    # TODO: Implement actual market cap fetch
    return None
