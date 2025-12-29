"""Excel DCF workbook export using openpyxl."""

from pathlib import Path
from typing import Optional

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill

from mcp_analyst.orchestrator.run_context import RunContext
from mcp_analyst.schemas.financials import FinancialSummary
from mcp_analyst.schemas.valuation import ValuationOutput


def export_dcf_to_excel(
    valuation_output: ValuationOutput,
    run_context: RunContext,
    financial_summary: Optional[FinancialSummary] = None,
) -> Path:
    """
    Export DCF assumptions and results to Excel workbook.

    Args:
        valuation_output: Valuation output with assumptions and results
        run_context: Run context for file naming

    Returns:
        Path to created Excel file
    """
    wb = Workbook()
    wb.remove(wb.active)  # Remove default sheet

    # Historical sheet (first)
    if financial_summary:
        historical_sheet = wb.create_sheet("Historical")
        _write_historical(historical_sheet, financial_summary)

    # Assumptions sheet
    assumptions_sheet = wb.create_sheet("Assumptions")
    _write_assumptions(assumptions_sheet, valuation_output.assumptions)

    # Results sheet
    results_sheet = wb.create_sheet("Results")
    _write_results(results_sheet, valuation_output.results)

    # Sensitivity sheet (if available)
    if valuation_output.sensitivity:
        sensitivity_sheet = wb.create_sheet("Sensitivity")
        _write_sensitivity(sensitivity_sheet, valuation_output.sensitivity)

    # Save workbook
    date_str = run_context.created_at.strftime("%Y-%m-%d")
    filename = f"DCF_{run_context.ticker}_{date_str}.xlsx"
    excel_path = run_context.run_dir / filename
    wb.save(excel_path)

    return excel_path


def _write_assumptions(sheet, assumptions) -> None:
    """Write assumptions to sheet."""
    sheet["A1"] = "Assumption"
    sheet["B1"] = "Value"
    sheet["A1"].font = Font(bold=True)
    sheet["B1"].font = Font(bold=True)

    row = 2
    sheet[f"A{row}"] = "Horizon (years)"
    sheet[f"B{row}"] = assumptions.horizon_years
    row += 1

    sheet[f"A{row}"] = "Terminal Method"
    sheet[f"B{row}"] = assumptions.terminal_method
    row += 1

    sheet[f"A{row}"] = "WACC"
    sheet[f"B{row}"] = assumptions.wacc
    row += 1

    sheet[f"A{row}"] = "Terminal Growth Rate"
    sheet[f"B{row}"] = assumptions.terminal_growth_rate
    row += 1

    # Revenue growth rates
    for i, rate in enumerate(assumptions.revenue_growth_rates):
        sheet[f"A{row}"] = f"Revenue Growth Year {i+1}"
        sheet[f"B{row}"] = rate
        row += 1

    # Margin assumptions
    for key, value in assumptions.margin_assumptions.items():
        sheet[f"A{row}"] = key.replace("_", " ").title()
        sheet[f"B{row}"] = value
        row += 1


def _write_results(sheet, results) -> None:
    """Write results to sheet."""
    sheet["A1"] = "Metric"
    sheet["B1"] = "Value"
    sheet["A1"].font = Font(bold=True)
    sheet["B1"].font = Font(bold=True)

    row = 2
    sheet[f"A{row}"] = "Fair Value per Share"
    sheet[f"B{row}"] = results.fair_value_per_share
    row += 1

    sheet[f"A{row}"] = "Total Enterprise Value"
    sheet[f"B{row}"] = results.total_enterprise_value
    row += 1

    sheet[f"A{row}"] = "Equity Value"
    sheet[f"B{row}"] = results.equity_value
    row += 1

    # Present values
    for key, value in results.present_values.items():
        sheet[f"A{row}"] = f"PV {key}"
        sheet[f"B{row}"] = value
        row += 1


def _write_historical(sheet, financial_summary: FinancialSummary) -> None:
    """Write historical financial data to sheet."""
    # Headers
    headers = ["Year"]
    metric_names = [m.metric_name for m in financial_summary.metrics]
    headers.extend(metric_names)
    
    for col, header in enumerate(headers, start=1):
        cell = sheet.cell(row=1, column=col)
        cell.value = header
        cell.font = Font(bold=True)
        cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        cell.font = Font(bold=True, color="FFFFFF")

    # Get revenue for margin calculations
    revenue_metric = next((m for m in financial_summary.metrics if m.metric_name == "Revenue"), None)
    operating_income_metric = next((m for m in financial_summary.metrics if m.metric_name == "Operating Income"), None)

    # Write data
    periods = financial_summary.periods
    for row_idx, period in enumerate(periods, start=2):
        sheet.cell(row=row_idx, column=1).value = period
        
        for col_idx, metric in enumerate(financial_summary.metrics, start=2):
            period_idx = periods.index(period)
            if period_idx < len(metric.values):
                value = metric.values[period_idx]
                sheet.cell(row=row_idx, column=col_idx).value = value

        # Add calculated metrics
        if revenue_metric and operating_income_metric:
            rev_idx = periods.index(period)
            if rev_idx < len(revenue_metric.values) and rev_idx < len(operating_income_metric.values):
                revenue = revenue_metric.values[rev_idx]
                op_inc = operating_income_metric.values[rev_idx] if rev_idx < len(operating_income_metric.values) else 0
                if revenue > 0:
                    margin = op_inc / revenue
                    # Add margin column if not already present
                    margin_col = len(headers) + 1
                    if row_idx == 2:  # Header row
                        sheet.cell(row=1, column=margin_col).value = "Operating Margin"
                        sheet.cell(row=1, column=margin_col).font = Font(bold=True)
                    sheet.cell(row=row_idx, column=margin_col).value = margin


def _write_assumptions(sheet, assumptions) -> None:
    """Write assumptions to sheet."""
    sheet["A1"] = "Assumption"
    sheet["B1"] = "Value"
    sheet["A1"].font = Font(bold=True)
    sheet["B1"].font = Font(bold=True)

    row = 2
    sheet[f"A{row}"] = "Base Year"
    sheet[f"B{row}"] = assumptions.base_year
    row += 1

    sheet[f"A{row}"] = "Base Revenue"
    sheet[f"B{row}"] = assumptions.base_revenue
    row += 1

    sheet[f"A{row}"] = "Horizon (years)"
    sheet[f"B{row}"] = assumptions.horizon_years
    row += 1

    sheet[f"A{row}"] = "Terminal Method"
    sheet[f"B{row}"] = assumptions.terminal_method
    row += 1

    sheet[f"A{row}"] = "WACC"
    sheet[f"B{row}"] = assumptions.wacc
    row += 1

    sheet[f"A{row}"] = "Terminal Growth Rate"
    sheet[f"B{row}"] = assumptions.terminal_growth_rate
    row += 1

    sheet[f"A{row}"] = "Tax Rate"
    sheet[f"B{row}"] = assumptions.tax_rate
    row += 1

    sheet[f"A{row}"] = "Shares Outstanding"
    sheet[f"B{row}"] = assumptions.shares_out
    row += 1

    sheet[f"A{row}"] = "Net Debt"
    sheet[f"B{row}"] = assumptions.net_debt
    row += 1

    sheet[f"A{row}"] = "Capex % Revenue"
    sheet[f"B{row}"] = assumptions.capex_pct_rev
    row += 1

    # Revenue growth rates
    for i, rate in enumerate(assumptions.revenue_growth_rates):
        sheet[f"A{row}"] = f"Revenue Growth Year {i+1}"
        sheet[f"B{row}"] = rate
        row += 1

    # Margin assumptions
    for key, value in assumptions.margin_assumptions.items():
        sheet[f"A{row}"] = key.replace("_", " ").title()
        sheet[f"B{row}"] = value
        row += 1


def _write_sensitivity(sheet, sensitivity) -> None:
    """Write sensitivity analysis to sheet."""
    sheet["A1"] = "Variable"
    sheet["B1"] = "Impact"
    sheet["A1"].font = Font(bold=True)
    sheet["B1"].font = Font(bold=True)

    row = 2
    for key, value in sensitivity.items():
        sheet[f"A{row}"] = key
        sheet[f"B{row}"] = value
        row += 1

