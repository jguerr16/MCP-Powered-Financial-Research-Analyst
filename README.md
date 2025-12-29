# MCP-Powered Financial Research Analyst

A systems-heavy financial analysis tool that produces reproducible, auditable research reports with professional-grade Excel DCF models. Built with MCP (Model Context Protocol) agents, this tool automates the entire financial research workflow from data retrieval to valuation.

## 🎯 Overview

This project transforms raw financial data into comprehensive investment research reports. It fetches real financial data from SEC EDGAR, normalizes metrics, builds detailed DCF models, and exports analyst-quality Excel workbooks—all with full audit trails and reproducibility.

### Key Features

- **Real SEC Data Integration**: Fetches financial data directly from SEC XBRL companyfacts API
- **Professional DCF Models**: Generates analyst-style Excel workbooks with full operating forecasts
- **Reproducible Runs**: Every analysis produces a complete audit trail with hashed artifacts
- **Validation Gates**: Fails loudly when data is missing—no silent garbage outputs
- **Multi-Scenario Analysis**: Base/Bull/Bear cases with sensitivity tables
- **Comprehensive Documentation**: Research memos with citations and source attribution

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

The generated Excel file includes:

1. **Historical** - Historical financial data from SEC filings
2. **Inputs** - All model assumptions and drivers
3. **DCF** - Full operating forecast with:
   - Revenue projections
   - Cost structure (COGS, SG&A, D&A)
   - EBIT → NOPAT bridge
   - Add-backs (D&A, SBC)
   - Working capital changes
   - Capital expenditures
   - Unlevered free cash flow
   - Present values by year
   - Terminal value
   - Equity bridge to per-share value
4. **Cases** - Base/Bull/Bear scenario definitions
5. **WACC** - Weighted average cost of capital calculation
6. **Sensitivities** - 2D sensitivity table (WACC vs terminal growth)
7. **Summary** - Key valuation outputs

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
   NEWS_API_KEY=your_news_api_key  # Optional
   ```

**Note**: The `SEC_USER_AGENT` is required per SEC guidelines. Use your real name and email.

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

### Future Data Sources

- Earnings call transcripts (pluggable interface)
- News articles (pluggable interface)
- Market data (optional)

## 🔍 Quality & Validation

### Validation Gates

The pipeline includes hard validation at each stage:

1. **Retriever**: Must produce at least 1 source
2. **Financials**: Must have at least 3 periods, revenue series, and one of: operating income, CFO, or capex
3. **Valuation**: Must have non-empty growth rates, base revenue > 0, shares outstanding

If any validation fails, the run stops with a clear error message.

### Quality Metrics

- **Citation Coverage**: Percentage of claims backed by citations
- **Confidence Scores**: Agent confidence in outputs
- **Skeptic Flags**: Unsupported claims, conflicting evidence, outdated data

## 🧪 Testing

```bash
# Run tests
pytest

# Run specific test
pytest src/tests/test_schemas.py

# Run with coverage
pytest --cov=src/mcp_analyst
```

## 📚 Documentation

- **[Architecture](docs/architecture.md)**: System design and data flow
- **[Data Sources](docs/data_sources.md)**: SEC EDGAR, transcripts, news
- **[Evaluation](docs/evaluation.md)**: Quality metrics and consistency testing
- **[Demo](docs/demo.md)**: 60-second demo script

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
- Pydantic for excellent data validation
- openpyxl for Excel file generation

## 📧 Contact

For questions or issues, please open a GitHub issue.

---

**Built with ❤️ using MCP (Model Context Protocol)**
