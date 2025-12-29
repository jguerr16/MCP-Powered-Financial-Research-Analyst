# MCP-Powered Financial Research Analyst

A systems-heavy financial analysis tool that produces reproducible, auditable research reports with professional-grade Excel DCF models. Built with MCP (Model Context Protocol) agents, this tool automates the entire financial research workflow from data retrieval to valuation.

**Version 3.0** - Now with real-time pricing, sentiment analysis, confidence labels, and IQVIA-style Excel formatting.

## 🎯 Overview

This project transforms raw financial data into comprehensive investment research reports. It fetches real financial data from SEC EDGAR, normalizes metrics, builds detailed DCF models, and exports analyst-quality Excel workbooks—all with full audit trails and reproducibility.

### Key Features

- **Real SEC Data Integration**: Fetches financial data directly from SEC XBRL companyfacts API
- **Real-Time Pricing**: Yahoo Finance integration with 10-minute caching for current stock prices, market cap, and beta
- **Professional DCF Models**: IQVIA-style Excel workbooks with full operating forecasts, section headers, and margin percentages
- **Confidence Labels**: HIGH/MED/LOW confidence indicators on all assumptions based on data provenance
- **Sentiment Analysis**: Material events with sentiment scoring using Event Registry (newsapi.ai)
- **Risk-Based Fade Schedules**: Sophisticated growth fade methods (linear/exp/piecewise) based on risk profile
- **Reproducible Runs**: Every analysis produces a complete audit trail with hashed artifacts
- **Validation Gates**: Fails loudly when data is missing—no silent garbage outputs
- **Multi-Scenario Analysis**: Base/Bull/Bear cases with sensitivity tables
- **Comprehensive Documentation**: Research memos with citations and source attribution
- **Formatting Tests**: Regression tests to prevent Excel formatting bugs

## 📊 What It Produces

Each analysis run generates a complete set of artifacts:

```
runs/2025-12-29_UBER_<run_id>/
├── run_manifest.json          # Run metadata, hashes, timings
├── sources.json               # All data sources with citations
├── factpack.json              # Structured facts extracted
├── financials.json            # Normalized financial metrics
├── dcf_assumptions.json       # DCF model assumptions
├── dcf_results.json            # Valuation results
├── skeptic_report.json        # Quality flags and validation
├── memo.md                    # Research memo (markdown)
├── DCF_UBER_2025-12-29.xlsx  # Professional Excel DCF model
└── logs/
    └── pipeline.log           # Execution log
```

### Excel Workbook Structure

The generated Excel file includes (IQVIA-style formatting):

1. **Historical** - Historical financial data from SEC filings with proper formatting
2. **Inputs** - All model assumptions and drivers with **confidence labels** (HIGH/MED/LOW) and color coding
3. **DCF** - Full operating forecast with IQVIA-style structure:
   - **Overview Block**: Company info, current share price, fair value, upside/downside
   - **Operating Build Section**:
     - Revenue projections
     - Gross Margin % and EBIT Margin % rows
     - Cost structure (COGS, SG&A, D&A)
     - EBIT → NOPAT bridge
   - **Cash Flow Adjustments Section**:
     - Add-backs (D&A, SBC)
     - Working capital changes
     - Capital expenditures
   - **Valuation Section**:
     - Unlevered free cash flow
     - Discount factors (properly formatted as decimals)
     - Present values by year
     - Terminal value (separate row)
     - PV of terminal value
     - Enterprise value bridge
     - Equity value and per-share value
4. **Cases** - Base/Bull/Bear scenario definitions
5. **WACC** - Weighted average cost of capital calculation
6. **Sensitivities** - 2D sensitivity table (WACC vs terminal growth)
7. **ValSum** - Valuation summary sheet with:
   - Key valuation outputs
   - Price comparison (current vs fair value with implied upside/downside)
   - Valuation range (Bull/Base/Bear)
   - Key assumptions summary
   - **Material Events** section with top 5 events, sentiment labels, and categories
   - Last updated timestamp

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- API keys (see Configuration)

### Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd MCP-Powered-Financial-Research-Analyst

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Or use the bootstrap script
./scripts/bootstrap_dev.sh
```

### Configuration

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Add your API keys to `.env`:
   ```env
   OPENAI_API_KEY=your_openai_key_here
   SEC_USER_AGENT="Your Name your_email@domain.com"
   NEWS_API_KEY=your_event_registry_key  # Optional - for Event Registry (newsapi.ai)
   ```

**Note**: 
- The `SEC_USER_AGENT` is required per SEC guidelines. Use your real name and email.
- `NEWS_API_KEY` should be your Event Registry API key from [newsapi.ai](https://newsapi.ai/dashboard). See [NEWSAPI_SETUP.md](NEWSAPI_SETUP.md) for setup instructions.

### Running an Analysis

```bash
# Basic analysis
mcp-analyst analyze UBER --horizon 5y --risk moderate

# Full options
mcp-analyst analyze UBER \
  --sector "Technology" \
  --horizon 5y \
  --risk "moderate" \
  --focus "revenue-growth" \
  --terminal gordon \
  --output-dir runs/
```

### Viewing Results

```bash
# List recent runs
ls -lt runs/

# View memo
cat runs/2025-12-29_UBER_*/memo.md

# Open Excel file
open runs/2025-12-29_UBER_*/DCF_UBER_*.xlsx

# Check manifest
cat runs/2025-12-29_UBER_*/run_manifest.json | jq
```

## 🏗️ Architecture

### System Design

The tool follows a **systems-heavy** approach with:

- **Schema-First**: All data structures defined with Pydantic models
- **Reproducible Runs**: Same inputs → same artifact set (modulo external data freshness)
- **Audit Trail**: Every run produces a manifest with hashes and timings
- **Validation Gates**: Pipeline fails loudly if data is missing or invalid

### Agent Pipeline

```
CLI Input (ticker, horizon, risk, focus)
    ↓
Orchestrator (Pipeline)
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

### Key Components

#### Agents
- **Retriever**: Fetches data from SEC EDGAR, transcripts, news
- **Financials**: Normalizes financial metrics from XBRL data
- **Valuation**: Builds full operating forecast and DCF model
- **Skeptic**: Validates claims against evidence
- **Synthesizer**: Generates research memo

#### Tools
- **EDGAR**: SEC XBRL companyfacts API integration
- **Cache**: Disk-based caching for API responses
- **HTTP**: Retry logic, rate limiting, proper headers

#### Storage
- **Runs**: Creates timestamped run directories
- **Artifacts**: Saves/loads JSON, markdown, Excel
- **Hashing**: Computes SHA-256 hashes for reproducibility

## 📈 Data Sources

### SEC EDGAR (Primary)

- **Source**: SEC XBRL companyfacts API
- **Data Extracted**:
  - Revenue
  - Operating Income
  - Net Income
  - Capital Expenditures
  - Cash Flow from Operations
  - Shares Outstanding
  - Debt and Cash
- **Caching**: Disk-based cache to minimize API calls
- **Rate Limiting**: Respectful delays between requests

### Event Registry (News & Sentiment)

- **Source**: Event Registry API (newsapi.ai)
- **Data Extracted**:
  - Recent news articles (30-90 days)
  - Material events (M&A, litigation, guidance, macro)
  - Sentiment scores (built-in from Event Registry)
  - Materiality scoring based on recency, category, and keywords
- **Integration**: Top 5 material events displayed in ValSum sheet with sentiment colors

### Yahoo Finance (Real-Time Pricing)

- **Source**: Yahoo Finance via `yfinance` library
- **Data Extracted**:
  - Current stock price
  - Market capitalization
  - Beta
  - Shares outstanding
  - Currency
- **Caching**: 10-minute TTL to avoid rate limits
- **Integration**: Displayed in Overview block and ValSum sheet

### Future Data Sources

- Earnings call transcripts (pluggable interface)

## 🔍 Quality & Validation

### Validation Gates

The pipeline includes hard validation at each stage:

1. **Retriever**: Must produce at least 1 source
2. **Financials**: Must have at least 3 periods, revenue series, and one of: operating income, CFO, or capex
3. **Valuation**: Must have non-empty growth rates, base revenue > 0, shares outstanding

If any validation fails, the run stops with a clear error message.

### Quality Metrics

- **Citation Coverage**: Percentage of claims backed by citations
- **Confidence Scores**: Agent confidence in outputs (HIGH/MED/LOW labels on assumptions)
- **Skeptic Flags**: Unsupported claims, conflicting evidence, outdated data
- **Data Provenance**: Confidence levels assigned based on data source:
  - **HIGH**: Directly from SEC XBRL filings
  - **MED**: Computed from historical SEC data
  - **LOW**: Fallback heuristics or estimates

## 🧪 Testing

```bash
# Run all tests
pytest

# Run specific test
pytest src/tests/test_schemas.py

# Run formatting regression tests (v3)
pytest src/tests/test_excel_formatting.py -v

# Run with coverage
pytest --cov=src/mcp_analyst
```

### Formatting Regression Tests

The test suite includes 9 regression tests to prevent Excel formatting bugs:
- Discount factor formatting (not currency)
- Shares outstanding formatting (not currency)
- Currency rows have proper formatting
- ValSum sheet exists
- Current price cell is numeric
- Confidence labels appear in Inputs
- Overview block exists in DCF
- Fade method displayed
- Column letters work past Z

## 📚 Documentation

- **[Architecture](docs/architecture.md)**: System design and data flow
- **[Data Sources](docs/data_sources.md)**: SEC EDGAR, transcripts, news
- **[Evaluation](docs/evaluation.md)**: Quality metrics and consistency testing
- **[Demo](docs/demo.md)**: 60-second demo script
- **[NewsAPI Setup](NEWSAPI_SETUP.md)**: Event Registry (newsapi.ai) configuration guide

## 🆕 Version 3.0 Features

### Real-Time Pricing Integration
- Yahoo Finance integration for current stock prices, market cap, and beta
- 10-minute caching to minimize API calls
- Displayed in Overview block and ValSum sheet

### Confidence Labels
- Every assumption tagged with HIGH/MED/LOW confidence
- Color-coded in Excel (green/yellow/red)
- Based on data provenance (SEC XBRL = HIGH, computed = MED, heuristic = LOW)

### Sentiment Analysis & Material Events
- Event Registry integration for news articles
- Sentiment scoring (positive/negative/neutral)
- Materiality scoring based on recency, category, and keywords
- Top 5 material events displayed in ValSum with sentiment colors

### Risk-Based Fade Schedules
- **Linear fade**: Conservative risk profile
- **Exponential fade**: Aggressive risk profile (slower initial decay)
- **Piecewise fade**: Moderate risk profile (fast fade years 1-2, slower thereafter)
- Fade method displayed in Inputs sheet

### IQVIA-Style Excel Formatting
- Professional section headers with dark fills
- Overview/Share Price Calculation block at top of DCF sheet
- Dedicated ValSum sheet (replaces Summary)
- Proper number formatting (currency, percent, decimal, per-share)
- Dynamic freeze panes
- Consistent fonts, borders, and column widths

### Formatting Regression Tests
- 9 comprehensive tests to prevent formatting bugs
- Validates number formats, sheet structure, and data types

## 🛠️ Development

### Project Structure

```
MCP-Powered-Financial-Research-Analyst/
├── src/mcp_analyst/
│   ├── agents/          # Analysis agents
│   ├── tools/          # Data retrieval tools
│   ├── schemas/        # Pydantic data models
│   ├── orchestrator/    # Pipeline coordination
│   ├── exports/         # Excel, PDF export
│   ├── storage/         # Run management
│   └── evaluation/     # Quality metrics
├── tests/              # Test suite
├── docs/               # Documentation
├── examples/            # Sample artifacts
└── runs/               # Analysis outputs (gitignored)
```

### Adding New Data Sources

1. Create a new tool in `src/mcp_analyst/tools/`
2. Implement the fetch function
3. Update `RetrieverAgent` to call it
4. Add validation if needed

### Extending the DCF Model

1. Update `DcfAssumptions` schema in `schemas/valuation.py`
2. Modify `ValuationAgent` to compute new assumptions
3. Update Excel export in `exports/excel_dcf.py`

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 🙏 Acknowledgments

- SEC EDGAR for providing free access to financial data
- Event Registry (newsapi.ai) for news and sentiment data
- Yahoo Finance for real-time stock pricing
- Pydantic for excellent data validation
- openpyxl for Excel file generation
- VADER Sentiment for sentiment analysis fallback

## 📧 Contact

For questions or issues, please open a GitHub issue.

---

**Built with ❤️ using MCP (Model Context Protocol)**
