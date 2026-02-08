#!/bin/bash
# BabbleFish startup script for Linux/Mac

echo "================================"
echo " BabbleFish Translation Service"
echo "================================"
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo
fi

# Activate virtual environment
source venv/bin/activate

# Install/upgrade dependencies
echo "Checking dependencies..."
pip install -r requirements.txt --quiet
echo

# Check if models are set up
if [ ! -d "models/nllb-ct2" ]; then
    echo
    echo "WARNING: NLLB model not found"
    echo "Run 'python setup_models.py' to download and convert models"
    echo
    echo "Starting anyway (NLLB translation will not be available)"
    sleep 3
fi

# Start the server
echo "Starting BabbleFish server..."
echo
echo "API will be available at: http://localhost:8000"
echo "API docs: http://localhost:8000/docs"
echo

python main.py
