#!/bin/bash

# Run unit tests for the Hugging Face Agent
# This script runs all unit tests in the tests directory

set -e  # Exit on error

# Add parent directory to PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Running unit tests for Hugging Face Agent...${NC}"

# Create logs directory if it doesn't exist
mkdir -p logs

# Run specific tests for components implemented in Phase 1
echo -e "\n${YELLOW}Running FinalAnswerProcessor tests...${NC}"
python -m unittest tests.test_final_answer_processor 2>&1 | tee logs/test_final_answer_processor.log
if [ ${PIPESTATUS[0]} -eq 0 ]; then
    echo -e "${GREEN}FinalAnswerProcessor tests passed!${NC}"
else
    echo -e "${RED}FinalAnswerProcessor tests failed!${NC}"
    exit 1
fi

echo -e "\n${YELLOW}Running PythonInterpreterTool tests...${NC}"
python -m unittest tests.test_python_interpreter 2>&1 | tee logs/test_python_interpreter.log
if [ ${PIPESTATUS[0]} -eq 0 ]; then
    echo -e "${GREEN}PythonInterpreterTool tests passed!${NC}"
else
    echo -e "${RED}PythonInterpreterTool tests failed!${NC}"
    exit 1
fi

# Run all unit tests
echo -e "\n${YELLOW}Running all unit tests...${NC}"
python -m unittest discover -s tests -p "test_*.py" 2>&1 | tee logs/test_all.log
if [ ${PIPESTATUS[0]} -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
else
    echo -e "${RED}Some tests failed!${NC}"
    exit 1
fi

echo -e "\n${GREEN}Unit testing completed successfully!${NC}"
exit 0 