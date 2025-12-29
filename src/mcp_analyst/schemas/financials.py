"""Financial metrics schemas."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class MetricSeries(BaseModel):
    """Time series of a financial metric."""

    metric_name: str
    values: List[float]
    periods: List[str]  # e.g., ["2023-Q1", "2023-Q2", ...]
    unit: str = "USD"  # "USD", "percentage", "ratio", etc.


class FinancialSummary(BaseModel):
    """Normalized financial summary with annual, quarterly, and TTM series."""

    ticker: str
    metrics: List[MetricSeries] = []
    periods: List[str] = []  # All periods (annual + quarterly)
    annual_periods: List[str] = []  # FY periods only
    quarterly_periods: List[str] = []  # Quarterly periods only
    ttm_period: Optional[str] = None  # TTM period identifier
    metadata: Dict[str, Any] = {}

