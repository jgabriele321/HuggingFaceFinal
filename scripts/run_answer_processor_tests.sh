#!/bin/bash

# Script to run the final answer processor tests

# Ensure we're in the project root directory
cd "$(dirname "$0")" || exit

# Create logs directory if it doesn't exist
mkdir -p logs

echo "Running final answer processor tests..."
python -m pytest tests/test_final_answer_processor.py -v

# Direct execution of test file as a fallback
if [ $? -ne 0 ]; then
    echo "Falling back to direct test execution..."
    python tests/test_final_answer_processor.py
fi

echo "Tests completed." 