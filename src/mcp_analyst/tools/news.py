"""News search wrapper with Event Registry (newsapi.ai) integration."""

import os
from datetime import datetime, timedelta
from typing import List, Optional

from mcp_analyst.config import Config
from mcp_analyst.schemas.sources import SourceItem


def search_news(
    query: str, from_date: Optional[str] = None, limit: int = 20
) -> List[SourceItem]:
    """
    Search news using Event Registry (newsapi.ai).

    Args:
        query: Search query (keywords or company name)
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
        from eventregistry import EventRegistry, QueryArticlesIter

        # Initialize Event Registry
        er = EventRegistry(apiKey=Config.NEWS_API_KEY)

        # Convert from_date to datetime for Event Registry
        from_date_obj = datetime.strptime(from_date, "%Y-%m-%d")

        # Create query for articles
        # Event Registry uses keyword search
        q = QueryArticlesIter(
            keywords=query,
            dateStart=from_date_obj,
            dataType=["news", "blog"],  # Include both news and blog posts
        )

        sources = []
        article_count = 0

        # Execute query and get articles
        try:
            for art in q.execQuery(er, sortBy="date", maxItems=limit):
                if article_count >= limit:
                    break

                # Extract article data - Event Registry returns dict-like objects
                # Access as dict or attributes depending on format
                if hasattr(art, 'get'):
                    # Dict-like access
                    title = art.get("title", "") or art.get("title", "")
                    url = art.get("url", "") or art.get("url", "")
                    published_at = art.get("date", "") or art.get("date", "")
                    description = (art.get("body", "") or art.get("body", ""))[:500] if art.get("body") else ""
                    source_info = art.get("source", {}) or {}
                    source_name = source_info.get("title", "") if isinstance(source_info, dict) else str(source_info)
                    sentiment = art.get("sentiment", 0) or art.get("sentiment", 0)
                else:
                    # Attribute access
                    title = getattr(art, "title", "") or ""
                    url = getattr(art, "url", "") or ""
                    published_at = getattr(art, "date", "") or ""
                    description = (getattr(art, "body", "") or "")[:500]
                    source_obj = getattr(art, "source", None)
                    source_name = getattr(source_obj, "title", "") if source_obj else ""
                    sentiment = getattr(art, "sentiment", 0) or 0

                # Parse date
                date_obj = None
                if published_at:
                    try:
                        # Event Registry returns dates in various formats
                        if isinstance(published_at, str):
                            # Try ISO format first
                            try:
                                date_obj = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
                            except ValueError:
                                # Try other common formats
                                for fmt in ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"]:
                                    try:
                                        date_obj = datetime.strptime(str(published_at)[:19], fmt)
                                        break
                                    except ValueError:
                                        continue
                        elif isinstance(published_at, (int, float)):
                            # Unix timestamp
                            date_obj = datetime.fromtimestamp(published_at)
                    except Exception:
                        date_obj = None

                source = SourceItem(
                    source_id=f"news_{hash(url) if url else hash(title)}",
                    source_type="news",
                    ticker="",  # Will be set by caller
                    title=title,
                    url=url,
                    date=date_obj,
                    metadata={
                        "source": source_name,
                        "description": description,
                        "publishedAt": str(published_at) if published_at else "",
                        "sentiment": float(sentiment) if sentiment else 0,  # Event Registry provides sentiment
                    },
                )
                sources.append(source)
                article_count += 1
        except Exception as query_error:
            print(f"Event Registry query error: {type(query_error).__name__}: {query_error}")
            # Return empty list if query fails
            return []

        return sources
    except ImportError:
        print("Event Registry package not installed. Install with: pip install eventregistry")
        return []
    except Exception as e:
        # Log errors for debugging
        print(f"Event Registry error: {type(e).__name__}: {e}")
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
    # Use company name or ticker as base query
    base_query = company_name or ticker
    
    # Event Registry works better with simpler queries
    # Search for the company/ticker first, then filter by keywords in the results
    all_sources = []
    seen_urls = set()
    
    # Primary search: just the company name/ticker
    primary_sources = search_news(base_query, limit=30)
    
    # Filter for material events by checking title/description for keywords
    material_keywords = {
        'm_and_a': ['deal', 'acquisition', 'merger', 'partnership', 'joint venture', 'takeover'],
        'litigation': ['lawsuit', 'litigation', 'regulatory', 'sec', 'investigation', 'settlement', 'fine'],
        'guidance': ['guidance', 'earnings', 'forecast', 'outlook', 'revenue', 'profit'],
        'macro': ['recession', 'rates', 'inflation', 'economy', 'fed', 'interest'],
    }
    
    for source in primary_sources:
        if source.url and source.url not in seen_urls:
            # Check if article contains material event keywords
            title_lower = (source.title or "").lower()
            desc_lower = (source.metadata.get("description", "") if source.metadata else "").lower()
            text = f"{title_lower} {desc_lower}"
            
            # Categorize by keywords
            category = "general"
            for cat, keywords in material_keywords.items():
                if any(kw in text for kw in keywords):
                    category = cat
                    break
            
            # Only include if it's a material event or has high relevance
            if category != "general" or len(primary_sources) < 20:
                source.ticker = ticker
                all_sources.append(source)
                seen_urls.add(source.url)

    # Sort by date (most recent first)
    all_sources.sort(
        key=lambda x: x.date if x.date else datetime.min, reverse=True
    )

    return all_sources[:20]  # Return top 20
