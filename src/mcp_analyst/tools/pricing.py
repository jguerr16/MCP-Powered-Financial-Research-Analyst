"""Price and market cap fetch wrapper using Yahoo Finance."""

import logging
from datetime import datetime, timezone
from typing import Optional

import yfinance as yf

from mcp_analyst.schemas.pricing import QuoteData
from mcp_analyst.tools.cache import get_cached, set_cached

logger = logging.getLogger(__name__)


def _normalize_ticker(ticker: str) -> str:
    """Normalize ticker: uppercase and strip whitespace."""
    return ticker.upper().strip()


def _get_cache_key(ticker: str) -> str:
    """Get cache key for ticker."""
    return f"quote_{_normalize_ticker(ticker)}"


def _is_cache_valid(cached_data: dict, ttl_seconds: int) -> bool:
    """Check if cached data is still valid based on TTL."""
    if not cached_data or "as_of_utc" not in cached_data:
        return False

    try:
        cached_time = datetime.fromisoformat(cached_data["as_of_utc"])
        age_seconds = (datetime.now(timezone.utc) - cached_time).total_seconds()
        return age_seconds < ttl_seconds
    except Exception:
        return False


def fetch_quote(ticker: str, ttl_seconds: int = 600) -> QuoteData:
    """
    Fetch quote data from Yahoo Finance with caching.

    Args:
        ticker: Stock ticker symbol
        ttl_seconds: Cache TTL in seconds (default: 600 = 10 minutes)

    Returns:
        QuoteData with price, market_cap, beta, etc. (fields may be None if unavailable)
    """
    ticker = _normalize_ticker(ticker)
    cache_key = _get_cache_key(ticker)

    # Check cache
    cached = get_cached(cache_key)
    if cached and _is_cache_valid(cached, ttl_seconds):
        logger.debug(f"Using cached quote for {ticker}")
        return QuoteData(**cached)

    # Fetch from Yahoo Finance
    logger.info(f"Fetching quote for {ticker} from Yahoo Finance")
    quote = QuoteData(
        ticker=ticker,
        as_of_utc=datetime.now(timezone.utc).isoformat(),
        source="yahoo_finance",
    )

    try:
        t = yf.Ticker(ticker)

        # Try fast_info first (faster)
        try:
            fast_info = t.fast_info
            if hasattr(fast_info, "last_price") and fast_info.last_price:
                quote.price = float(fast_info.last_price)
            elif hasattr(fast_info, "lastPrice") and fast_info.lastPrice:
                quote.price = float(fast_info.lastPrice)

            if hasattr(fast_info, "market_cap") and fast_info.market_cap:
                quote.market_cap = float(fast_info.market_cap)
            elif hasattr(fast_info, "marketCap") and fast_info.marketCap:
                quote.market_cap = float(fast_info.marketCap)

            if hasattr(fast_info, "shares") and fast_info.shares:
                quote.shares_out = float(fast_info.shares)

            if hasattr(fast_info, "currency") and fast_info.currency:
                quote.currency = str(fast_info.currency)
        except Exception as e:
            logger.debug(f"fast_info failed for {ticker}: {e}, falling back to info")

        # Fallback to info for missing fields
        info = t.info
        if info:
            if quote.price is None:
                if "regularMarketPrice" in info and info["regularMarketPrice"]:
                    quote.price = float(info["regularMarketPrice"])
                elif "currentPrice" in info and info["currentPrice"]:
                    quote.price = float(info["currentPrice"])

            if quote.market_cap is None:
                if "marketCap" in info and info["marketCap"]:
                    quote.market_cap = float(info["marketCap"])

            if quote.beta is None:
                if "beta" in info and info["beta"] is not None:
                    quote.beta = float(info["beta"])

            if quote.shares_out is None:
                if "sharesOutstanding" in info and info["sharesOutstanding"]:
                    quote.shares_out = float(info["sharesOutstanding"])

            if quote.currency is None:
                if "currency" in info and info["currency"]:
                    quote.currency = str(info["currency"])

    except Exception as e:
        logger.warning(f"Failed to fetch quote for {ticker}: {e}")
        # Return quote with None fields but valid timestamp

    # Cache the result
    try:
        cache_data = quote.model_dump()
        set_cached(cache_key, cache_data)
    except Exception as e:
        logger.debug(f"Failed to cache quote for {ticker}: {e}")

    return quote


def fetch_current_price(ticker: str) -> Optional[float]:
    """
    Fetch current stock price (backwards compatible).

    Args:
        ticker: Stock ticker symbol

    Returns:
        Current price or None if unavailable
    """
    quote = fetch_quote(ticker)
    return quote.price


def fetch_market_cap(ticker: str) -> Optional[float]:
    """
    Fetch market capitalization.

    Args:
        ticker: Stock ticker symbol

    Returns:
        Market cap or None if unavailable
    """
    quote = fetch_quote(ticker)
    return quote.market_cap
