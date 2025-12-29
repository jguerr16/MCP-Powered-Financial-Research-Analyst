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
    """Normalized financial summary."""

    ticker: str
    metrics: List[MetricSeries] = []
    periods: List[str] = []
    metadata: Dict[str, Any] = {}

