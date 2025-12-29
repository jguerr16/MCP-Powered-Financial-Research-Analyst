"""Price and market cap fetch wrapper (optional)."""

from typing import Optional


def fetch_current_price(ticker: str) -> Optional[float]:
    """
    Fetch current stock price.

    Args:
        ticker: Stock ticker symbol

    Returns:
        Current price or None if unavailable
    """
    # TODO: Implement actual pricing provider
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

