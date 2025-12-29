# Architecture

## Overview

MCP-Powered-Financial-Research-Analyst is a systems-heavy financial analysis tool that produces reproducible, auditable research reports with Excel DCF artifacts.

## Agent Graph

```
CLI Input (ticker, horizon, risk, focus)
    ↓
Orchestrator (Router + Pipeline)
    ↓
┌─────────────────────────────────────┐
│  Agent Pipeline                      │
│  ┌──────────┐  ┌──────────┐         │
│  │Retriever │→ │Financials│         │
│  └──────────┘  └──────────┘         │
│       ↓             ↓                │
│  ┌──────────┐  ┌──────────┐         │
│  │Valuation │→ │Skeptic   │         │
│  └──────────┘  └──────────┘         │
│       ↓             ↓                │
│  ┌──────────┐                       │
│  │Synthesizer│                      │
│  └──────────┘                       │
└─────────────────────────────────────┘
    ↓
Artifacts (JSON + Markdown + Excel)
```

## Data Flow

1. **Input**: Ticker, sector, time horizon, risk appetite, focus area
2. **Retrieval**: EDGAR filings, transcripts, news → `FactPack`
3. **Normalization**: Financial metrics → `FinancialSummary`
4. **Valuation**: Assumptions → DCF model → `ValuationOutput`
5. **Skepticism**: Flag unsupported claims → `SkepticReport`
6. **Synthesis**: All schemas → `memo.md` + executive summary
7. **Export**: DCF assumptions → Excel workbook

## Key Components

### Orchestrator
- **Router**: Routes tasks to appropriate agents/tools
- **Pipeline**: End-to-end execution coordinator
- **RunContext**: Manages run_id, timestamps, directories

### Agents
- **Retriever**: Fetches and structures source data
- **Financials**: Normalizes financial metrics
- **Valuation**: Produces DCF assumptions and results
- **Skeptic**: Validates claims against evidence
- **Synthesizer**: Generates final memo

### Tools
- **EDGAR**: SEC filings fetch + caching
- **Transcripts**: Earnings call transcripts (pluggable)
- **News**: News search (pluggable)
- **Pricing**: Market data (optional)

### Storage
- **Runs**: Creates run directories with timestamps
- **Artifacts**: Saves/loads JSON, markdown, Excel
- **Hashing**: Computes artifact hashes for reproducibility

## Reproducibility

Each run produces:
- `run_manifest.json`: Inputs, outputs, hashes, timings
- All intermediate schemas as JSON
- Deterministic Excel workbook
- Structured logs

Same inputs → same artifact set (modulo external data freshness).

