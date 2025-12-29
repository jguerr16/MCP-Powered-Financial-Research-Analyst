"""Run directory management."""

from pathlib import Path

from mcp_analyst.orchestrator.run_context import RunContext


def create_run_directory(run_context: RunContext) -> Path:
    """
    Create run directory structure.

    Args:
        run_context: Run context

    Returns:
        Path to created run directory
    """
    run_dir = run_context.run_dir
    run_dir.mkdir(parents=True, exist_ok=True)

    # Create logs subdirectory
    (run_dir / "logs").mkdir(exist_ok=True)

    return run_dir

