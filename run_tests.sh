#!/bin/bash

# Run Tests Script
# This script runs all tests for the SmolAgent implementations

echo "Running tests for SmolAgent implementations..."
echo ""

# Check if Python environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "No virtual environment detected."
    if [ -d "venv" ]; then
        echo "Activating virtual environment from ./venv"
        source venv/bin/activate || source venv/Scripts/activate
    fi
fi

# Check required environment variables
echo "Checking environment variables..."
if [ -z "$OPENROUTER_API_KEY" ] && [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️ Warning: Neither OPENROUTER_API_KEY nor OPENAI_API_KEY is set."
    echo "Some tests may fail. Consider setting these in your .env file."
    echo ""
fi

# Run implementation tests
echo "Running implementation tests..."
python tests/test_implementations.py "$@"

# Run model tests
echo ""
echo "Running model availability tests..."
python tests/test_model.py "$@"

echo ""
echo "All tests completed." 