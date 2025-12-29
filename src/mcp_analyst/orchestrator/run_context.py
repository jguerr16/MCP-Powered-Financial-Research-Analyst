"""Run context management."""

import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional


class RunContext:
    """Context for a single analysis run."""

    def __init__(
        self,
        run_id: str,
        ticker: str,
        sector: Optional[str],
        horizon: str,
        risk: str,
        focus: Optional[str],
        terminal: str,
        output_dir: Path,
        created_at: datetime,
    ):
        """Initialize run context."""
        self.run_id = run_id
        self.ticker = ticker
        self.sector = sector
        self.horizon = horizon
        self.risk = risk
        self.focus = focus
        self.terminal = terminal
        self.output_dir = output_dir
        self.created_at = created_at

    @property
    def run_dir(self) -> Path:
        """Get run directory path."""
        date_str = self.created_at.strftime("%Y-%m-%d")
        dir_name = f"{date_str}_{self.ticker}_{self.run_id[:8]}"
        return self.output_dir / dir_name

    @classmethod
    def create(
        cls,
        ticker: str,
        sector: Optional[str],
        horizon: str,
        risk: str,
        focus: Optional[str],
        terminal: str,
        output_dir: Path,
    ) -> "RunContext":
        """Create a new run context."""
        run_id = str(uuid.uuid4())
        created_at = datetime.now()

        return cls(
            run_id=run_id,
            ticker=ticker,
            sector=sector,
            horizon=horizon,
            risk=risk,
            focus=focus,
            terminal=terminal,
            output_dir=output_dir,
            created_at=created_at,
        )

