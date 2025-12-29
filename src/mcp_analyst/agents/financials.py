"""Financial metrics normalization agent."""

from mcp_analyst.orchestrator.run_context import RunContext
from mcp_analyst.schemas.factpack import FactPack
from mcp_analyst.schemas.financials import FinancialSummary


class FinancialsAgent:
    """Normalizes financial metrics from various sources."""

    def __init__(self, run_context: RunContext):
        """Initialize financials agent."""
        self.run_context = run_context

    def analyze(self, factpack: FactPack) -> FinancialSummary:
        """
        Analyze and normalize financial metrics.

        Args:
            factpack: Structured facts from retrieval

        Returns:
            Normalized financial summary
        """
        # TODO: Extract and normalize financial metrics
        # For v1, return empty FinancialSummary structure
        return FinancialSummary(
            ticker=self.run_context.ticker,
            metrics=[],
            periods=[],
        )

