"""End-to-end pipeline execution."""

from mcp_analyst.agents.financials import FinancialsAgent
from mcp_analyst.agents.retriever import RetrieverAgent
from mcp_analyst.agents.skeptic import SkepticAgent
from mcp_analyst.agents.synthesizer import SynthesizerAgent
from mcp_analyst.agents.valuation import ValuationAgent
from mcp_analyst.exports.excel_dcf import export_dcf_to_excel
from mcp_analyst.logging import setup_logging
from mcp_analyst.orchestrator.run_context import RunContext
from mcp_analyst.storage.artifacts import save_artifacts
from mcp_analyst.storage.runs import create_run_directory


class Pipeline:
    """End-to-end analysis pipeline."""

    def __init__(self, run_context: RunContext):
        """Initialize pipeline with run context."""
        self.run_context = run_context
        self.logger = setup_logging(run_dir=run_context.run_dir)

    def execute(self) -> None:
        """Execute the full analysis pipeline."""
        self.logger.info(f"Starting analysis for {self.run_context.ticker}")

        # Create run directory
        create_run_directory(self.run_context)

        # Step 1: Retrieve data
        self.logger.info("Step 1: Retrieving data sources")
        retriever = RetrieverAgent(self.run_context)
        factpack = retriever.retrieve()

        # Step 2: Normalize financials
        self.logger.info("Step 2: Normalizing financial metrics")
        financials_agent = FinancialsAgent(self.run_context)
        financial_summary = financials_agent.analyze(factpack)

        # Step 3: Generate valuation
        self.logger.info("Step 3: Generating DCF valuation")
        valuation_agent = ValuationAgent(self.run_context)
        valuation_output = valuation_agent.valuate(financial_summary, factpack)

        # Step 4: Skeptic validation
        self.logger.info("Step 4: Running skeptic validation")
        skeptic_agent = SkepticAgent(self.run_context)
        skeptic_report = skeptic_agent.validate(factpack, valuation_output)

        # Step 5: Synthesize memo
        self.logger.info("Step 5: Synthesizing research memo")
        synthesizer = SynthesizerAgent(self.run_context)
        memo = synthesizer.synthesize(
            factpack, financial_summary, valuation_output, skeptic_report
        )

        # Step 6: Export Excel
        self.logger.info("Step 6: Exporting Excel workbook")
        excel_path = export_dcf_to_excel(
            valuation_output, self.run_context
        )

        # Step 7: Save all artifacts
        self.logger.info("Step 7: Saving artifacts")
        save_artifacts(
            run_context=self.run_context,
            factpack=factpack,
            financial_summary=financial_summary,
            valuation_output=valuation_output,
            skeptic_report=skeptic_report,
            memo=memo,
            excel_path=excel_path,
        )

        self.logger.info(f"Analysis complete: {self.run_context.run_dir}")

