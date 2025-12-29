#!/bin/bash
# One-liner demo command

set -e

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Run demo analysis
echo "Running demo analysis for UBER..."
mcp-analyst analyze UBER \
    --sector "Technology" \
    --horizon 5y \
    --risk "moderate" \
    --focus "revenue-growth" \
    --terminal gordon

echo "Demo complete! Check runs/ directory for results."

