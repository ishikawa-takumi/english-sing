#!/bin/bash
set -euo pipefail

# Only run on Claude Code remote (web) environment
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

# Session start hook for english-sing repository
# This script runs when a Claude Code session starts on the web

echo "Setting up english-sing environment..."

# Navigate to project directory
cd "$CLAUDE_PROJECT_DIR"

# Install dependencies if package.json exists (Node.js projects)
if [ -f "package.json" ]; then
  echo "Installing Node.js dependencies..."
  npm install
fi

# Install dependencies if requirements.txt exists (Python projects)
if [ -f "requirements.txt" ]; then
  echo "Installing Python dependencies..."
  pip install -r requirements.txt
fi

# Install dependencies if pyproject.toml exists (Python projects with Poetry/pip)
if [ -f "pyproject.toml" ]; then
  echo "Installing Python dependencies from pyproject.toml..."
  pip install -e .
fi

echo "Environment setup complete!"
