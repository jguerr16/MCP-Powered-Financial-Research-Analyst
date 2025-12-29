"""News analysis agent for sentiment and materiality scoring."""

from datetime import datetime, timedelta
from typing import List, Optional

from mcp_analyst.schemas.sources import SourceItem


class MaterialEvent:
    """Material event from news with sentiment and scoring."""

    def __init__(
        self,
        title: str,
        date: Optional[datetime],
        sentiment: str,  # "positive", "negative", "neutral"
        sentiment_score: float,  # -1 to 1
        materiality_score: float,  # 0 to 1
        category: str,
        url: str,
        source_id: str,
    ):
        self.title = title
        self.date = date
        self.sentiment = sentiment
        self.sentiment_score = sentiment_score
        self.materiality_score = materiality_score
        self.category = category
        self.url = url
        self.source_id = source_id


def analyze_news_sentiment(text: str, metadata_sentiment: Optional[float] = None) -> tuple[str, float]:
    """
    Analyze sentiment of text using VADER or Event Registry sentiment.
    
    Args:
        text: Text to analyze
        metadata_sentiment: Optional sentiment score from Event Registry metadata
        
    Returns:
        Tuple of (sentiment_label, sentiment_score)
        sentiment_label: "positive", "negative", or "neutral"
        sentiment_score: -1.0 to 1.0
    """
    # Use Event Registry sentiment if available (more accurate)
    if metadata_sentiment is not None:
        sentiment_score = float(metadata_sentiment)
        if sentiment_score >= 0.1:
            return "positive", sentiment_score
        elif sentiment_score <= -0.1:
            return "negative", sentiment_score
        else:
            return "neutral", sentiment_score
    
    # Fallback to VADER if Event Registry sentiment not available
    try:
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
        
        analyzer = SentimentIntensityAnalyzer()
        scores = analyzer.polarity_scores(text)
        compound = scores["compound"]
        
        if compound >= 0.05:
            return "positive", compound
        elif compound <= -0.05:
            return "negative", compound
        else:
            return "neutral", compound
    except ImportError:
        # Fallback if vaderSentiment not available
        return "neutral", 0.0
    except Exception:
        return "neutral", 0.0


def calculate_materiality_score(
    title: str, description: str, category: str, days_ago: int
) -> float:
    """
    Calculate materiality score based on keywords, category, and recency.
    
    Args:
        title: Article title
        description: Article description
        category: Event category
        days_ago: Days since publication
        
    Returns:
        Materiality score (0.0 to 1.0)
    """
    score = 0.0
    
    # Recency weight (more recent = higher score)
    recency_weight = max(0.0, 1.0 - (days_ago / 90.0))  # Decay over 90 days
    score += recency_weight * 0.3
    
    # Category weight
    category_weights = {
        "litigation": 0.9,  # Litigation is highly material
        "m_and_a": 0.8,  # M&A is very material
        "guidance": 0.7,  # Guidance is material
        "macro": 0.5,  # Macro is less material
        "general": 0.3,
    }
    category_weight = category_weights.get(category, 0.3)
    score += category_weight * 0.4
    
    # Keyword weight (litigation keywords are more material)
    text = (title + " " + description).lower()
    high_impact_keywords = [
        "lawsuit", "litigation", "settlement", "fine", "penalty",
        "acquisition", "merger", "takeover", "deal",
        "guidance", "forecast", "outlook", "earnings",
    ]
    keyword_matches = sum(1 for kw in high_impact_keywords if kw in text)
    keyword_weight = min(1.0, keyword_matches * 0.1)
    score += keyword_weight * 0.3
    
    return min(1.0, score)


def analyze_news_articles(news: List[SourceItem]) -> List[MaterialEvent]:
    """
    Analyze news articles for sentiment and materiality.
    
    Args:
        news: List of news source items
        
    Returns:
        List of material events with sentiment and scores
    """
    material_events = []
    now = datetime.now()
    
    for article in news:
        # Get text for sentiment analysis
        title = article.title or ""
        description = article.metadata.get("description", "") if article.metadata else ""
        text = f"{title} {description}"
        
        # Get Event Registry sentiment from metadata if available
        metadata_sentiment = None
        if article.metadata and "sentiment" in article.metadata:
            metadata_sentiment = article.metadata.get("sentiment")
        
        # Analyze sentiment (use Event Registry sentiment if available)
        sentiment_label, sentiment_score = analyze_news_sentiment(text, metadata_sentiment)
        
        # Determine category
        title_lower = title.lower()
        if any(word in title_lower for word in ["deal", "acquisition", "merger", "partnership"]):
            category = "m_and_a"
        elif any(word in title_lower for word in ["lawsuit", "litigation", "regulatory", "sec", "investigation"]):
            category = "litigation"
        elif any(word in title_lower for word in ["guidance", "earnings", "forecast", "outlook"]):
            category = "guidance"
        elif any(word in title_lower for word in ["macro", "recession", "rates", "inflation", "economy"]):
            category = "macro"
        else:
            category = "general"
        
        # Calculate days ago
        days_ago = 0
        if article.date:
            days_ago = (now - article.date.replace(tzinfo=None)).days
        
        # Calculate materiality score
        materiality_score = calculate_materiality_score(
            title, description, category, days_ago
        )
        
        # Only include if materiality score > 0.3
        if materiality_score > 0.3:
            event = MaterialEvent(
                title=title,
                date=article.date,
                sentiment=sentiment_label,
                sentiment_score=sentiment_score,
                materiality_score=materiality_score,
                category=category,
                url=article.url or "",
                source_id=article.source_id,
            )
            material_events.append(event)
    
    # Sort by materiality score (highest first)
    material_events.sort(key=lambda x: x.materiality_score, reverse=True)
    
    return material_events[:5]  # Return top 5 material events

