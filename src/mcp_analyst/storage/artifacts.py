"""Artifact save/load utilities."""

import json
from datetime import datetime
from pathlib import Path

from mcp_analyst.orchestrator.run_context import RunContext
from mcp_analyst.schemas.factpack import FactPack
from mcp_analyst.schemas.financials import FinancialSummary
from mcp_analyst.schemas.manifest import RunManifest
from mcp_analyst.schemas.skeptic import SkepticReport
from mcp_analyst.schemas.valuation import ValuationOutput
from mcp_analyst.storage.hashing import compute_file_hash


def save_artifacts(
    run_context: RunContext,
    factpack: FactPack,
    financial_summary: FinancialSummary,
    valuation_output: ValuationOutput,
    skeptic_report: SkepticReport,
    memo: str,
    excel_path: Path,
    quote_data=None,
) -> None:
    """
    Save all artifacts to run directory.

    Args:
        run_context: Run context
        factpack: FactPack
        financial_summary: Financial summary
        valuation_output: Valuation output
        skeptic_report: Skeptic report
        memo: Memo markdown content
        excel_path: Path to Excel file
    """
    run_dir = run_context.run_dir
    artifacts = {}
    hashes = {}

    # Save JSON artifacts
    json_artifacts = {
        "sources.json": factpack.sources,
        "factpack.json": factpack,
        "financials.json": financial_summary,
        "dcf_assumptions.json": valuation_output.assumptions,
        "dcf_results.json": valuation_output.results,
        "skeptic_report.json": skeptic_report,
    }

    for filename, data in json_artifacts.items():
        filepath = run_dir / filename
        with open(filepath, "w") as f:
            json.dump(
                data.model_dump() if hasattr(data, "model_dump") else data,
                f,
                indent=2,
                default=str,
            )
        artifacts[filename] = str(filepath)
        hashes[filename] = compute_file_hash(filepath)

    # Save memo
    memo_path = run_dir / "memo.md"
    with open(memo_path, "w") as f:
        f.write(memo)
    artifacts["memo.md"] = str(memo_path)
    hashes["memo.md"] = compute_file_hash(memo_path)

    # Excel file
    artifacts["dcf_excel"] = str(excel_path)
    hashes["dcf_excel"] = compute_file_hash(excel_path)

    # Create and save manifest
    manifest = RunManifest(
        run_id=run_context.run_id,
        ticker=run_context.ticker,
        sector=run_context.sector,
        horizon=run_context.horizon,
        risk=run_context.risk,
        focus=run_context.focus,
        terminal=run_context.terminal,
        created_at=run_context.created_at,
        completed_at=datetime.now(),
        artifacts=artifacts,
        artifact_hashes=hashes,
        quote_data=quote_data.model_dump() if quote_data else None,
    )

    manifest_path = run_dir / "run_manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest.model_dump(), f, indent=2, default=str)


def save_failed_run(run_context: RunContext, error_message: str) -> None:
    """
    Save a failed run manifest.

    Args:
        run_context: Run context
        error_message: Error message
    """
    from datetime import datetime
    from mcp_analyst.schemas.manifest import RunManifest

    run_dir = run_context.run_dir
    run_dir.mkdir(parents=True, exist_ok=True)

    manifest = RunManifest(
        run_id=run_context.run_id,
        ticker=run_context.ticker,
        sector=run_context.sector,
        horizon=run_context.horizon,
        risk=run_context.risk,
        focus=run_context.focus,
        terminal=run_context.terminal,
        created_at=run_context.created_at,
        completed_at=datetime.now(),
        artifacts={},
        artifact_hashes={},
        timings={},
    )

    manifest_path = run_dir / "run_manifest.json"
    manifest_dict = manifest.model_dump()
    manifest_dict["status"] = "failed"
    manifest_dict["failed_reason"] = error_message

    with open(manifest_path, "w") as f:
        json.dump(manifest_dict, f, indent=2, default=str)

