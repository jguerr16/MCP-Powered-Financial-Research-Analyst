"""Skeptic validation schemas."""

from typing import List, Optional

from pydantic import BaseModel


class SkepticFlag(BaseModel):
    """Individual skeptic flag."""

    flag_type: str  # "unsupported_claim", "conflicting_evidence", "outdated_data", etc.
    severity: str  # "low", "medium", "high"
    description: str
    claim_id: Optional[str] = None
    evidence_ids: List[str] = []


class SkepticReport(BaseModel):
    """Skeptic validation report."""

    flags: List[SkepticFlag] = []
    citation_coverage: float = 0.0  # Percentage of claims with citations
    confidence_score: float = 0.0  # Overall confidence (0-1)

