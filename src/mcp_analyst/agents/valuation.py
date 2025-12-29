"""DCF valuation agent."""

from mcp_analyst.orchestrator.run_context import RunContext
from mcp_analyst.schemas.factpack import FactPack
from mcp_analyst.schemas.financials import FinancialSummary
from mcp_analyst.schemas.valuation import DcfAssumptions, DcfResults, ValuationOutput


class ValuationAgent:
    """Produces DCF assumptions and valuation results."""

    def __init__(self, run_context: RunContext):
        """Initialize valuation agent."""
        self.run_context = run_context

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
        # TODO: Generate DCF assumptions based on inputs
        # For v1, return stub assumptions
        assumptions = DcfAssumptions(
            horizon_years=int(self.run_context.horizon.rstrip("y")),
            terminal_method=self.run_context.terminal,
            wacc=0.10,
            terminal_growth_rate=0.03,
            revenue_growth_rates=[],
            margin_assumptions={},
        )

        # TODO: Calculate DCF results
        results = DcfResults(
            fair_value_per_share=0.0,
            total_enterprise_value=0.0,
            equity_value=0.0,
            present_values={},
        )

        return ValuationOutput(
            assumptions=assumptions,
            results=results,
            sensitivity={},
        )

