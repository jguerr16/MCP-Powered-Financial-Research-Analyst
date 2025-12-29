"""SEC EDGAR filings fetch and caching."""

import json
from typing import Dict, List, Optional

from mcp_analyst.config import Config
from mcp_analyst.schemas.sources import SourceItem
from mcp_analyst.tools.cache import get_cached, set_cached
from mcp_analyst.tools.http import http_get


def ticker_to_cik(ticker: str) -> Optional[str]:
    """
    Convert ticker symbol to CIK.

    Args:
        ticker: Stock ticker symbol

    Returns:
        CIK string (10 digits, zero-padded) or None
    """
    cache_key = f"ticker_cik_{ticker}"
    cached = get_cached(cache_key)
    if cached:
        return cached

    try:
        # SEC company tickers JSON endpoint
        url = "https://www.sec.gov/files/company_tickers.json"
        response = http_get(url)
        data = response.json()

        # SEC returns a dict where values are the company data
        # Structure: {0: {"cik_str": "0001318605", "ticker": "AAPL", "title": "Apple Inc."}, ...}
        for entry in data.values():
            if isinstance(entry, dict) and entry.get("ticker", "").upper() == ticker.upper():
                cik = str(entry.get("cik_str", ""))
                # Pad CIK to 10 digits
                cik = cik.zfill(10)
                set_cached(cache_key, cik)
                return cik

        return None
    except Exception as e:
        # Log error but don't fail
        return None


def fetch_companyfacts(ticker: str) -> Optional[Dict]:
    """
    Fetch SEC companyfacts JSON for a ticker.

    Args:
        ticker: Stock ticker symbol

    Returns:
        Companyfacts JSON data or None
    """
    cache_key = f"companyfacts_{ticker}"
    cached = get_cached(cache_key)
    if cached:
        return cached

    cik = ticker_to_cik(ticker)
    if not cik:
        return None

    try:
        url = f"{Config.EDGAR_BASE_URL}/api/xbrl/companyfacts/CIK{cik}.json"
        response = http_get(url)
        data = response.json()
        set_cached(cache_key, data)
        return data
    except Exception:
        return None


def extract_financial_metric(
    companyfacts: Dict, tag: str, unit: str = "USD"
) -> Optional[List[Dict]]:
    """
    Extract financial metric from companyfacts.

    Args:
        companyfacts: Companyfacts JSON data
        tag: XBRL tag (e.g., "Revenues", "OperatingIncomeLoss")
        unit: Unit filter (e.g., "USD", "shares")

    Returns:
        List of {end, val, accn, fy, fp} dicts or None
    """
    try:
        facts = companyfacts.get("facts", {})
        us_gaap = facts.get("us-gaap", {})
        tag_data = us_gaap.get(tag, {})

        # Get units
        units = tag_data.get("units", {})
        if unit not in units:
            # Try to find any unit
            if units:
                unit = list(units.keys())[0]
            else:
                return None

        # Get annual data (fp == "FY")
        annual_data = []
        for entry in units.get(unit, []):
            if entry.get("fp") == "FY" and entry.get("form") in ["10-K", "10-Q"]:
                annual_data.append(entry)

        # Sort by end date (most recent first)
        annual_data.sort(key=lambda x: x.get("end", ""), reverse=True)

        return annual_data[:10]  # Return last 10 years
    except Exception:
        return None


def fetch_filings(ticker: str) -> List[SourceItem]:
    """
    Fetch SEC filings for a ticker.

    Args:
        ticker: Stock ticker symbol

    Returns:
        List of source items (filings)
    """
    # Check cache first
    cache_key = f"edgar_filings_{ticker}"
    cached = get_cached(cache_key)
    if cached:
        return cached

    cik = ticker_to_cik(ticker)
    if not cik:
        return []

    try:
        # Fetch companyfacts as a source
        companyfacts = fetch_companyfacts(ticker)
        if companyfacts:
            entity_name = companyfacts.get("entityName", "")
            source = SourceItem(
                source_id=f"sec_companyfacts_{cik}",
                source_type="companyfacts",
                ticker=ticker,
                title=f"SEC Company Facts - {entity_name}",
                url=f"{Config.EDGAR_BASE_URL}/api/xbrl/companyfacts/CIK{cik}.json",
                metadata={"cik": cik, "entity_name": entity_name},
            )
            filings = [source]
        else:
            filings = []

        # Cache result
        set_cached(cache_key, filings)
        return filings
    except Exception:
        return []


def fetch_10k(ticker: str, year: int) -> str:
    """
    Fetch a specific 10-K filing.

    Args:
        ticker: Stock ticker symbol
        year: Filing year

    Returns:
        Filing content (text)
    """
    # TODO: Implement actual 10-K fetch
    return ""


def fetch_10q(ticker: str, year: int, quarter: int) -> str:
    """
    Fetch a specific 10-Q filing.

    Args:
        ticker: Stock ticker symbol
        year: Filing year
        quarter: Filing quarter (1-4)

    Returns:
        Filing content (text)
    """
    # TODO: Implement actual 10-Q fetch
    return ""

