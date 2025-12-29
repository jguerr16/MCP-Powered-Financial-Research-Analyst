"""Pricing data schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class QuoteData(BaseModel):
    """Quote data from pricing provider."""

    ticker: str
    price: Optional[float] = None
    market_cap: Optional[float] = None
    beta: Optional[float] = None
    shares_out: Optional[float] = None
    currency: Optional[str] = None
    as_of_utc: str  # ISO timestamp
    source: str = "yahoo_finance"

    def model_dump(self, **kwargs):
        """Dump model to dict (Pydantic v2 compatible)."""
        return super().model_dump(**kwargs)

