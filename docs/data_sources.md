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

## News Sources

**Source**: Pluggable provider (e.g., NewsAPI, Alpha Vantage, etc.)

### Implementation
- Abstract interface for news providers
- v1: Stub implementation (returns sample data)
- Future: Real API integration

### Caveats
- News sentiment may be biased
- Coverage varies by company size
- Requires careful source attribution

## Market Data (Optional)

**Source**: Pluggable provider (e.g., Alpha Vantage, Yahoo Finance, etc.)

### Use Cases
- Current stock price
- Market capitalization
- Historical price data

### Caveats
- Real-time data may require paid APIs
- Free APIs often have rate limits
- Data quality varies by provider

## Data Quality Guidelines

1. **Always cite sources**: Every fact must have a `Citation`
2. **Timestamp data**: Record when data was fetched
3. **Cache responsibly**: Balance freshness vs. API limits
4. **Handle errors gracefully**: Missing data should not crash the pipeline

