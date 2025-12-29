"""Financial metrics normalization agent."""

from typing import List, Optional

from mcp_analyst.orchestrator.run_context import RunContext
from mcp_analyst.schemas.factpack import FactPack
from mcp_analyst.schemas.financials import FinancialSummary, MetricSeries
from mcp_analyst.tools.edgar import extract_financial_metric, fetch_companyfacts


class FinancialsAgent:
    """Normalizes financial metrics from various sources."""

    def __init__(self, run_context: RunContext):
        """Initialize financials agent."""
        self.run_context = run_context

    def _extract_metric(
        self, companyfacts: dict, tag: str, metric_name: str, unit: str = "USD"
    ) -> Optional[MetricSeries]:
        """Extract a metric series from companyfacts."""
        data = extract_financial_metric(companyfacts, tag, unit)
        if not data:
            return None

        values = [float(entry["val"]) for entry in data]
        periods = [entry.get("end", "")[:4] for entry in data]  # Extract year

        return MetricSeries(
            metric_name=metric_name,
            values=values,
            periods=periods,
            unit=unit,
        )

    def analyze(self, factpack: FactPack) -> FinancialSummary:
        """
        Analyze and normalize financial metrics.

        Args:
            factpack: Structured facts from retrieval

        Returns:
            Normalized financial summary
        """
        # Fetch companyfacts
        companyfacts = fetch_companyfacts(self.run_context.ticker)
        if not companyfacts:
            raise ValueError(f"No companyfacts data found for {self.run_context.ticker}")

        metrics: List[MetricSeries] = []
        periods_set = set()

        # Extract key metrics
        # Revenue
        revenue = self._extract_metric(
            companyfacts, "Revenues", "Revenue", "USD"
        )
        if revenue:
            metrics.append(revenue)
            periods_set.update(revenue.periods)

        # Operating Income
        operating_income = self._extract_metric(
            companyfacts, "OperatingIncomeLoss", "Operating Income", "USD"
        )
        if operating_income:
            metrics.append(operating_income)

        # Net Income
        net_income = self._extract_metric(
            companyfacts, "NetIncomeLoss", "Net Income", "USD"
        )
        if net_income:
            metrics.append(net_income)

        # Capital Expenditures
        capex = self._extract_metric(
            companyfacts, "CapitalExpenditure", "Capital Expenditures", "USD"
        )
        if not capex:
            # Try alternative tag
            capex = self._extract_metric(
                companyfacts, "PaymentsToAcquirePropertyPlantAndEquipment", "Capital Expenditures", "USD"
            )
        if capex:
            metrics.append(capex)

        # Cash Flow from Operations
        cfo = self._extract_metric(
            companyfacts, "NetCashProvidedByUsedInOperatingActivities", "Cash Flow from Operations", "USD"
        )
        if cfo:
            metrics.append(cfo)

        # Shares Outstanding (try multiple tags)
        shares = self._extract_metric(
            companyfacts, "EntityCommonStockSharesOutstanding", "Shares Outstanding", "shares"
        )
        if not shares:
            shares = self._extract_metric(
                companyfacts, "WeightedAverageNumberOfSharesOutstandingBasic", "Shares Outstanding", "shares"
            )
        if not shares:
            shares = self._extract_metric(
                companyfacts, "WeightedAverageNumberOfDilutedSharesOutstanding", "Shares Outstanding", "shares"
            )
        if shares:
            metrics.append(shares)

        # Total Debt
        debt = self._extract_metric(
            companyfacts, "LongTermDebtAndCapitalLeaseObligations", "Total Debt", "USD"
        )
        if debt:
            metrics.append(debt)

        # Cash and Cash Equivalents
        cash = self._extract_metric(
            companyfacts, "CashAndCashEquivalentsAtCarryingValue", "Cash", "USD"
        )
        if cash:
            metrics.append(cash)

        # Get all unique periods and sort
        periods = sorted(list(periods_set), reverse=True)

        if not periods:
            raise ValueError("No financial periods extracted")

        return FinancialSummary(
            ticker=self.run_context.ticker,
            metrics=metrics,
            periods=periods,
            metadata={"source": "SEC XBRL companyfacts"},
        )

