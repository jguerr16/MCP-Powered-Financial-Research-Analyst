"""Schema validation tests."""

import pytest

from mcp_analyst.schemas.factpack import FactPack
from mcp_analyst.schemas.financials import FinancialSummary
from mcp_analyst.schemas.valuation import DcfAssumptions, DcfResults, ValuationOutput
from mcp_analyst.schemas.skeptic import SkepticReport


def test_factpack_schema():
    """Test FactPack schema validation."""
    factpack = FactPack(ticker="UBER", facts=[], sources=[])
    assert factpack.ticker == "UBER"
    assert isinstance(factpack.facts, list)
    assert isinstance(factpack.sources, list)


def test_financial_summary_schema():
    """Test FinancialSummary schema validation."""
    summary = FinancialSummary(ticker="UBER", metrics=[], periods=[])
    assert summary.ticker == "UBER"
    assert isinstance(summary.metrics, list)


def test_dcf_assumptions_schema():
    """Test DcfAssumptions schema validation."""
    assumptions = DcfAssumptions(
        horizon_years=5,
        terminal_method="gordon",
        wacc=0.10,
        terminal_growth_rate=0.03,
        revenue_growth_rates=[0.15, 0.12, 0.10],
        margin_assumptions={"operating_margin": 0.15},
    )
    assert assumptions.horizon_years == 5
    assert assumptions.terminal_method == "gordon"


def test_valuation_output_schema():
    """Test ValuationOutput schema validation."""
    assumptions = DcfAssumptions(
        horizon_years=5,
        terminal_method="gordon",
        wacc=0.10,
        terminal_growth_rate=0.03,
        revenue_growth_rates=[],
        margin_assumptions={},
    )
    results = DcfResults(
        fair_value_per_share=50.0,
        total_enterprise_value=1000000000.0,
        equity_value=1000000000.0,
        present_values={},
    )
    output = ValuationOutput(assumptions=assumptions, results=results)
    assert output.assumptions == assumptions
    assert output.results == results


def test_skeptic_report_schema():
    """Test SkepticReport schema validation."""
    report = SkepticReport(flags=[], citation_coverage=0.8, confidence_score=0.75)
    assert report.citation_coverage == 0.8
    assert report.confidence_score == 0.75

