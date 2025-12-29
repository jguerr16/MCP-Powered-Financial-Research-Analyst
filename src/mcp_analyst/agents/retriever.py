"""Data retrieval agent."""

from mcp_analyst.orchestrator.run_context import RunContext
from mcp_analyst.schemas.factpack import FactPack
from mcp_analyst.tools.edgar import fetch_filings
from mcp_analyst.tools.news import fetch_news
from mcp_analyst.tools.transcripts import fetch_transcripts


class RetrieverAgent:
    """Retrieves and structures source data."""

    def __init__(self, run_context: RunContext):
        """Initialize retriever agent."""
        self.run_context = run_context

    def retrieve(self) -> FactPack:
        """
        Retrieve data from all sources and create FactPack.

        Returns:
            FactPack containing structured facts
        """
        # Fetch from EDGAR
        filings = fetch_filings(self.run_context.ticker)

        # Fetch transcripts (stub in v1)
        transcripts = fetch_transcripts(self.run_context.ticker)

        # Fetch news (stub in v1)
        news = fetch_news(self.run_context.ticker)

        # TODO: Process raw data into FactPack
        # For v1, return empty FactPack structure
        return FactPack(
            ticker=self.run_context.ticker,
            facts=[],
            sources=[],
        )

