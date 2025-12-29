"""Source data schemas."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class Citation(BaseModel):
    """Citation reference."""

    source_id: str
    url: Optional[str] = None
    title: Optional[str] = None
    date: Optional[datetime] = None
    page: Optional[str] = None


class EvidenceSnippet(BaseModel):
    """Evidence snippet from a source."""

    text: str
    citation: Citation
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)


class SourceItem(BaseModel):
    """Source data item (filing, transcript, news, etc.)."""

    source_id: str
    source_type: str  # "filing", "transcript", "news", etc.
    ticker: str
    title: str
    url: Optional[str] = None
    date: Optional[datetime] = None
    content: Optional[str] = None
    metadata: dict = Field(default_factory=dict)

