"""HTTP requests wrapper with retries, headers, and rate limiting."""

import time
from typing import Any, Dict, Optional

import requests

from mcp_analyst.config import Config


def http_get(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    max_retries: int = None,
) -> requests.Response:
    """
    Make HTTP GET request with retries and rate limiting.

    Args:
        url: URL to fetch
        headers: Optional headers
        max_retries: Maximum retry attempts (defaults to Config.MAX_RETRIES)

    Returns:
        Response object

    Raises:
        requests.RequestException: If request fails after retries
    """
    if max_retries is None:
        max_retries = Config.MAX_RETRIES

    default_headers = {
        "User-Agent": Config.SEC_USER_AGENT,
    }
    if headers:
        default_headers.update(headers)

    # Rate limiting
    time.sleep(Config.REQUEST_DELAY_SECONDS)

    for attempt in range(max_retries + 1):
        try:
            response = requests.get(
                url,
                headers=default_headers,
                timeout=Config.REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            if attempt == max_retries:
                raise
            time.sleep(2 ** attempt)  # Exponential backoff

    raise requests.RequestException("Request failed after retries")

