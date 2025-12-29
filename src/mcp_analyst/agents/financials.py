"""Financial metrics normalization agent."""

from datetime import datetime
from typing import Dict, List, Optional

from mcp_analyst.orchestrator.run_context import RunContext
from mcp_analyst.schemas.factpack import FactPack
from mcp_analyst.schemas.financials import FinancialSummary, MetricSeries
from mcp_analyst.tools.edgar import (
    extract_financial_metric,
    fetch_companyfacts,
    get_submissions,
    ticker_to_cik,
)


class FinancialsAgent:
    """Normalizes financial metrics from various sources."""

    def __init__(self, run_context: RunContext):
        """Initialize financials agent."""
        self.run_context = run_context

    def _extract_metric_with_fallbacks(
        self, companyfacts: dict, tags: List[str], metric_name: str, unit: str = "USD"
    ) -> Optional[MetricSeries]:
        """Extract metric trying multiple XBRL tags."""
        for tag in tags:
            data = extract_financial_metric(companyfacts, tag, unit, period_type="both")
            if data and (data["annual"] or data["quarterly"]):
                # Combine annual and quarterly
                all_data = data["annual"] + data["quarterly"]
                if all_data:
                    values = [float(entry["val"]) for entry in all_data]
                    periods = []
                    for entry in all_data:
                        end_date = entry.get("end", "")
                        fp = entry.get("fp", "")
                        if fp == "FY":
                            periods.append(end_date[:4])  # Year only
                        else:
                            # Quarterly: "2024-03-31" -> "2024-Q1"
                            year = end_date[:4]
                            month = int(end_date[5:7])
                            quarter = (month - 1) // 3 + 1
                            periods.append(f"{year}-Q{quarter}")

                    return MetricSeries(
                        metric_name=metric_name,
                        values=values,
                        periods=periods,
                        unit=unit,
                    )
        return None

    def _calculate_ttm(self, quarterly_data: List[dict], metric_name: str) -> Optional[float]:
        """Calculate trailing twelve months from quarterly data."""
        if not quarterly_data or len(quarterly_data) < 4:
            return None

        # Get last 4 quarters
        last_4_quarters = quarterly_data[:4]
        ttm_value = sum(float(entry["val"]) for entry in last_4_quarters)
        return ttm_value

    def _build_series(
        self, companyfacts: dict, all_metrics: List[MetricSeries]
    ) -> tuple:
        """Build annual, quarterly, and TTM series."""
        annual_periods = set()
        quarterly_periods = set()
        ttm_value = None

        # Find revenue for TTM calculation
        revenue_quarterly = None
        for metric in all_metrics:
            if metric.metric_name == "Revenue":
                # Separate annual and quarterly periods
                for period in metric.periods:
                    if "-Q" in period:
                        quarterly_periods.add(period)
                    else:
                        annual_periods.add(period)

                # Get quarterly data for TTM
                revenue_data = extract_financial_metric(
                    companyfacts, "Revenues", "USD", period_type="quarterly"
                )
                if revenue_data and revenue_data["quarterly"]:
                    revenue_quarterly = revenue_data["quarterly"]
                    ttm_value = self._calculate_ttm(revenue_quarterly, "Revenue")

        # Get all periods from all metrics
        for metric in all_metrics:
            for period in metric.periods:
                if "-Q" in period:
                    quarterly_periods.add(period)
                else:
                    annual_periods.add(period)

        return sorted(list(annual_periods), reverse=True), sorted(
            list(quarterly_periods), reverse=True
        ), ttm_value

    def analyze(self, factpack: FactPack) -> FinancialSummary:
        """
        Analyze and normalize financial metrics with annual, quarterly, and TTM.

        Args:
            factpack: Structured facts from retrieval

        Returns:
            Normalized financial summary
        """
        # Get CIK and submissions
        cik = ticker_to_cik(self.run_context.ticker)
        if not cik:
            raise ValueError(f"Could not find CIK for ticker {self.run_context.ticker}")

        submissions = get_submissions(cik)
        latest_10k_date = submissions.get("latest_10k_date") if submissions else None
        latest_10q_date = submissions.get("latest_10q_date") if submissions else None

        # Fetch companyfacts
        companyfacts = fetch_companyfacts(self.run_context.ticker)
        if not companyfacts:
            raise ValueError(f"No companyfacts data found for {self.run_context.ticker}")

        metrics: List[MetricSeries] = []

        # Extract key metrics with fallback tags
        # Revenue
        revenue = self._extract_metric_with_fallbacks(
            companyfacts, ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax"], "Revenue", "USD"
        )
        if not revenue:
            raise ValueError("Revenue data missing - cannot proceed without revenue")

        metrics.append(revenue)

        # Operating Income
        operating_income = self._extract_metric_with_fallbacks(
            companyfacts,
            ["OperatingIncomeLoss", "IncomeLossFromContinuingOperationsBeforeTax"],
            "Operating Income",
            "USD",
        )
        if operating_income:
            metrics.append(operating_income)

        # Net Income
        net_income = self._extract_metric_with_fallbacks(
            companyfacts, ["NetIncomeLoss", "ProfitLoss"], "Net Income", "USD"
        )
        if net_income:
            metrics.append(net_income)

        # Capital Expenditures
        capex = self._extract_metric_with_fallbacks(
            companyfacts,
            [
                "PaymentsToAcquirePropertyPlantAndEquipment",
                "CapitalExpenditure",
                "CapitalExpenditures",
            ],
            "Capital Expenditures",
            "USD",
        )
        if capex:
            metrics.append(capex)

        # Cash Flow from Operations
        cfo = self._extract_metric_with_fallbacks(
            companyfacts,
            ["NetCashProvidedByUsedInOperatingActivities", "CashFlowFromOperatingActivities"],
            "Cash Flow from Operations",
            "USD",
        )
        if cfo:
            metrics.append(cfo)

        # D&A
        da = self._extract_metric_with_fallbacks(
            companyfacts,
            [
                "DepreciationDepletionAndAmortization",
                "DepreciationAndAmortization",
            ],
            "Depreciation & Amortization",
            "USD",
        )
        if da:
            metrics.append(da)

        # Shares Outstanding
        shares = self._extract_metric_with_fallbacks(
            companyfacts,
            [
                "EntityCommonStockSharesOutstanding",
                "WeightedAverageNumberOfSharesOutstandingBasic",
                "WeightedAverageNumberOfDilutedSharesOutstanding",
            ],
            "Shares Outstanding",
            "shares",
        )
        if shares:
            metrics.append(shares)

        # Total Debt (try multiple tags)
        debt = self._extract_metric_with_fallbacks(
            companyfacts,
            [
                "LongTermDebtAndCapitalLeaseObligations",
                "LongTermDebt",
                "DebtCurrent",
                "Liabilities",
            ],
            "Total Debt",
            "USD",
        )
        if debt:
            metrics.append(debt)

        # Cash and Cash Equivalents
        cash = self._extract_metric_with_fallbacks(
            companyfacts,
            [
                "CashAndCashEquivalentsAtCarryingValue",
                "CashCashEquivalentsAndShortTermInvestments",
            ],
            "Cash",
            "USD",
        )
        if cash:
            metrics.append(cash)

        # Build annual/quarterly/TTM series
        annual_periods, quarterly_periods, ttm_value = self._build_series(
            companyfacts, metrics
        )

        # Validate we have enough data
        if len(annual_periods) < 3:
            raise ValueError(
                f"Insufficient annual data: {len(annual_periods)} periods (need at least 3)"
            )

        if len(quarterly_periods) < 4:
            raise ValueError(
                f"Insufficient quarterly data: {len(quarterly_periods)} periods (need at least 4)"
            )

        # All periods combined
        all_periods = sorted(set(annual_periods + quarterly_periods), reverse=True)

        # TTM period identifier
        ttm_period = None
        if ttm_value and quarterly_periods:
            latest_quarter = quarterly_periods[0]
            ttm_period = f"TTM-{latest_quarter}"

        return FinancialSummary(
            ticker=self.run_context.ticker,
            metrics=metrics,
            periods=all_periods,
            annual_periods=annual_periods,
            quarterly_periods=quarterly_periods,
            ttm_period=ttm_period,
            metadata={
                "source": "SEC XBRL companyfacts",
                "latest_10k_date": latest_10k_date,
                "latest_10q_date": latest_10q_date,
                "cik": cik,
            },
        )
