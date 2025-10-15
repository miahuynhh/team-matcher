#!/bin/bash

# Team Formation System - Setup and Run Script

set -e  # Exit on error

echo "=== Team Formation System Setup ==="

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 not found. Installing Python 3..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew &> /dev/null; then
            brew install python3
        else
            echo "Error: Homebrew not found. Please install Python 3 manually."
            exit 1
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        sudo apt-get update
        sudo apt-get install -y python3 python3-pip
    else
        echo "Error: Unsupported OS. Please install Python 3 manually."
        exit 1
    fi
else
    echo "Python 3 found: $(python3 --version)"
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "pip not found. Installing pip..."
    python3 -m ensurepip --upgrade
else
    echo "pip found: $(pip3 --version)"
fi

# Install pandas
echo "Installing pandas..."
pip3 install pandas 2>/dev/null || pip3 install --break-system-packages pandas

echo ""
echo "=== Running Team Formation System ==="
echo ""

# Run the Python script
python3 team_formation.py cse403-preferences.csv out.csv

echo ""
echo "=== Done ==="

