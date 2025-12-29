# Demo Script

## 60-Second Demo

### Setup (One-time)
```bash
# Clone and setup
git clone <repo>
cd MCP-Powered-Financial-Research-Analyst
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

### Run Analysis
```bash
# Basic analysis
mcp-analyst analyze UBER --horizon 5y --terminal gordon

# With all options
mcp-analyst analyze UBER \
  --sector "Technology" \
  --horizon 5y \
  --risk "moderate" \
  --focus "revenue-growth" \
  --output-dir runs/
```

### Inspect Results
```bash
# View run directory
ls -la runs/2025-12-29_UBER_<run_id>/

# Read memo
cat runs/2025-12-29_UBER_<run_id>/memo.md

# Open Excel file
open runs/2025-12-29_UBER_<run_id>/DCF_UBER_2025-12-29.xlsx

# Check manifest
cat runs/2025-12-29_UBER_<run_id>/run_manifest.json | jq
```

## Sample Commands

### Quick Analysis
```bash
mcp-analyst analyze TSLA --horizon 10y
```

### Full Analysis with Custom Output
```bash
mcp-analyst analyze AAPL \
  --sector "Consumer Technology" \
  --horizon 5y \
  --risk "conservative" \
  --focus "profitability" \
  --output-dir ./my_analysis/
```

### View Help
```bash
mcp-analyst analyze --help
```

## Expected Outputs

After running, you should see:
- ✅ `run_manifest.json`: Run metadata
- ✅ `sources.json`: All data sources with citations
- ✅ `factpack.json`: Structured facts extracted
- ✅ `financials.json`: Normalized financial metrics
- ✅ `dcf_assumptions.json`: DCF model assumptions
- ✅ `dcf_results.json`: DCF calculation results
- ✅ `skeptic_report.json`: Quality flags
- ✅ `memo.md`: Research memo
- ✅ `DCF_<TICKER>_<DATE>.xlsx`: Excel workbook
- ✅ `logs/pipeline.log`: Execution log

