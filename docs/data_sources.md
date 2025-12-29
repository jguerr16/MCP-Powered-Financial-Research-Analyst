# Data Sources

## SEC EDGAR

**Primary Source**: SEC EDGAR database for company filings

### Supported Filings
- 10-K (Annual reports)
- 10-Q (Quarterly reports)
- 8-K (Current reports)
- Proxy statements (DEF 14A)

### Access
- **API**: SEC EDGAR REST API (free, no auth required)
- **User Agent**: Required per SEC guidelines
- **Rate Limiting**: Respectful delays between requests
- **Caching**: Disk-based cache to minimize API calls

### Caveats
- EDGAR data may have delays (typically 1-2 days after filing)
- Historical filings may have formatting inconsistencies
- Some companies file in non-standard formats

## Earnings Call Transcripts

**Source**: Pluggable provider (e.g., Seeking Alpha, AlphaSense, etc.)

### Implementation
- Abstract interface for transcript providers
- v1: Stub implementation (returns sample data)
- Future: Real API integration

### Caveats
- Transcript quality varies by provider
- Not all companies have transcripts available
- Timing may lag earnings releases

## Event Registry (News & Sentiment) - v3

**Source**: Event Registry API (newsapi.ai)

### Implementation
- **Status**: ✅ Fully implemented in v3
- **Package**: `eventregistry` Python library
- **API Key**: Required (set `NEWS_API_KEY` in `.env`)
- **Setup**: See [NEWSAPI_SETUP.md](../NEWSAPI_SETUP.md)

### Features
- Fetches recent news articles (30-90 days)
- Built-in sentiment scoring from Event Registry
- Material events categorization (M&A, litigation, guidance, macro)
- Materiality scoring based on recency, category, and keywords
- Top 5 material events displayed in ValSum sheet

### Data Extracted
- Article title, URL, date, source
- Sentiment score (-1 to 1)
- Sentiment label (positive/negative/neutral)
- Materiality score (0 to 1)
- Category (material_event_m_and_a, material_event_litigation, etc.)

### Caveats
- News sentiment may be biased
- Coverage varies by company size
- Requires Event Registry API key
- Falls back to VADER Sentiment if Event Registry sentiment unavailable

## Yahoo Finance (Real-Time Pricing) - v3

**Source**: Yahoo Finance via `yfinance` library

### Implementation
- **Status**: ✅ Fully implemented in v3
- **Package**: `yfinance` Python library
- **API Key**: Not required (free public API)
- **Caching**: 10-minute TTL to avoid rate limits

### Features
- Real-time stock price
- Market capitalization
- Beta (if available)
- Shares outstanding
- Currency
- Timestamp of data fetch

### Data Extracted
- Current stock price
- Market cap
- Beta
- Shares outstanding
- Currency code
- Data timestamp

### Integration
- Displayed in DCF Overview block
- Displayed in ValSum sheet with price comparison
- Stored in `run_manifest.json` and `valuation_output`
- Used for upside/downside calculations

### Caveats
- Free API may have rate limits (mitigated by caching)
- Data may lag real-time by a few minutes
- Some tickers may not have complete data
- Beta may not be available for all companies

## Data Quality Guidelines

1. **Always cite sources**: Every fact must have a `Citation`
2. **Timestamp data**: Record when data was fetched
3. **Cache responsibly**: Balance freshness vs. API limits
4. **Handle errors gracefully**: Missing data should not crash the pipeline

