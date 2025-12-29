"""DCF valuation agent."""

import math
from typing import Optional

from mcp_analyst.orchestrator.run_context import RunContext
from mcp_analyst.schemas.factpack import FactPack
from mcp_analyst.schemas.financials import FinancialSummary, MetricSeries
from mcp_analyst.schemas.valuation import (
    DcfAssumptions,
    DcfResults,
    OperatingForecast,
    ValuationOutput,
)
from mcp_analyst.valuation.fade import get_fade_schedule


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

    def _get_metric_by_period_type(
        self, financial_summary: FinancialSummary, metric_name: str, period_type: str
    ) -> Optional[MetricSeries]:
        """Get metric series filtered by period type (annual/quarterly)."""
        for metric in financial_summary.metrics:
            if metric.metric_name.lower() == metric_name.lower():
                # Filter periods
                filtered_values = []
                filtered_periods = []
                for period, value in zip(metric.periods, metric.values):
                    is_quarterly = "-Q" in period
                    if period_type == "quarterly" and is_quarterly:
                        filtered_periods.append(period)
                        filtered_values.append(value)
                    elif period_type == "annual" and not is_quarterly:
                        filtered_periods.append(period)
                        filtered_values.append(value)

                if filtered_values:
                    return MetricSeries(
                        metric_name=metric.metric_name,
                        values=filtered_values,
                        periods=filtered_periods,
                        unit=metric.unit,
                    )
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
        return 0.025  # 2.5% default

    def _estimate_cost_structure(
        self, financial_summary: FinancialSummary, revenue_values: list
    ) -> tuple:
        """Estimate cost structure from historical data."""
        # Estimate COGS (excluding D&A) - typically 60-70% of revenue for most companies
        # We'll use gross margin if available, otherwise estimate
        cogs_pct = 0.65  # Default 65% COGS

        # Estimate SG&A - typically 15-25% of revenue
        sga_pct = 0.20  # Default 20% SG&A

        # Estimate D&A - typically 2-5% of revenue
        da_pct = 0.03  # Default 3% D&A

        # Estimate SBC - typically 1-3% of revenue for tech companies
        sbc_pct = 0.02  # Default 2% SBC

        # Get operating income to refine estimates
        operating_income_values = self._get_metric(financial_summary, "Operating Income")
        if operating_income_values and len(operating_income_values) >= 3:
            # Calculate implied COGS + SG&A from operating margin
            operating_margins = [
                oi / rev if rev > 0 else 0.0
                for oi, rev in zip(operating_income_values[:3], revenue_values[:3])
            ]
            avg_op_margin = sum(operating_margins) / len(operating_margins)
            # If operating margin is known, adjust COGS + SG&A
            implied_cogs_sga = 1.0 - avg_op_margin - da_pct
            if implied_cogs_sga > 0:
                # Split between COGS and SG&A (60/40 typical)
                cogs_pct = implied_cogs_sga * 0.6
                sga_pct = implied_cogs_sga * 0.4

        return cogs_pct, sga_pct, da_pct, sbc_pct

    def valuate(
        self, financial_summary: FinancialSummary, factpack: FactPack
    ) -> ValuationOutput:
        """
        Generate DCF valuation with full operating forecast.

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

        # Use TTM if available, else use latest annual
        base_revenue = None
        base_year = None
        base_year_int = None
        confidence = "medium"

        if financial_summary.ttm_period:
            # Calculate TTM from quarterly data
            revenue_quarterly = self._get_metric_by_period_type(financial_summary, "Revenue", "quarterly")
            if revenue_quarterly and len(revenue_quarterly.values) >= 4:
                base_revenue = sum(revenue_quarterly.values[:4])
                base_year = financial_summary.ttm_period
                base_year_int = int(financial_summary.quarterly_periods[0][:4]) if financial_summary.quarterly_periods else 2024
                confidence = "high"  # TTM is high confidence

        if not base_revenue:
            # Fall back to latest annual
            revenue_annual = self._get_metric_by_period_type(financial_summary, "Revenue", "annual")
            if revenue_annual and len(revenue_annual.values) > 0:
                base_revenue = revenue_annual.values[0]
                base_year = financial_summary.annual_periods[0] if financial_summary.annual_periods else "2024"
                base_year_int = int(base_year)
                confidence = "high"  # Direct from filings
            else:
                # Last resort: use first value from all periods
                base_revenue = revenue_values[0]
                base_year = financial_summary.periods[0] if financial_summary.periods else "2024"
                base_year_int = int(base_year)
                confidence = "medium"

        if base_revenue <= 0:
            raise ValueError(f"Base revenue invalid: {base_revenue}")

        # Calculate growth rates
        horizon_years = int(self.run_context.horizon.rstrip("y"))
        
        # Use 3Y CAGR if available, else 2Y, else 5% default
        if len(revenue_values) >= 4:
            growth_rate = self._calculate_cagr(revenue_values, 3)
        elif len(revenue_values) >= 3:
            growth_rate = self._calculate_cagr(revenue_values, 2)
        else:
            growth_rate = 0.05  # 5% default

        # Apply sophisticated fade schedule based on risk profile
        terminal_growth = self._get_terminal_growth()
        
        # Choose fade method based on risk profile
        if self.run_context.risk == "aggressive":
            # Aggressive: exponential fade (higher early growth, slower fade)
            fade_method = "exp"
            fade_kwargs = {"k": 0.3}  # Slower exponential fade
        elif self.run_context.risk == "conservative":
            # Conservative: linear fast fade
            fade_method = "linear"
            fade_kwargs = {}
        else:  # moderate
            # Moderate: piecewise fade (fast fade years 1-2, slower thereafter)
            fade_method = "piecewise"
            mid_growth = growth_rate * 0.6  # 60% of initial after 2 years
            fade_kwargs = {"mid": mid_growth, "split": 2}
        
        # Generate fade schedule
        revenue_growth_rates = get_fade_schedule(
            fade_method,
            growth_rate,
            terminal_growth,
            horizon_years,
            **fade_kwargs
        )
        
        # Ensure no growth rate goes below terminal
        revenue_growth_rates = [max(rate, terminal_growth) for rate in revenue_growth_rates]

        # Estimate cost structure
        cogs_pct, sga_pct, da_pct, sbc_pct = self._estimate_cost_structure(
            financial_summary, revenue_values
        )

        # Get capex for capex % revenue
        capex_values = self._get_metric(financial_summary, "Capital Expenditures")
        if capex_values and len(capex_values) >= 3:
            capex_pct_rev = self._calculate_trailing_average(
                [c / r if r > 0 else 0.0 for c, r in zip(capex_values[:3], revenue_values[:3])],
                3
            )
        else:
            capex_pct_rev = 0.05  # 5% default

        # NWC typically 10-15% of revenue
        nwc_pct_rev = 0.10  # 10% default

        # Get shares outstanding
        shares_values = self._get_metric(financial_summary, "Shares Outstanding")
        if shares_values and len(shares_values) > 0:
            shares_out = shares_values[0]
            if shares_out < 1000:
                shares_out = shares_out * 1_000_000
            elif shares_out < 1_000_000:
                shares_out = shares_out * 1_000
        else:
            shares_out = 1_000_000_000  # 1B shares default

        # Get net debt
        debt_values = self._get_metric(financial_summary, "Total Debt")
        cash_values = self._get_metric(financial_summary, "Cash")
        
        net_debt = 0.0
        if debt_values and len(debt_values) > 0:
            net_debt += debt_values[0]
        if cash_values and len(cash_values) > 0:
            net_debt -= cash_values[0]
        net_debt = max(0.0, net_debt)

        # Generate forecast years
        forecast_years = [str(base_year_int + i) for i in range(1, horizon_years + 1)]

        # Build confidence labels based on data provenance
        confidence_map = {}
        
        # Base revenue: HIGH if from TTM/annual, MED if fallback
        if financial_summary.ttm_period:
            confidence_map["base_revenue"] = "HIGH"
        elif financial_summary.annual_periods:
            confidence_map["base_revenue"] = "HIGH"
        else:
            confidence_map["base_revenue"] = "MED"
        
        # Revenue growth: HIGH if 3Y+ CAGR, MED if 2Y, LOW if default
        if len(revenue_values) >= 4:
            confidence_map["revenue_growth"] = "HIGH"
        elif len(revenue_values) >= 3:
            confidence_map["revenue_growth"] = "MED"
        else:
            confidence_map["revenue_growth"] = "LOW"
        
        # Cost structure: Check if we have operating income data
        operating_income = self._get_metric(financial_summary, "Operating Income")
        if operating_income and len(operating_income) >= 3:
            confidence_map["cogs_pct"] = "MED"  # Computed from historical
            confidence_map["sga_pct"] = "MED"
        else:
            confidence_map["cogs_pct"] = "LOW"  # Fallback heuristic
            confidence_map["sga_pct"] = "LOW"
        
        # D&A and SBC: typically LOW (hard to extract from filings)
        confidence_map["da_pct"] = "LOW"
        confidence_map["sbc_pct"] = "LOW"
        
        # Capex: HIGH if from filings, LOW if default
        if capex_values and len(capex_values) >= 3:
            confidence_map["capex_pct"] = "HIGH"
        else:
            confidence_map["capex_pct"] = "LOW"
        
        # NWC: typically LOW (estimated)
        confidence_map["nwc_pct"] = "LOW"
        
        # Shares: HIGH if from filings, LOW if default
        if shares_values and len(shares_values) > 0:
            confidence_map["shares_out"] = "HIGH"
        else:
            confidence_map["shares_out"] = "LOW"
        
        # Net debt: HIGH if both debt and cash from filings, MED if one, LOW if default
        if debt_values and cash_values and len(debt_values) > 0 and len(cash_values) > 0:
            confidence_map["net_debt"] = "HIGH"
        elif (debt_values and len(debt_values) > 0) or (cash_values and len(cash_values) > 0):
            confidence_map["net_debt"] = "MED"
        else:
            confidence_map["net_debt"] = "LOW"
        
        # WACC components: typically LOW (estimated/defaults)
        confidence_map["wacc"] = "LOW"
        confidence_map["risk_free_rate"] = "LOW"
        confidence_map["equity_risk_premium"] = "LOW"
        confidence_map["beta"] = "LOW"
        confidence_map["cost_of_debt"] = "LOW"
        confidence_map["debt_to_equity_ratio"] = "LOW"
        confidence_map["tax_rate"] = "LOW"
        confidence_map["terminal_growth"] = "LOW"
        
        # Build assumptions with per-year vectors
        wacc = self._get_wacc()
        assumptions = DcfAssumptions(
            horizon_years=horizon_years,
            forecast_years=forecast_years,
            base_year=base_year,
            base_year_revenue=base_revenue,
            revenue_growth_rates=revenue_growth_rates,
            cogs_ex_da_pct_rev=[cogs_pct] * horizon_years,
            sga_pct_rev=[sga_pct] * horizon_years,
            da_pct_rev=[da_pct] * horizon_years,
            sbc_pct_rev=[sbc_pct] * horizon_years,
            capex_pct_rev=[capex_pct_rev] * horizon_years,
            nwc_pct_rev=[nwc_pct_rev] * horizon_years,
            terminal_method=self.run_context.terminal,
            terminal_growth_rate=self._get_terminal_growth(),
            wacc=wacc,
            tax_rate=0.21,
            shares_out=shares_out,
            net_debt=net_debt,
            risk_free_rate=0.04,
            equity_risk_premium=0.06,
            beta=1.0,
            cost_of_debt=0.05,
            debt_to_equity_ratio=0.3,
            confidence=confidence_map,
            fade_method=fade_method,
        )

        # Build full operating forecast
        operating_forecast = []
        present_values = {}
        cumulative_pv = 0.0
        projected_revenue = base_revenue
        prev_nwc = base_revenue * nwc_pct_rev  # Starting NWC

        for year_idx, year in enumerate(forecast_years):
            # Project revenue
            growth_rate = revenue_growth_rates[year_idx]
            projected_revenue = projected_revenue * (1 + growth_rate)

            # Operating build
            cogs_ex_da = projected_revenue * cogs_pct
            sga = projected_revenue * sga_pct
            da = projected_revenue * da_pct
            ebit = projected_revenue - cogs_ex_da - sga - da
            taxes = ebit * assumptions.tax_rate
            nopat = ebit - taxes

            # Add-backs
            da_addback = da
            sbc_addback = projected_revenue * sbc_pct

            # Investments
            capex = projected_revenue * capex_pct_rev
            current_nwc = projected_revenue * nwc_pct_rev
            delta_nwc = current_nwc - prev_nwc
            prev_nwc = current_nwc

            # Unlevered FCF
            unlevered_fcf = nopat + da_addback + sbc_addback - delta_nwc - capex

            # Discount to present
            discount_factor = 1.0 / ((1 + wacc) ** (year_idx + 1))
            pv_ufcf = unlevered_fcf * discount_factor
            present_values[f"Year {year_idx + 1}"] = pv_ufcf
            cumulative_pv += pv_ufcf

            operating_forecast.append(
                OperatingForecast(
                    year=year,
                    revenue=projected_revenue,
                    cogs_ex_da=cogs_ex_da,
                    sga=sga,
                    da=da,
                    ebit=ebit,
                    taxes=taxes,
                    nopat=nopat,
                    da_addback=da_addback,
                    sbc_addback=sbc_addback,
                    delta_nwc=delta_nwc,
                    capex=capex,
                    unlevered_fcf=unlevered_fcf,
                    discount_factor=discount_factor,
                    pv_ufcf=pv_ufcf,
                )
            )

        # Terminal value (using final year UFCF)
        final_ufcf = operating_forecast[-1].unlevered_fcf
        terminal_ufcf = final_ufcf * (1 + assumptions.terminal_growth_rate)
        terminal_value = terminal_ufcf / (wacc - assumptions.terminal_growth_rate)
        pv_terminal = terminal_value / ((1 + wacc) ** horizon_years)
        present_values["Terminal Value"] = pv_terminal

        # Total enterprise value
        total_enterprise_value = cumulative_pv + pv_terminal

        # Equity value
        equity_value = total_enterprise_value - net_debt

        # Fair value per share
        fair_value_per_share = equity_value / shares_out if shares_out > 0 else 0.0

        # Build sensitivity table (WACC vs terminal growth)
        sensitivity = self._build_sensitivity_table(
            operating_forecast, horizon_years, wacc, assumptions.terminal_growth_rate, shares_out, net_debt
        )

        results = DcfResults(
            fair_value_per_share=fair_value_per_share,
            total_enterprise_value=total_enterprise_value,
            equity_value=equity_value,
            present_values=present_values,
            terminal_value=terminal_value,
            pv_terminal_value=pv_terminal,
            operating_forecast=operating_forecast,
            sensitivity=sensitivity,
        )

        return ValuationOutput(
            assumptions=assumptions,
            results=results,
            sensitivity=sensitivity,
        )

    def _build_sensitivity_table(
        self, operating_forecast: list, horizon_years: int, base_wacc: float,
        base_terminal_growth: float, shares_out: float, net_debt: float
    ) -> dict:
        """Build 2D sensitivity table (WACC vs terminal growth)."""
        wacc_range = [base_wacc - 0.02, base_wacc - 0.01, base_wacc, base_wacc + 0.01, base_wacc + 0.02]
        growth_range = [
            base_terminal_growth - 0.01, base_terminal_growth - 0.005,
            base_terminal_growth, base_terminal_growth + 0.005, base_terminal_growth + 0.01
        ]

        final_ufcf = operating_forecast[-1].unlevered_fcf
        sensitivity_table = {}

        for wacc in wacc_range:
            row = {}
            cumulative_pv = sum(f.pv_ufcf for f in operating_forecast)
            for growth in growth_range:
                terminal_ufcf = final_ufcf * (1 + growth)
                terminal_value = terminal_ufcf / (wacc - growth) if wacc > growth else 0
                pv_terminal = terminal_value / ((1 + wacc) ** horizon_years)
                total_ev = cumulative_pv + pv_terminal
                equity_value = total_ev - net_debt
                price_per_share = equity_value / shares_out if shares_out > 0 else 0.0
                row[f"{growth:.3f}"] = price_per_share
            sensitivity_table[f"{wacc:.3f}"] = row

        return sensitivity_table
