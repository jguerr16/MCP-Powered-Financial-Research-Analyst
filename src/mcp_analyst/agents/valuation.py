"""DCF valuation agent."""

import math
from typing import Optional

from mcp_analyst.orchestrator.run_context import RunContext
from mcp_analyst.schemas.factpack import FactPack
from mcp_analyst.schemas.financials import FinancialSummary
from mcp_analyst.schemas.valuation import DcfAssumptions, DcfResults, ValuationOutput


class ValuationAgent:
    """Produces DCF assumptions and valuation results."""

    def __init__(self, run_context: RunContext):
        """Initialize valuation agent."""
        self.run_context = run_context

    def _get_metric(self, financial_summary: FinancialSummary, metric_name: str) -> Optional[list]:
        """Get metric values by name."""
        for metric in financial_summary.metrics:
            if metric.metric_name.lower() == metric_name.lower():
                return metric.values
        return None

    def _calculate_cagr(self, values: list, years: int) -> float:
        """Calculate CAGR over N years."""
        if len(values) < years + 1 or values[-1] <= 0:
            return 0.0
        return (values[0] / values[years]) ** (1.0 / years) - 1.0

    def _calculate_trailing_average(self, values: list, periods: int) -> float:
        """Calculate trailing average."""
        if not values or len(values) < periods:
            return 0.0
        return sum(values[:periods]) / periods

    def _get_wacc(self) -> float:
        """Get WACC based on risk profile."""
        risk_wacc_map = {
            "conservative": 0.08,
            "moderate": 0.10,
            "aggressive": 0.12,
        }
        return risk_wacc_map.get(self.run_context.risk, 0.10)

    def _get_terminal_growth(self) -> float:
        """Get terminal growth rate."""
        return 0.025  # 2.5% default, can be adjusted by risk

    def valuate(
        self, financial_summary: FinancialSummary, factpack: FactPack
    ) -> ValuationOutput:
        """
        Generate DCF valuation.

        Args:
            financial_summary: Normalized financial metrics
            factpack: Structured facts

        Returns:
            Valuation output with assumptions and results
        """
        # Get revenue series
        revenue_values = self._get_metric(financial_summary, "Revenue")
        if not revenue_values or len(revenue_values) == 0:
            raise ValueError("Revenue data missing")

        # Base revenue (most recent)
        base_revenue = revenue_values[0]
        if base_revenue <= 0:
            raise ValueError(f"Base revenue invalid: {base_revenue}")

        # Base year (most recent period)
        base_year = financial_summary.periods[0] if financial_summary.periods else "2024"

        # Calculate growth rates
        horizon_years = int(self.run_context.horizon.rstrip("y"))
        
        # Use 3Y CAGR if available, else 2Y, else 5% default
        if len(revenue_values) >= 4:
            growth_rate = self._calculate_cagr(revenue_values, 3)
        elif len(revenue_values) >= 3:
            growth_rate = self._calculate_cagr(revenue_values, 2)
        else:
            growth_rate = 0.05  # 5% default

        # Apply fade schedule (growth declines over time)
        revenue_growth_rates = []
        for year in range(horizon_years):
            # Fade from initial growth to terminal growth
            fade_factor = 1.0 - (year / (horizon_years - 1)) if horizon_years > 1 else 1.0
            year_growth = growth_rate * (1.0 - fade_factor * 0.5)  # Fade to 50% of initial
            revenue_growth_rates.append(max(year_growth, self._get_terminal_growth()))

        # Get operating income for margin calculation
        operating_income_values = self._get_metric(financial_summary, "Operating Income")
        if operating_income_values and len(operating_income_values) >= 3:
            # Calculate trailing average operating margin
            operating_margins = [
                oi / rev if rev > 0 else 0.0
                for oi, rev in zip(operating_income_values[:3], revenue_values[:3])
            ]
            avg_operating_margin = sum(operating_margins) / len(operating_margins)
        else:
            # Fallback: assume 15% margin
            avg_operating_margin = 0.15

        # Get capex for capex % revenue
        capex_values = self._get_metric(financial_summary, "Capital Expenditures")
        if capex_values and len(capex_values) >= 3:
            capex_pct_rev = self._calculate_trailing_average(
                [c / r if r > 0 else 0.0 for c, r in zip(capex_values[:3], revenue_values[:3])],
                3
            )
        else:
            capex_pct_rev = 0.05  # 5% default

        # Get shares outstanding
        shares_values = self._get_metric(financial_summary, "Shares Outstanding")
        if shares_values and len(shares_values) > 0:
            shares_out = shares_values[0]
            # Check if already in millions or needs conversion
            # SEC typically reports in thousands, but some tags are in actual shares
            if shares_out < 1000:  # Likely in millions
                shares_out = shares_out * 1_000_000
            elif shares_out < 1_000_000:  # Likely in thousands
                shares_out = shares_out * 1_000
            # Otherwise assume already in actual shares
        else:
            # Fallback: estimate from market cap if available, or use default
            # For v1.1, we'll use a reasonable default based on typical company size
            self.run_context.logger.warning("Shares outstanding not found, using estimated value")
            shares_out = 1_000_000_000  # 1B shares default (will be flagged in validation)

        # Get net debt
        debt_values = self._get_metric(financial_summary, "Total Debt")
        cash_values = self._get_metric(financial_summary, "Cash")
        
        net_debt = 0.0
        if debt_values and len(debt_values) > 0:
            net_debt += debt_values[0]
        if cash_values and len(cash_values) > 0:
            net_debt -= cash_values[0]
        net_debt = max(0.0, net_debt)  # Can't be negative for simplicity

        # Build assumptions
        assumptions = DcfAssumptions(
            horizon_years=horizon_years,
            terminal_method=self.run_context.terminal,
            wacc=self._get_wacc(),
            terminal_growth_rate=self._get_terminal_growth(),
            revenue_growth_rates=revenue_growth_rates,
            margin_assumptions={"operating_margin": avg_operating_margin},
            base_year=base_year,
            base_revenue=base_revenue,
            shares_out=shares_out,
            net_debt=net_debt,
            tax_rate=0.21,
            capex_pct_rev=capex_pct_rev,
        )

        # Calculate DCF (simplified)
        # Free Cash Flow = (Revenue * Operating Margin * (1 - Tax Rate)) - (Revenue * Capex %)
        # Terminal Value = FCF_terminal * (1 + g) / (WACC - g)
        # PV = sum of discounted FCFs + PV of terminal value
        
        present_values = {}
        cumulative_pv = 0.0
        projected_revenue = base_revenue
        
        for year in range(1, horizon_years + 1):
            # Project revenue (compound growth)
            growth_rate = revenue_growth_rates[year - 1]
            projected_revenue = projected_revenue * (1 + growth_rate)
            
            # Calculate FCF
            ebit = projected_revenue * avg_operating_margin
            nopat = ebit * (1 - assumptions.tax_rate)
            capex = projected_revenue * capex_pct_rev
            fcf = nopat - capex
            
            # Discount to present
            pv = fcf / ((1 + assumptions.wacc) ** year)
            present_values[f"Year {year}"] = pv
            cumulative_pv += pv

        # Terminal value (using final year FCF)
        terminal_fcf = fcf * (1 + assumptions.terminal_growth_rate)
        terminal_value = terminal_fcf / (assumptions.wacc - assumptions.terminal_growth_rate)
        pv_terminal = terminal_value / ((1 + assumptions.wacc) ** horizon_years)
        present_values["Terminal Value"] = pv_terminal

        # Total enterprise value
        total_enterprise_value = cumulative_pv + pv_terminal

        # Equity value
        equity_value = total_enterprise_value - net_debt

        # Fair value per share
        fair_value_per_share = equity_value / shares_out if shares_out > 0 else 0.0

        results = DcfResults(
            fair_value_per_share=fair_value_per_share,
            total_enterprise_value=total_enterprise_value,
            equity_value=equity_value,
            present_values=present_values,
        )

        return ValuationOutput(
            assumptions=assumptions,
            results=results,
            sensitivity={},
        )

