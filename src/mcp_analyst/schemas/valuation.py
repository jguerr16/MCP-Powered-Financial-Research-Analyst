"""DCF valuation schemas."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class DcfAssumptions(BaseModel):
    """DCF model assumptions."""

    horizon_years: int
    terminal_method: str  # "gordon", "perpetuity"
    wacc: float  # Weighted average cost of capital
    terminal_growth_rate: float
    revenue_growth_rates: List[float]  # Per year
    margin_assumptions: Dict[str, float]  # e.g., {"operating_margin": 0.15}
    other_assumptions: Dict[str, Any] = {}


class DcfResults(BaseModel):
    """DCF calculation results."""

    fair_value_per_share: float
    total_enterprise_value: float
    equity_value: float
    present_values: Dict[str, float]  # PV by year
    sensitivity: Dict[str, float] = {}  # Sensitivity analysis results


class SensitivitySpec(BaseModel):
    """Sensitivity analysis specification."""

    variable: str
    base_value: float
    range_min: float
    range_max: float
    steps: int = 10


class ValuationOutput(BaseModel):
    """Complete valuation output."""

    assumptions: DcfAssumptions
    results: DcfResults
    sensitivity: Dict[str, Any] = {}

