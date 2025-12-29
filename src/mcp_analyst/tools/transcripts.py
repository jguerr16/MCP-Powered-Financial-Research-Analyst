"""Earnings call transcripts fetch wrapper (pluggable)."""

from typing import List

from mcp_analyst.schemas.sources import SourceItem


def fetch_transcripts(ticker: str) -> List[SourceItem]:
    """
    Fetch earnings call transcripts for a ticker.

    Args:
        ticker: Stock ticker symbol

    Returns:
        List of source items (transcripts)

    Note:
        This is a pluggable interface. v1 returns stub data.
    """
    # TODO: Implement actual transcript provider integration
    # For v1, return empty list
    return []

