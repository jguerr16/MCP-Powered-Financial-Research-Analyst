"""DCF valuation schemas."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class DcfAssumptions(BaseModel):
    """DCF model assumptions with full operating forecast drivers."""

    # Forecast years
    horizon_years: int
    forecast_years: List[str]  # e.g., ["2025", "2026", "2027", "2028", "2029"]
    base_year: str  # e.g., "2024"
    base_year_revenue: float

    # Revenue growth
    revenue_growth_rates: List[float]  # Per year, length = horizon_years

    # Cost structure (% of revenue, per year)
    cogs_ex_da_pct_rev: List[float]  # Cost of goods sold (excluding D&A) as % of revenue
    sga_pct_rev: List[float]  # SG&A as % of revenue
    da_pct_rev: List[float]  # Depreciation & amortization as % of revenue
    sbc_pct_rev: List[float]  # Stock-based compensation as % of revenue

    # Investments (% of revenue, per year)
    capex_pct_rev: List[float]  # Capital expenditures as % of revenue
    nwc_pct_rev: List[float]  # Net working capital as % of revenue (or ΔNWC %)

    # Valuation parameters
    terminal_method: str  # "gordon", "exit_multiple"
    terminal_growth_rate: float
    exit_multiple: Optional[float] = None  # EBITDA multiple if exit_multiple method
    wacc: float  # Weighted average cost of capital
    tax_rate: float = 0.21

    # Capital structure
    shares_out: float  # Shares outstanding
    net_debt: float  # Net debt (debt - cash)

    # WACC components (for WACC tab)
    risk_free_rate: float = 0.04
    equity_risk_premium: float = 0.06
    beta: float = 1.0
    cost_of_debt: float = 0.05
    debt_to_equity_ratio: float = 0.3

    other_assumptions: Dict[str, Any] = {}
    
    # Confidence labels for assumptions
    confidence: Dict[str, str] = {}  # e.g., {"revenue_growth": "HIGH", "cogs_pct": "MED", "wacc": "LOW"}
    
    # Fade schedule metadata
    fade_method: Optional[str] = None  # "linear", "exp", "piecewise"


class OperatingForecast(BaseModel):
    """Operating forecast for a single year."""

    year: str
    revenue: float
    cogs_ex_da: float
    sga: float
    da: float
    ebit: float
    taxes: float
    nopat: float
    da_addback: float
    sbc_addback: float
    delta_nwc: float
    capex: float
    unlevered_fcf: float
    discount_factor: float
    pv_ufcf: float


class DcfResults(BaseModel):
    """DCF calculation results."""

    fair_value_per_share: float
    total_enterprise_value: float
    equity_value: float
    present_values: Dict[str, float]  # PV by year
    terminal_value: float
    pv_terminal_value: float
    operating_forecast: List[OperatingForecast] = []  # Year-by-year forecast
    sensitivity: Dict[str, Any] = {}  # Sensitivity analysis results


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

