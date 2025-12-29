"""End-to-end pipeline execution."""

from mcp_analyst.agents.financials import FinancialsAgent
from mcp_analyst.agents.retriever import RetrieverAgent
from mcp_analyst.agents.skeptic import SkepticAgent
from mcp_analyst.agents.synthesizer import SynthesizerAgent
from mcp_analyst.agents.valuation import ValuationAgent
from mcp_analyst.exports.excel_dcf import export_dcf_to_excel
from mcp_analyst.logging import setup_logging
from mcp_analyst.orchestrator.run_context import RunContext
from mcp_analyst.storage.artifacts import save_artifacts, save_failed_run
from mcp_analyst.storage.runs import create_run_directory


class Pipeline:
    """End-to-end analysis pipeline."""

    def __init__(self, run_context: RunContext):
        """Initialize pipeline with run context."""
        self.run_context = run_context
        self.logger = setup_logging(run_dir=run_context.run_dir)

    def _validate_retriever(self, factpack) -> None:
        """Validate retriever output."""
        if not factpack.sources or len(factpack.sources) == 0:
            raise ValueError("Retriever failed: No sources retrieved")
        # For v1.1, we require at least 1 fact (we'll get more from financials)
        if not factpack.facts or len(factpack.facts) < 1:
            raise ValueError(
                f"Retriever failed: No facts retrieved ({len(factpack.facts) if factpack.facts else 0})"
            )

    def _validate_financials(self, financial_summary) -> None:
        """Validate financials output."""
        if not financial_summary.periods or len(financial_summary.periods) < 3:
            raise ValueError(
                f"Financials failed: Insufficient periods ({len(financial_summary.periods) if financial_summary.periods else 0} < 3)"
            )

        # Check for revenue series
        revenue_series = next(
            (m for m in financial_summary.metrics if m.metric_name.lower() == "revenue"),
            None,
        )
        if not revenue_series or not revenue_series.values:
            raise ValueError("Financials failed: Revenue series missing or empty")

        # Check for at least one of: operating income, CFO, capex
        has_operating_income = any(
            "operating" in m.metric_name.lower() and "income" in m.metric_name.lower()
            for m in financial_summary.metrics
        )
        has_cfo = any("cfo" in m.metric_name.lower() or "cash flow" in m.metric_name.lower() for m in financial_summary.metrics)
        has_capex = any("capex" in m.metric_name.lower() or "capital expenditure" in m.metric_name.lower() for m in financial_summary.metrics)

        if not (has_operating_income or has_cfo or has_capex):
            raise ValueError(
                "Financials failed: Missing required metrics (operating income, CFO, or capex)"
            )

    def _validate_valuation(self, valuation_output) -> None:
        """Validate valuation output."""
        assumptions = valuation_output.assumptions
        if not assumptions.revenue_growth_rates or len(assumptions.revenue_growth_rates) != assumptions.horizon_years:
            raise ValueError(
                f"Valuation failed: Revenue growth rates missing or incorrect length "
                f"(expected {assumptions.horizon_years}, got {len(assumptions.revenue_growth_rates) if assumptions.revenue_growth_rates else 0})"
            )

        if assumptions.base_year_revenue <= 0:
            raise ValueError(f"Valuation failed: Base revenue missing or <= 0 (got {assumptions.base_year_revenue})")

        if assumptions.shares_out <= 0:
            raise ValueError(f"Valuation failed: Shares outstanding missing or <= 0 (got {assumptions.shares_out})")

        if not valuation_output.results.operating_forecast or len(valuation_output.results.operating_forecast) != assumptions.horizon_years:
            raise ValueError(
                f"Valuation failed: Operating forecast missing or incorrect length "
                f"(expected {assumptions.horizon_years}, got {len(valuation_output.results.operating_forecast) if valuation_output.results.operating_forecast else 0})"
            )

    def execute(self) -> None:
        """Execute the full analysis pipeline."""
        import time
        from datetime import datetime

        start_time = time.time()
        self.logger.info(f"Starting analysis for {self.run_context.ticker}")

        # Create run directory
        create_run_directory(self.run_context)

        try:
            # Step 1: Retrieve data
            step_start = time.time()
            self.logger.info("Step 1: Retrieving data sources")
            retriever = RetrieverAgent(self.run_context)
            factpack = retriever.retrieve()
            self._validate_retriever(factpack)
            self.logger.info(f"Step 1 complete: {len(factpack.sources)} sources, {len(factpack.facts)} facts")

            # Step 2: Normalize financials
            step_start = time.time()
            self.logger.info("Step 2: Normalizing financial metrics")
            financials_agent = FinancialsAgent(self.run_context)
            financial_summary = financials_agent.analyze(factpack)
            self._validate_financials(financial_summary)
            self.logger.info(f"Step 2 complete: {len(financial_summary.periods)} periods, {len(financial_summary.metrics)} metrics")

            # Step 3: Generate valuation
            step_start = time.time()
            self.logger.info("Step 3: Generating DCF valuation")
            valuation_agent = ValuationAgent(self.run_context)
            valuation_output = valuation_agent.valuate(financial_summary, factpack)
            self._validate_valuation(valuation_output)
            self.logger.info("Step 3 complete: DCF valuation generated")

            # Step 4: Skeptic validation
            step_start = time.time()
            self.logger.info("Step 4: Running skeptic validation")
            skeptic_agent = SkepticAgent(self.run_context)
            skeptic_report = skeptic_agent.validate(factpack, valuation_output)

            # Step 5: Synthesize memo
            step_start = time.time()
            self.logger.info("Step 5: Synthesizing research memo")
            synthesizer = SynthesizerAgent(self.run_context)
            memo = synthesizer.synthesize(
                factpack, financial_summary, valuation_output, skeptic_report
            )

            # Step 6: Export Excel
            step_start = time.time()
            self.logger.info("Step 6: Exporting Excel workbook")
            excel_path = export_dcf_to_excel(
                valuation_output, self.run_context, financial_summary=financial_summary
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

        except Exception as e:
            self.logger.error(f"Pipeline failed: {str(e)}")
            save_failed_run(self.run_context, str(e))
            raise

