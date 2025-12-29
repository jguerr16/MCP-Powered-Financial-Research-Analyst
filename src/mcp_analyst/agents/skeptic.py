"""Skeptic validation agent."""

from mcp_analyst.orchestrator.run_context import RunContext
from mcp_analyst.schemas.factpack import FactPack
from mcp_analyst.schemas.skeptic import SkepticReport
from mcp_analyst.schemas.valuation import ValuationOutput


class SkepticAgent:
    """Flags unsupported claims and validates evidence."""

    def __init__(self, run_context: RunContext):
        """Initialize skeptic agent."""
        self.run_context = run_context

    def validate(
        self, factpack: FactPack, valuation_output: ValuationOutput
    ) -> SkepticReport:
        """
        Validate claims against evidence.

        Args:
            factpack: Structured facts
            valuation_output: Valuation results to validate

        Returns:
            Skeptic report with flags
        """
        # TODO: Validate claims and flag issues
        # For v1, return empty SkepticReport
        return SkepticReport(
            flags=[],
            citation_coverage=0.0,
            confidence_score=0.0,
        )

