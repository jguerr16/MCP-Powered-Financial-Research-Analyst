"""Smoke tests for end-to-end pipeline."""

import pytest
from pathlib import Path
import tempfile

from mcp_analyst.orchestrator.pipeline import Pipeline
from mcp_analyst.orchestrator.run_context import RunContext


@pytest.mark.skip(reason="Requires full implementation")
def test_pipeline_smoke():
    """Smoke test for full pipeline execution."""
    with tempfile.TemporaryDirectory() as tmpdir:
        run_context = RunContext.create(
            ticker="TEST",
            sector="Technology",
            horizon="5y",
            risk="moderate",
            focus="revenue-growth",
            terminal="gordon",
            output_dir=Path(tmpdir),
        )

        pipeline = Pipeline(run_context=run_context)
        # pipeline.execute()  # Uncomment when ready

        # Verify artifacts were created
        # assert (run_context.run_dir / "run_manifest.json").exists()
        # assert (run_context.run_dir / "memo.md").exists()

