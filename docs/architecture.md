# Architecture

## Overview

MCP-Powered-Financial-Research-Analyst is a systems-heavy financial analysis tool that produces reproducible, auditable research reports with Excel DCF artifacts.

## Agent Graph (v3)

```
CLI Input (ticker, horizon, risk, focus)
    ↓
Orchestrator (Router + Pipeline)
    ↓
┌─────────────────────────────────────┐
│  Agent Pipeline                      │
│  ┌──────────┐  ┌──────────┐         │
│  │Retriever │→ │Financials│         │
│  │  + News  │  └──────────┘         │
│  │  Analyst│       ↓                │
│  └──────────┘  ┌──────────┐         │
│       ↓        │ Pricing  │         │
│  ┌──────────┐  │  Tool    │         │
│  │Valuation │  └──────────┘         │
│  │  + Fade │       ↓                │
│  │ Schedules│  ┌──────────┐         │
│  └──────────┘→ │Skeptic   │         │
│       ↓        └──────────┘         │
│  ┌──────────┐       ↓                │
│  │Synthesizer│  ┌──────────┐         │
│  └──────────┘  │  Excel   │         │
│                │  Export  │         │
│                └──────────┘         │
└─────────────────────────────────────┘
    ↓
Artifacts (JSON + Markdown + Excel)
```

## Data Flow (v3)

1. **Input**: Ticker, sector, time horizon, risk appetite, focus area
2. **Pricing**: Fetch current stock price, market cap, beta from Yahoo Finance (cached 10 min)
3. **Retrieval**: EDGAR filings, transcripts, news → `FactPack`
4. **News Analysis**: Material events extraction with sentiment scoring → `FactPack` (material events)
5. **Normalization**: Financial metrics → `FinancialSummary`
6. **Valuation**: Assumptions + fade schedules → DCF model → `ValuationOutput` (with confidence labels)
7. **Skepticism**: Flag unsupported claims → `SkepticReport`
8. **Synthesis**: All schemas → `memo.md` + executive summary
9. **Export**: DCF assumptions + quote data + factpack → IQVIA-style Excel workbook

## Key Components

### Orchestrator
- **Router**: Routes tasks to appropriate agents/tools
- **Pipeline**: End-to-end execution coordinator
- **RunContext**: Manages run_id, timestamps, directories

### Agents
- **Retriever**: Fetches and structures source data (EDGAR, transcripts, news)
- **NewsAnalyst**: Analyzes news articles for material events, sentiment, and materiality (v3)
- **Financials**: Normalizes financial metrics from SEC XBRL
- **Valuation**: Produces DCF assumptions and results with confidence labels and fade schedules (v3)
- **Skeptic**: Validates claims against evidence
- **Synthesizer**: Generates final memo

### Tools
- **EDGAR**: SEC filings fetch + caching
- **News (Event Registry)**: News search with sentiment analysis (v3) - uses Event Registry API
- **Pricing (Yahoo Finance)**: Real-time stock price, market cap, beta (v3) - uses `yfinance` with 10-min caching
- **Transcripts**: Earnings call transcripts (pluggable, stub in v1)

### Valuation Components (v3)
- **Fade Schedules**: Risk-based growth fade methods (linear/exp/piecewise)
- **Confidence Labels**: HIGH/MED/LOW confidence on assumptions based on data provenance
- **Operating Forecast**: Full 3-statement build with margin percentages

### Storage
- **Runs**: Creates run directories with timestamps
- **Artifacts**: Saves/loads JSON, markdown, Excel
- **Hashing**: Computes artifact hashes for reproducibility

## Reproducibility

Each run produces:
- `run_manifest.json`: Inputs, outputs, hashes, timings, quote data
- All intermediate schemas as JSON (factpack, financials, valuation, etc.)
- Deterministic Excel workbook (IQVIA-style formatting)
- Structured logs

Same inputs → same artifact set (modulo external data freshness).

## v3 Enhancements

### Real-Time Pricing
- Yahoo Finance integration via `yfinance`
- 10-minute disk cache to avoid rate limits
- Stored in `run_manifest.json` and `valuation_output`
- Used for price comparison in Excel

### Sentiment Analysis
- Event Registry API for news articles
- Built-in sentiment scores from Event Registry
- VADER Sentiment fallback if Event Registry unavailable
- Material events categorized and scored

### Confidence Labels
- Every assumption tagged with confidence level
- Based on data source: SEC XBRL (HIGH), computed (MED), heuristic (LOW)
- Displayed in Excel Inputs sheet with color coding

### Fade Schedules
- Risk profile determines fade method:
  - **Conservative**: Linear fade
  - **Moderate**: Piecewise fade (fast years 1-2, slower thereafter)
  - **Aggressive**: Exponential fade (slower initial decay)
- Fade method recorded in assumptions

### Excel Formatting
- IQVIA-style professional formatting
- Overview block with price comparison
- Dedicated ValSum sheet
- Section headers and proper number formats
- Regression tests to prevent formatting bugs

