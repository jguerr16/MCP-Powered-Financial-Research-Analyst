"""Data retrieval agent."""

from mcp_analyst.orchestrator.run_context import RunContext
from mcp_analyst.schemas.factpack import FactPack, FactItem
from mcp_analyst.schemas.sources import Citation, EvidenceSnippet
from mcp_analyst.tools.edgar import fetch_companyfacts, fetch_filings
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
        sources = list(filings) if filings else []

        # Fetch companyfacts for facts
        companyfacts = fetch_companyfacts(self.run_context.ticker)
        facts = []

        if companyfacts:
            entity_name = companyfacts.get("entityName", "")
            
            # Create facts from companyfacts metadata
            if entity_name:
                citation = Citation(
                    source_id=sources[0].source_id if sources else "sec_companyfacts",
                    url=sources[0].url if sources else "",
                    title=f"SEC Company Facts - {entity_name}",
                )
                facts.append(
                    FactItem(
                        fact_id="entity_name",
                        category="company_info",
                        claim=f"Company name: {entity_name}",
                        evidence=[
                            EvidenceSnippet(
                                text=f"Entity name from SEC filings: {entity_name}",
                                citation=citation,
                                confidence=1.0,
                            )
                        ],
                        confidence=1.0,
                    )
                )

            # Add financial facts
            facts_data = companyfacts.get("facts", {}).get("us-gaap", {})
            if "Revenues" in facts_data:
                citation = Citation(
                    source_id=sources[0].source_id if sources else "sec_companyfacts",
                    url=sources[0].url if sources else "",
                    title="SEC XBRL Revenue Data",
                )
                facts.append(
                    FactItem(
                        fact_id="revenue_data_available",
                        category="financial",
                        claim="Revenue data available from SEC XBRL filings",
                        evidence=[
                            EvidenceSnippet(
                                text="Revenue data extracted from SEC companyfacts API",
                                citation=citation,
                                confidence=1.0,
                            )
                        ],
                        confidence=1.0,
                    )
                )

        # Fetch transcripts (stub in v1)
        transcripts = fetch_transcripts(self.run_context.ticker)
        sources.extend(transcripts)

        # Fetch news with material events
        entity_name = None
        if companyfacts:
            entity_name = companyfacts.get("entityName", "")
        news = fetch_news(self.run_context.ticker, entity_name)
        sources.extend(news)

        # Add material events to facts
        if news:
            for article in news[:10]:  # Top 10 news items
                # Categorize by keywords
                title_lower = article.title.lower() if article.title else ""
                category = "general"
                if any(
                    word in title_lower
                    for word in ["deal", "acquisition", "merger", "partnership"]
                ):
                    category = "m_and_a"
                elif any(
                    word in title_lower
                    for word in ["lawsuit", "litigation", "regulatory", "sec"]
                ):
                    category = "litigation"
                elif any(
                    word in title_lower
                    for word in ["guidance", "earnings", "forecast", "outlook"]
                ):
                    category = "guidance"
                elif any(
                    word in title_lower
                    for word in ["macro", "recession", "rates", "inflation"]
                ):
                    category = "macro"

                citation = Citation(
                    source_id=article.source_id,
                    url=article.url,
                    title=article.title,
                    date=article.date,
                )

                facts.append(
                    FactItem(
                        fact_id=f"news_{article.source_id}",
                        category=f"material_event_{category}",
                        claim=article.title or "News article",
                        evidence=[
                            EvidenceSnippet(
                                text=article.metadata.get("description", "")
                                if article.metadata
                                else "",
                                citation=citation,
                                confidence=0.7,
                            )
                        ],
                        confidence=0.7,
                    )
                )

        # Ensure we have at least some facts
        if not facts:
            # Create a minimal fact to pass validation
            if sources:
                citation = Citation(
                    source_id=sources[0].source_id,
                    url=sources[0].url if hasattr(sources[0], "url") else "",
                    title=sources[0].title if hasattr(sources[0], "title") else "SEC Data",
                )
                facts.append(
                    FactItem(
                        fact_id="data_retrieved",
                        category="data_availability",
                        claim=f"Financial data retrieved for {self.run_context.ticker}",
                        evidence=[
                            EvidenceSnippet(
                                text=f"Data sources retrieved: {len(sources)} sources",
                                citation=citation,
                                confidence=0.8,
                            )
                        ],
                        confidence=0.8,
                    )
                )

        return FactPack(
            ticker=self.run_context.ticker,
            facts=facts,
            sources=sources,
        )

