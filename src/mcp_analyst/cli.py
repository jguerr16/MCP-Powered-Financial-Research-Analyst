"""Command-line interface for MCP analyst."""

import argparse
from pathlib import Path
from typing import Optional

from mcp_analyst.orchestrator.pipeline import Pipeline
from mcp_analyst.orchestrator.run_context import RunContext


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="MCP-Powered Financial Research Analyst"
    )
    parser.add_argument(
        "command",
        choices=["analyze"],
        help="Command to execute",
    )
    parser.add_argument(
        "ticker",
        type=str.upper,
        help="Stock ticker symbol (e.g., UBER)",
    )
    parser.add_argument(
        "--sector",
        type=str,
        help="Company sector (e.g., Technology)",
    )
    parser.add_argument(
        "--horizon",
        type=str,
        default="5y",
        help="Time horizon for analysis (e.g., 5y, 10y)",
    )
    parser.add_argument(
        "--risk",
        type=str,
        choices=["conservative", "moderate", "aggressive"],
        default="moderate",
        help="Risk appetite",
    )
    parser.add_argument(
        "--focus",
        type=str,
        help="Focus area (e.g., revenue-growth, profitability)",
    )
    parser.add_argument(
        "--terminal",
        type=str,
        default="gordon",
        choices=["gordon", "perpetuity"],
        help="Terminal value method",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("runs"),
        help="Output directory for run artifacts",
    )

    args = parser.parse_args()

    if args.command == "analyze":
        run_analysis(
            ticker=args.ticker,
            sector=args.sector,
            horizon=args.horizon,
            risk=args.risk,
            focus=args.focus,
            terminal=args.terminal,
            output_dir=args.output_dir,
        )


def run_analysis(
    ticker: str,
    sector: Optional[str],
    horizon: str,
    risk: str,
    focus: Optional[str],
    terminal: str,
    output_dir: Path,
) -> None:
    """Run financial analysis for a ticker."""
    # Create run context
    run_context = RunContext.create(
        ticker=ticker,
        sector=sector,
        horizon=horizon,
        risk=risk,
        focus=focus,
        terminal=terminal,
        output_dir=output_dir,
    )

    # Initialize pipeline
    pipeline = Pipeline(run_context=run_context)

    # Execute pipeline
    pipeline.execute()


if __name__ == "__main__":
    main()

