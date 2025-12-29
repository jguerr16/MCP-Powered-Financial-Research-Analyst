"""FactPack schema for structured facts."""

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


class FactPack(BaseModel):
    """Structured facts from all sources."""

    ticker: str
    facts: List[FactItem] = []
    sources: List[SourceItem] = []

