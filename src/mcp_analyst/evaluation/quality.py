"""Quality evaluation metrics."""

from pathlib import Path
from typing import Dict

from mcp_analyst.schemas.manifest import RunManifest
from mcp_analyst.schemas.skeptic import SkepticReport


def evaluate_quality(run_dir: Path) -> Dict[str, any]:
    """
    Evaluate quality metrics for a run.

    Args:
        run_dir: Run directory path

    Returns:
        Quality metrics report
    """
    import json

    # Load manifest
    manifest_path = run_dir / "run_manifest.json"
    with open(manifest_path, "r") as f:
        manifest_data = json.load(f)
    manifest = RunManifest(**manifest_data)

    # Load skeptic report
    skeptic_path = run_dir / "skeptic_report.json"
    with open(skeptic_path, "r") as f:
        skeptic_data = json.load(f)
    skeptic_report = SkepticReport(**skeptic_data)

    # Calculate metrics
    citation_coverage = skeptic_report.citation_coverage
    confidence_score = skeptic_report.confidence_score
    flag_count = len(skeptic_report.flags)
    high_severity_flags = sum(
        1 for flag in skeptic_report.flags if flag.severity == "high"
    )

    return {
        "citation_coverage": citation_coverage,
        "confidence_score": confidence_score,
        "total_flags": flag_count,
        "high_severity_flags": high_severity_flags,
        "run_id": manifest.run_id,
        "ticker": manifest.ticker,
    }

