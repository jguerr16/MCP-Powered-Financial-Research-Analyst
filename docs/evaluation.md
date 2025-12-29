# Evaluation Framework

## Reliability Metrics

### Citation Coverage
- **Definition**: Percentage of claims backed by citations
- **Target**: >80% of factual claims should have citations
- **Measurement**: Count claims vs. citations in `SkepticReport`

### Consistency
- **Definition**: Variance in valuation outputs across multiple runs
- **Target**: <5% coefficient of variation for key metrics (e.g., fair value)
- **Measurement**: Run pipeline N times (e.g., 10) with same inputs, compare outputs

### Confidence Scores
- **Definition**: Agent confidence in its outputs
- **Target**: High confidence (>0.8) for well-supported claims
- **Measurement**: Track confidence scores in schemas

## Quality Checks

### Skeptic Flags
- **Unsupported Claims**: Claims without citations
- **Conflicting Evidence**: Multiple sources contradicting
- **Outdated Data**: Data older than threshold (e.g., 1 year)
- **Low Confidence**: Agent confidence below threshold

### Schema Validation
- All JSON artifacts must validate against Pydantic schemas
- Required fields must be present
- Data types must match schema definitions

### Excel Workbook Validation
- Required tabs exist
- Required cells populated
- Formulas calculate correctly
- Formatting consistent

## Evaluation Workflow

1. **Run Consistency Test**: Execute pipeline N times with same inputs
2. **Compare Artifacts**: Use `storage/hashing.py` to detect differences
3. **Generate Report**: Summarize variance, citation coverage, skeptic flags
4. **Track Over Time**: Monitor metrics across versions

## Sample Evaluation Command

```bash
# Run consistency test
python -m mcp_analyst.evaluation.consistency --ticker UBER --runs 10

# Generate quality report
python -m mcp_analyst.evaluation.quality --run-dir runs/2025-12-29_UBER_abc123
```

