"""FactPack schema for structured facts."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from mcp_analyst.schemas.sources import EvidenceSnippet, SourceItem


class FactItem(BaseModel):
    """Individual fact item."""

    fact_id: str
    category: str  # "financial", "operational", "strategic", etc.
    claim: str
    evidence: List[EvidenceSnippet]
    confidence: float = 0.5


class MaterialEvent(BaseModel):
    """Material event from news with sentiment."""

    title: str
    date: Optional[datetime] = None
    sentiment: str  # "positive", "negative", "neutral"
    sentiment_score: float  # -1 to 1
    materiality_score: float  # 0 to 1
    category: str
    url: str
    source_id: str


class FactPack(BaseModel):
    """Structured facts from all sources."""

    ticker: str
    facts: List[FactItem] = []
    sources: List[SourceItem] = []
    material_events: List[MaterialEvent] = []  # Top material events with sentiment

