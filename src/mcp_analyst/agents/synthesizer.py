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
        # TODO: Generate memo using LLM or template
        # For v1, return stub memo
        memo = f"""# Research Memo: {self.run_context.ticker}

## Executive Summary

[Generated executive summary]

## Financial Analysis

[Financial metrics analysis]

## Valuation

[Valuation results and assumptions]

## Risks and Considerations

[Skeptic flags and risks]

## Sources

[Citation list]
"""
        return memo

