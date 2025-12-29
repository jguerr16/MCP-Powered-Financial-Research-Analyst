"""Request cache (disk-based)."""

import hashlib
import json
from pathlib import Path
from typing import Any, Optional

from mcp_analyst.config import Config


def _get_cache_path(key: str) -> Path:
    """Get cache file path for a key."""
    Config.CACHE_DIR.mkdir(parents=True, exist_ok=True)
    key_hash = hashlib.md5(key.encode()).hexdigest()
    return Config.CACHE_DIR / f"{key_hash}.json"


def get_cached(key: str) -> Optional[Any]:
    """
    Get cached value.

    Args:
        key: Cache key

    Returns:
        Cached value or None if not found
    """
    cache_path = _get_cache_path(key)
    if not cache_path.exists():
        return None

    try:
        with open(cache_path, "r") as f:
            return json.load(f)
    except Exception:
        return None


def set_cached(key: str, value: Any) -> None:
    """
    Set cached value.

    Args:
        key: Cache key
        value: Value to cache (must be JSON-serializable)
    """
    cache_path = _get_cache_path(key)
    try:
        with open(cache_path, "w") as f:
            json.dump(value, f, indent=2)
    except Exception:
        pass  # Fail silently on cache write errors

