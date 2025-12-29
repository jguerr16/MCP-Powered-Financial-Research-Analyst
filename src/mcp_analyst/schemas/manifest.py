"""Run manifest schema."""

from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel


class RunManifest(BaseModel):
    """Manifest for a single analysis run."""

    run_id: str
    ticker: str
    sector: Optional[str] = None
    horizon: str
    risk: str
    focus: Optional[str] = None
    terminal: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    artifacts: Dict[str, str] = {}  # artifact_name -> file_path
    artifact_hashes: Dict[str, str] = {}  # artifact_name -> hash
    timings: Dict[str, float] = {}  # step_name -> seconds
    version: str = "0.1.0"

