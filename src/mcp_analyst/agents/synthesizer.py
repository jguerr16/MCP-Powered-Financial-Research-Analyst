"""Memo synthesis agent."""

from mcp_analyst.orchestrator.run_context import RunContext
from mcp_analyst.schemas.factpack import FactPack
from mcp_analyst.schemas.financials import FinancialSummary
from mcp_analyst.schemas.skeptic import SkepticReport
from mcp_analyst.schemas.valuation import ValuationOutput


class SynthesizerAgent:
    """Generates research memo and executive summary."""

    def __init__(self, run_context: RunContext):
        """Initialize synthesizer agent."""
        self.run_context = run_context

    def synthesize(
        self,
        factpack: FactPack,
        financial_summary: FinancialSummary,
        valuation_output: ValuationOutput,
        skeptic_report: SkepticReport,
    ) -> str:
        """
        Synthesize research memo from all inputs.

        Args:
            factpack: Structured facts
            financial_summary: Normalized financial metrics
            valuation_output: DCF valuation results
            skeptic_report: Validation flags

        Returns:
            Markdown memo content
        """
        assumptions = valuation_output.assumptions
        results = valuation_output.results

        # Get revenue metric
        revenue_metric = next(
            (m for m in financial_summary.metrics if m.metric_name == "Revenue"),
            None,
        )
        operating_income_metric = next(
            (m for m in financial_summary.metrics if m.metric_name == "Operating Income"),
            None,
        )

        # Calculate growth metrics
        growth_text = ""
        if revenue_metric and len(revenue_metric.values) >= 3:
            latest = revenue_metric.values[0]
            three_years_ago = revenue_metric.values[2] if len(revenue_metric.values) > 2 else revenue_metric.values[-1]
            if three_years_ago > 0:
                cagr = ((latest / three_years_ago) ** (1.0 / 3.0)) - 1.0
                growth_text = f"Revenue has grown at a {cagr:.1%} CAGR over the past 3 years."

        # Build memo
        memo = f"""# Research Memo: {self.run_context.ticker}

**Date**: {self.run_context.created_at.strftime("%Y-%m-%d")}  
**Analyst**: MCP-Powered Financial Research Analyst  
**Sector**: {self.run_context.sector or "Not specified"}  
**Risk Profile**: {self.run_context.risk.title()}

## Executive Summary

This memo presents a DCF valuation analysis of {self.run_context.ticker}. Based on our analysis using SEC XBRL data, we estimate a **fair value per share of ${results.fair_value_per_share:.2f}**.

### Key Findings

- **Base Revenue**: ${assumptions.base_year_revenue:,.0f} (FY{assumptions.base_year})
- **Fair Value per Share**: ${results.fair_value_per_share:.2f}
- **Total Enterprise Value**: ${results.total_enterprise_value:,.0f}
- **Equity Value**: ${results.equity_value:,.0f}
- **Shares Outstanding**: {assumptions.shares_out:,.0f}

## Financial Analysis

### Historical Performance

{growth_text}

**Historical Revenue Trends:**
"""
        if revenue_metric:
            for period, value in zip(revenue_metric.periods[:5], revenue_metric.values[:5]):
                memo += f"- {period}: ${value:,.0f}\n"

        if operating_income_metric and revenue_metric:
            memo += "\n**Operating Margins:**\n"
            for i, period in enumerate(operating_income_metric.periods[:5]):
                if i < len(revenue_metric.values) and i < len(operating_income_metric.values):
                    revenue = revenue_metric.values[i]
                    op_inc = operating_income_metric.values[i]
                    if revenue > 0:
                        margin = op_inc / revenue
                        memo += f"- {period}: {margin:.1%}\n"

        memo += f"""
### Data Sources

Financial data extracted from SEC XBRL companyfacts API:
- **Source**: SEC EDGAR Database
- **Data Points**: {len(financial_summary.metrics)} metrics across {len(financial_summary.periods)} periods
- **Latest Period**: {financial_summary.periods[0] if financial_summary.periods else "N/A"}

## Valuation

### DCF Assumptions

- **Forecast Horizon**: {assumptions.horizon_years} years
- **Terminal Method**: {assumptions.terminal_method.title()} Growth Model
- **WACC**: {assumptions.wacc:.1%}
- **Terminal Growth Rate**: {assumptions.terminal_growth_rate:.1%}
- **Tax Rate**: {assumptions.tax_rate:.1%}
- **Capex % Revenue**: {(assumptions.capex_pct_rev[0] if assumptions.capex_pct_rev else 0.0):.1%}

### Revenue Growth Assumptions

| Year | Growth Rate |
|------|-------------|
"""
        for i, rate in enumerate(assumptions.revenue_growth_rates, 1):
            memo += f"| Year {i} | {rate:.1%} |\n"

        memo += f"""
### Cost Structure Assumptions

"""
        if assumptions.cogs_ex_da_pct_rev:
            memo += f"- **COGS ex D&A % Revenue**: {assumptions.cogs_ex_da_pct_rev[0]:.1%}\n"
        if assumptions.sga_pct_rev:
            memo += f"- **SG&A % Revenue**: {assumptions.sga_pct_rev[0]:.1%}\n"
        if assumptions.da_pct_rev:
            memo += f"- **D&A % Revenue**: {assumptions.da_pct_rev[0]:.1%}\n"
        if assumptions.sbc_pct_rev:
            memo += f"- **SBC % Revenue**: {assumptions.sbc_pct_rev[0]:.1%}\n"

        memo += f"""
### Valuation Results

- **Fair Value per Share**: ${results.fair_value_per_share:.2f}
- **Total Enterprise Value**: ${results.total_enterprise_value:,.0f}
- **Equity Value**: ${results.equity_value:,.0f}
- **Net Debt**: ${assumptions.net_debt:,.0f}

### Present Value Breakdown

"""
        for key, value in results.present_values.items():
            memo += f"- **{key}**: ${value:,.0f}\n"

        memo += f"""
## Risks and Considerations

### Data Quality

- **Citation Coverage**: {skeptic_report.citation_coverage:.1%}
- **Confidence Score**: {skeptic_report.confidence_score:.1%}
- **Skeptic Flags**: {len(skeptic_report.flags)}

"""
        if skeptic_report.flags:
            memo += "**Flagged Issues:**\n"
            for flag in skeptic_report.flags[:5]:  # Show top 5
                memo += f"- [{flag.severity.upper()}] {flag.description}\n"
        else:
            memo += "No major data quality issues identified.\n"

        memo += f"""
### Key Risks

- **Model Assumptions**: DCF valuation is sensitive to growth rates and WACC assumptions
- **Data Freshness**: Historical data may not reflect recent changes
- **Market Conditions**: Valuation does not account for market sentiment or short-term volatility

## Sources

"""
        for i, source in enumerate(factpack.sources[:10], 1):  # Top 10 sources
            memo += f"{i}. {source.title}\n"
            if source.url:
                memo += f"   - URL: {source.url}\n"
            if hasattr(source, "date") and source.date:
                memo += f"   - Date: {source.date}\n"

        memo += f"""
---

*This memo was generated by MCP-Powered Financial Research Analyst v0.1.0*  
*Run ID: {self.run_context.run_id[:8]}*
"""
        return memo

