"""Excel DCF workbook export using openpyxl."""

from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill

from mcp_analyst.orchestrator.run_context import RunContext
from mcp_analyst.schemas.valuation import ValuationOutput


def export_dcf_to_excel(
    valuation_output: ValuationOutput,
    run_context: RunContext,
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

