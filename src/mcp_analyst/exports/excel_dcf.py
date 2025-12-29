"""Excel DCF workbook export using openpyxl - Analyst-style DCF model."""

from pathlib import Path
from typing import Optional

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from mcp_analyst.orchestrator.run_context import RunContext
from mcp_analyst.schemas.financials import FinancialSummary
from mcp_analyst.schemas.valuation import ValuationOutput


def export_dcf_to_excel(
    valuation_output: ValuationOutput,
    run_context: RunContext,
    financial_summary: Optional[FinancialSummary] = None,
) -> Path:
    """
    Export DCF assumptions and results to Excel workbook (analyst-style).

    Args:
        valuation_output: Valuation output with assumptions and results
        run_context: Run context for file naming

    Returns:
        Path to created Excel file
    """
    wb = Workbook()
    wb.remove(wb.active)  # Remove default sheet

    # Sheet order: Historical, Inputs, DCF, Cases, WACC, Sensitivities, Summary
    if financial_summary:
        historical_sheet = wb.create_sheet("Historical", 0)
        _write_historical(historical_sheet, financial_summary)

    # Inputs/Assumptions sheet
    inputs_sheet = wb.create_sheet("Inputs", 1)
    _write_inputs(inputs_sheet, valuation_output.assumptions)

    # DCF Forecast sheet (main model)
    dcf_sheet = wb.create_sheet("DCF", 2)
    _write_dcf_forecast(dcf_sheet, valuation_output)

    # Cases sheet
    cases_sheet = wb.create_sheet("Cases", 3)
    _write_cases(cases_sheet, valuation_output.assumptions)

    # WACC Calculation sheet
    wacc_sheet = wb.create_sheet("WACC", 4)
    _write_wacc(wacc_sheet, valuation_output.assumptions)

    # Sensitivities sheet
    sensitivities_sheet = wb.create_sheet("Sensitivities", 5)
    _write_sensitivities(sensitivities_sheet, valuation_output.results.sensitivity)

    # Summary sheet
    summary_sheet = wb.create_sheet("Summary", 6)
    _write_summary(summary_sheet, valuation_output)

    # Save workbook
    date_str = run_context.created_at.strftime("%Y-%m-%d")
    filename = f"DCF_{run_context.ticker}_{date_str}.xlsx"
    excel_path = run_context.run_dir / filename
    wb.save(excel_path)

    return excel_path


def _header_style():
    """Get header cell style."""
    return {
        "font": Font(bold=True, color="FFFFFF"),
        "fill": PatternFill(start_color="366092", end_color="366092", fill_type="solid"),
        "alignment": Alignment(horizontal="center", vertical="center"),
        "border": Border(
            left=Side(style="thin"),
            right=Side(style="thin"),
            top=Side(style="thin"),
            bottom=Side(style="thin"),
        ),
    }


def _write_historical(sheet, financial_summary: FinancialSummary) -> None:
    """Write historical financial data to sheet."""
    # Headers
    headers = ["Year"]
    metric_names = [m.metric_name for m in financial_summary.metrics]
    headers.extend(metric_names)
    
    for col, header in enumerate(headers, start=1):
        cell = sheet.cell(row=1, column=col)
        cell.value = header
        for key, value in _header_style().items():
            setattr(cell, key, value)

    # Write data
    periods = financial_summary.periods
    for row_idx, period in enumerate(periods, start=2):
        sheet.cell(row=row_idx, column=1).value = period
        
        for col_idx, metric in enumerate(financial_summary.metrics, start=2):
            period_idx = periods.index(period)
            if period_idx < len(metric.values):
                value = metric.values[period_idx]
                sheet.cell(row=row_idx, column=col_idx).value = value


def _write_inputs(sheet, assumptions) -> None:
    """Write input assumptions to sheet."""
    row = 1
    sheet.cell(row, 1).value = "Input"
    sheet.cell(row, 2).value = "Value"
    for col in [1, 2]:
        cell = sheet.cell(row, col)
        for key, value in _header_style().items():
            setattr(cell, key, value)

    row = 2
    inputs = [
        ("Base Year", assumptions.base_year),
        ("Base Revenue", assumptions.base_year_revenue),
        ("Horizon (years)", assumptions.horizon_years),
        ("Tax Rate", assumptions.tax_rate),
        ("WACC", assumptions.wacc),
        ("Terminal Growth Rate", assumptions.terminal_growth_rate),
        ("Terminal Method", assumptions.terminal_method),
        ("Shares Outstanding", assumptions.shares_out),
        ("Net Debt", assumptions.net_debt),
    ]

    for label, value in inputs:
        sheet.cell(row, 1).value = label
        sheet.cell(row, 2).value = value
        row += 1

    # Revenue growth rates
    sheet.cell(row, 1).value = "Revenue Growth Rates"
    row += 1
    for i, rate in enumerate(assumptions.revenue_growth_rates):
        sheet.cell(row, 1).value = f"Year {i+1}"
        sheet.cell(row, 2).value = rate
        row += 1


def _write_dcf_forecast(sheet, valuation_output: ValuationOutput) -> None:
    """Write full DCF operating forecast to sheet."""
    assumptions = valuation_output.assumptions
    forecast = valuation_output.results.operating_forecast

    # Headers
    headers = [
        "", "Base Year", *assumptions.forecast_years, "Terminal"
    ]
    
    row_labels = [
        "Revenue",
        "(-) COGS ex D&A",
        "(-) SG&A",
        "(-) D&A",
        "EBIT",
        "(-) Taxes",
        "NOPAT",
        "(+) D&A add-back",
        "(+) SBC add-back",
        "(-) ΔNWC",
        "(-) Capex",
        "Unlevered FCF",
        "Discount Factor",
        "PV of UFCF",
    ]

    # Write headers
    for col, header in enumerate(headers, start=1):
        cell = sheet.cell(row=1, column=col)
        cell.value = header
        for key, value in _header_style().items():
            setattr(cell, key, value)

    # Write base year
    sheet.cell(row=2, column=1).value = "Base Year"
    sheet.cell(row=2, column=2).value = assumptions.base_year_revenue

    # Write forecast data
    for row_idx, label in enumerate(row_labels, start=2):
        sheet.cell(row=row_idx, column=1).value = label

    # Fill in forecast years
    for col_idx, year in enumerate(assumptions.forecast_years, start=3):
        if col_idx - 3 < len(forecast):
            f = forecast[col_idx - 3]
            sheet.cell(2, col_idx).value = f.revenue  # Revenue
            sheet.cell(3, col_idx).value = -f.cogs_ex_da  # COGS
            sheet.cell(4, col_idx).value = -f.sga  # SG&A
            sheet.cell(5, col_idx).value = -f.da  # D&A
            sheet.cell(6, col_idx).value = f.ebit  # EBIT
            sheet.cell(7, col_idx).value = -f.taxes  # Taxes
            sheet.cell(8, col_idx).value = f.nopat  # NOPAT
            sheet.cell(9, col_idx).value = f.da_addback  # D&A add-back
            sheet.cell(10, col_idx).value = f.sbc_addback  # SBC add-back
            sheet.cell(11, col_idx).value = -f.delta_nwc  # ΔNWC
            sheet.cell(12, col_idx).value = -f.capex  # Capex
            sheet.cell(13, col_idx).value = f.unlevered_fcf  # UFCF
            sheet.cell(14, col_idx).value = f.discount_factor  # Discount factor
            sheet.cell(15, col_idx).value = f.pv_ufcf  # PV of UFCF

    # Terminal value
    terminal_col = len(assumptions.forecast_years) + 3
    sheet.cell(15, terminal_col).value = valuation_output.results.pv_terminal_value

    # Summary rows
    summary_row = len(row_labels) + 3
    sheet.cell(summary_row, 1).value = "Total PV of UFCF"
    sheet.cell(summary_row, 2).value = sum(f.pv_ufcf for f in forecast)
    sheet.cell(summary_row + 1, 1).value = "PV of Terminal Value"
    sheet.cell(summary_row + 1, 2).value = valuation_output.results.pv_terminal_value
    sheet.cell(summary_row + 2, 1).value = "Enterprise Value"
    sheet.cell(summary_row + 2, 2).value = valuation_output.results.total_enterprise_value
    sheet.cell(summary_row + 3, 1).value = "(-) Net Debt"
    sheet.cell(summary_row + 3, 2).value = -assumptions.net_debt
    sheet.cell(summary_row + 4, 1).value = "Equity Value"
    sheet.cell(summary_row + 4, 2).value = valuation_output.results.equity_value
    sheet.cell(summary_row + 5, 1).value = "Shares Outstanding"
    sheet.cell(summary_row + 5, 2).value = assumptions.shares_out
    sheet.cell(summary_row + 6, 1).value = "Fair Value per Share"
    sheet.cell(summary_row + 6, 2).value = valuation_output.results.fair_value_per_share
    sheet.cell(summary_row + 6, 2).font = Font(bold=True, size=12)


def _write_cases(sheet, assumptions) -> None:
    """Write scenario cases (Base/Bull/Bear) to sheet."""
    row = 1
    headers = ["Case", "Growth Fade", "Steady Margin", "WACC", "Terminal Growth"]
    for col, header in enumerate(headers, start=1):
        cell = sheet.cell(row, col)
        cell.value = header
        for key, value in _header_style().items():
            setattr(cell, key, value)

    # Base case
    row = 2
    sheet.cell(row, 1).value = "Base"
    sheet.cell(row, 2).value = "50% fade"
    sheet.cell(row, 3).value = assumptions.cogs_ex_da_pct_rev[0] + assumptions.sga_pct_rev[0] if assumptions.cogs_ex_da_pct_rev else 0.85
    sheet.cell(row, 4).value = assumptions.wacc
    sheet.cell(row, 5).value = assumptions.terminal_growth_rate

    # Bull case
    row = 3
    sheet.cell(row, 1).value = "Bull"
    sheet.cell(row, 2).value = "30% fade"
    sheet.cell(row, 3).value = (assumptions.cogs_ex_da_pct_rev[0] + assumptions.sga_pct_rev[0] - 0.05) if assumptions.cogs_ex_da_pct_rev else 0.80
    sheet.cell(row, 4).value = assumptions.wacc - 0.01
    sheet.cell(row, 5).value = assumptions.terminal_growth_rate + 0.005

    # Bear case
    row = 4
    sheet.cell(row, 1).value = "Bear"
    sheet.cell(row, 2).value = "70% fade"
    sheet.cell(row, 3).value = (assumptions.cogs_ex_da_pct_rev[0] + assumptions.sga_pct_rev[0] + 0.05) if assumptions.cogs_ex_da_pct_rev else 0.90
    sheet.cell(row, 4).value = assumptions.wacc + 0.01
    sheet.cell(row, 5).value = assumptions.terminal_growth_rate - 0.005


def _write_wacc(sheet, assumptions) -> None:
    """Write WACC calculation to sheet."""
    row = 1
    sheet.cell(row, 1).value = "Component"
    sheet.cell(row, 2).value = "Value"
    for col in [1, 2]:
        cell = sheet.cell(row, col)
        for key, value in _header_style().items():
            setattr(cell, key, value)

    # Cost of Equity
    row = 2
    sheet.cell(row, 1).value = "Risk-Free Rate"
    sheet.cell(row, 2).value = assumptions.risk_free_rate
    row += 1

    sheet.cell(row, 1).value = "Equity Risk Premium"
    sheet.cell(row, 2).value = assumptions.equity_risk_premium
    row += 1

    sheet.cell(row, 1).value = "Beta"
    sheet.cell(row, 2).value = assumptions.beta
    row += 1

    cost_of_equity = assumptions.risk_free_rate + (assumptions.beta * assumptions.equity_risk_premium)
    sheet.cell(row, 1).value = "Cost of Equity"
    sheet.cell(row, 2).value = cost_of_equity
    row += 2

    # Cost of Debt
    sheet.cell(row, 1).value = "Cost of Debt"
    sheet.cell(row, 2).value = assumptions.cost_of_debt
    row += 1

    sheet.cell(row, 1).value = "Tax Rate"
    sheet.cell(row, 2).value = assumptions.tax_rate
    row += 1

    after_tax_cost_of_debt = assumptions.cost_of_debt * (1 - assumptions.tax_rate)
    sheet.cell(row, 1).value = "After-Tax Cost of Debt"
    sheet.cell(row, 2).value = after_tax_cost_of_debt
    row += 2

    # Weights
    sheet.cell(row, 1).value = "Debt/Equity Ratio"
    sheet.cell(row, 2).value = assumptions.debt_to_equity_ratio
    row += 1

    # Calculate weights
    debt_weight = assumptions.debt_to_equity_ratio / (1 + assumptions.debt_to_equity_ratio)
    equity_weight = 1 / (1 + assumptions.debt_to_equity_ratio)

    sheet.cell(row, 1).value = "Debt Weight"
    sheet.cell(row, 2).value = debt_weight
    row += 1

    sheet.cell(row, 1).value = "Equity Weight"
    sheet.cell(row, 2).value = equity_weight
    row += 2

    # WACC
    wacc = (equity_weight * cost_of_equity) + (debt_weight * after_tax_cost_of_debt)
    sheet.cell(row, 1).value = "WACC"
    sheet.cell(row, 2).value = wacc
    sheet.cell(row, 2).font = Font(bold=True, size=12)


def _write_sensitivities(sheet, sensitivity: dict) -> None:
    """Write 2D sensitivity table to sheet."""
    if not sensitivity:
        sheet.cell(1, 1).value = "No sensitivity data available"
        return

    # Get WACC and growth ranges
    wacc_values = sorted([float(k) for k in sensitivity.keys()])
    growth_values = sorted([float(k) for k in list(sensitivity.values())[0].keys()])

    # Headers
    row = 1
    sheet.cell(row, 1).value = "WACC \\ Terminal Growth"
    for col, growth in enumerate(growth_values, start=2):
        cell = sheet.cell(row, col)
        cell.value = f"{growth:.3f}"
        for key, value in _header_style().items():
            setattr(cell, key, value)

    # Data rows
    for row_idx, wacc in enumerate(wacc_values, start=2):
        cell = sheet.cell(row_idx, 1)
        cell.value = f"{wacc:.3f}"
        for key, value in _header_style().items():
            setattr(cell, key, value)

        wacc_key = f"{wacc:.3f}"
        if wacc_key in sensitivity:
            for col_idx, growth in enumerate(growth_values, start=2):
                growth_key = f"{growth:.3f}"
                if growth_key in sensitivity[wacc_key]:
                    sheet.cell(row_idx, col_idx).value = sensitivity[wacc_key][growth_key]


def _write_summary(sheet, valuation_output: ValuationOutput) -> None:
    """Write summary sheet with key outputs."""
    row = 1
    sheet.cell(row, 1).value = "Metric"
    sheet.cell(row, 2).value = "Value"
    for col in [1, 2]:
        cell = sheet.cell(row, col)
        for key, value in _header_style().items():
            setattr(cell, key, value)

    results = valuation_output.results
    assumptions = valuation_output.assumptions

    summary_data = [
        ("Fair Value per Share", results.fair_value_per_share),
        ("Equity Value", results.equity_value),
        ("Enterprise Value", results.total_enterprise_value),
        ("PV of Terminal Value", results.pv_terminal_value),
        ("Total PV of UFCF", sum(f.pv_ufcf for f in results.operating_forecast)),
        ("Net Debt", assumptions.net_debt),
        ("Shares Outstanding", assumptions.shares_out),
        ("WACC", assumptions.wacc),
        ("Terminal Growth Rate", assumptions.terminal_growth_rate),
    ]

    row = 2
    for label, value in summary_data:
        sheet.cell(row, 1).value = label
        sheet.cell(row, 2).value = value
        if "Fair Value" in label:
            sheet.cell(row, 2).font = Font(bold=True, size=14)
        row += 1
