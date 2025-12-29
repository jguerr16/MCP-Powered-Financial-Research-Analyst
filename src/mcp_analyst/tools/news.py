"""News search wrapper with NewsAPI integration."""

import os
from datetime import datetime, timedelta
from typing import List, Optional

from mcp_analyst.config import Config
from mcp_analyst.schemas.sources import SourceItem


def search_news(
    query: str, from_date: Optional[str] = None, limit: int = 20
) -> List[SourceItem]:
    """
    Search news using NewsAPI.

    Args:
        query: Search query
        from_date: Start date (YYYY-MM-DD), defaults to 30 days ago
        limit: Maximum number of results

    Returns:
        List of source items (news articles)
    """
    if not Config.NEWS_API_KEY:
        # Return empty if no API key
        return []

    if not from_date:
        # Default to 30 days ago
        from_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

    try:
        import requests

        url = "https://newsapi.org/v2/everything"
        params = {
            "q": query,
            "from": from_date,
            "sortBy": "publishedAt",
            "pageSize": min(limit, 100),
            "apiKey": Config.NEWS_API_KEY,
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        articles = data.get("articles", [])
        sources = []

        for article in articles[:limit]:
            published_at = article.get("publishedAt")
            try:
                if published_at:
                    date_obj = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
                else:
                    date_obj = None
            except Exception:
                date_obj = None

            source = SourceItem(
                source_id=f"news_{hash(article.get('url', ''))}",
                source_type="news",
                ticker="",  # Will be set by caller
                title=article.get("title", ""),
                url=article.get("url", ""),
                date=date_obj,
                metadata={
                    "source": article.get("source", {}).get("name", ""),
                    "description": article.get("description", ""),
                    "publishedAt": published_at,
                },
            )
            sources.append(source)

        return sources
    except Exception:
        # Fail silently if API call fails
        return []


def fetch_news(ticker: str, company_name: Optional[str] = None) -> List[SourceItem]:
    """
    Fetch news articles for a ticker with material events filtering.

    Args:
        ticker: Stock ticker symbol
        company_name: Optional company name for better search

    Returns:
        List of source items (news articles)
    """
    # Build search queries for material events
    base_query = company_name or ticker

    queries = [
        f'"{base_query}" AND (deal OR acquisition OR merger OR partnership OR joint venture)',
        f'"{base_query}" AND (lawsuit OR litigation OR regulatory OR SEC OR investigation)',
        f'"{base_query}" AND (guidance OR earnings OR forecast OR outlook)',
        f'"{base_query}" AND (macro OR recession OR rates OR inflation OR economy)',
    ]

    all_sources = []
    seen_urls = set()

    for query in queries:
        sources = search_news(query, limit=10)
        for source in sources:
            if source.url and source.url not in seen_urls:
                source.ticker = ticker
                all_sources.append(source)
                seen_urls.add(source.url)

    # Sort by date (most recent first)
    all_sources.sort(
        key=lambda x: x.date if x.date else datetime.min, reverse=True
    )

    return all_sources[:20]  # Return top 20
