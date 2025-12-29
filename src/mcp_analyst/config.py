"""Configuration management."""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Application configuration."""

    # API Keys
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    SEC_USER_AGENT: str = os.getenv(
        "SEC_USER_AGENT", "MCP Analyst mcp-analyst@example.com"
    )
    NEWS_API_KEY: Optional[str] = os.getenv("NEWS_API_KEY")
    TRANSCRIPTS_API_KEY: Optional[str] = os.getenv("TRANSCRIPTS_API_KEY")

    # Paths
    DEFAULT_OUTPUT_DIR: Path = Path("runs")
    CACHE_DIR: Path = Path(".cache")

    # API Settings
    EDGAR_BASE_URL: str = "https://data.sec.gov"
    REQUEST_DELAY_SECONDS: float = 0.1  # Rate limiting
    REQUEST_TIMEOUT_SECONDS: int = 30
    MAX_RETRIES: int = 3

    # Analysis Defaults
    DEFAULT_HORIZON: str = "5y"
    DEFAULT_RISK: str = "moderate"
    DEFAULT_TERMINAL: str = "gordon"

    @classmethod
    def validate(cls) -> None:
        """Validate required configuration."""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required")
        if not cls.SEC_USER_AGENT:
            raise ValueError("SEC_USER_AGENT is required")

