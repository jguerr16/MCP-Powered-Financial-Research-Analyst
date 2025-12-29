#!/bin/bash
# Bootstrap development environment

set -e

echo "Bootstrapping MCP-Powered Financial Research Analyst development environment..."

# Create virtual environment
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install package in editable mode
echo "Installing package..."
pip install -e ".[dev]"

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo "Please edit .env with your API keys"
fi

# Create runs directory if it doesn't exist
mkdir -p runs

echo "Development environment ready!"
echo "To activate: source .venv/bin/activate"

