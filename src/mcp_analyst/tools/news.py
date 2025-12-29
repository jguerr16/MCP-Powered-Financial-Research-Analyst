"""News search wrapper (pluggable)."""

from typing import List

from mcp_analyst.schemas.sources import SourceItem


def fetch_news(ticker: str) -> List[SourceItem]:
    """
    Fetch news articles for a ticker.

    Args:
        ticker: Stock ticker symbol

    Returns:
        List of source items (news articles)

    Note:
        This is a pluggable interface. v1 returns stub data.
    """
    # TODO: Implement actual news provider integration
    # For v1, return empty list
    return []

