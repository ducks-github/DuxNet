#!/bin/bash

# Exit on any error
set -e

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
REQUIRED_VERSION="3.8"

# Compare Python versions
if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "Error: Python 3.8+ is required. Current version: $PYTHON_VERSION"
    exit 1
fi

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip and setuptools
pip install --upgrade pip setuptools wheel

# Install the package in editable mode with development dependencies
pip install -e .[dev]

# Run tests to verify installation
echo "Running tests..."
pytest tests/

# Verify CLI is installed
echo "Verifying CLI installation..."
duxos-node-registry --help

echo "Dux OS Node Registry CLI installed successfully!"
echo "Activate the virtual environment with: source venv/bin/activate"
echo "Run the CLI with: duxos-node-registry" 