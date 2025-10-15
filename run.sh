#!/bin/bash

# Team Formation System - Setup and Run Script

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "======================================================================="
echo "Team Formation System - Setup and Run"
echo "======================================================================="
echo ""

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
echo "Step 1: Installing dependencies..."
if pip3 list 2>/dev/null | grep -q pandas; then
    echo "  ✓ pandas already installed"
else
    echo "  Installing pandas..."
    pip3 install pandas 2>/dev/null || pip3 install --break-system-packages pandas
    if [ $? -eq 0 ]; then
        echo "  ✓ pandas installed successfully"
    else
        echo -e "${RED}✗ Failed to install pandas${NC}"
        exit 1
    fi
fi

echo ""
echo "======================================================================="
echo "Step 2: Running Validation Tests"
echo "======================================================================="
echo ""

# Run tests first
python3 team_formation.py --test cse403-preferences.csv

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Tests failed! Please fix issues before proceeding.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ All tests passed!${NC}"

echo ""
echo "======================================================================="
echo "Step 3: Running Team Formation"
echo "======================================================================="
echo ""

# Run the Python script
python3 team_formation.py cse403-preferences.csv out.csv

# Check if output was created
if [ ! -f out.csv ]; then
    echo -e "${RED}✗ Error: Output file 'out.csv' was not created${NC}"
    exit 1
fi

if [ ! -f report.txt ]; then
    echo -e "${YELLOW}⚠ Warning: Report file 'report.txt' was not created${NC}"
fi

echo ""
echo "======================================================================="
echo "COMPLETED SUCCESSFULLY"
echo "======================================================================="
echo ""
echo "Output files generated:"
if [ -f out.csv ]; then
    team_count=$(wc -l < out.csv)
    echo -e "  ${GREEN}✓${NC} out.csv (team assignments) - $team_count team(s)"
fi
if [ -f report.txt ]; then
    echo -e "  ${GREEN}✓${NC} report.txt (detailed summary)"
fi
if [ -f team_formation.log ]; then
    echo -e "  ${GREEN}✓${NC} team_formation.log (processing log)"
fi
echo ""
echo "To view results:"
echo "  cat out.csv           # View team assignments"
echo "  cat report.txt        # View detailed report"
echo "  cat team_formation.log # View processing log"
echo ""

