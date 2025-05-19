#!/bin/bash

# Script to run Final Answer Processor tests

set -e  # Exit on error

# Add parent directory to PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Running Final Answer Processor Tests for Phase 1 Enhancements...${NC}"

# Create logs directory if it doesn't exist
mkdir -p logs

# Run the FinalAnswerProcessor tests with verbose output
python -m unittest tests.test_final_answer_processor -v 2>&1 | tee logs/test_final_answer_processor.log

if [ ${PIPESTATUS[0]} -eq 0 ]; then
    echo -e "${GREEN}Final Answer Processor tests passed!${NC}"
    
    # Run specific enhanced tests
    echo -e "\n${YELLOW}Running specific Phase 1 enhancement tests...${NC}"
    python -m unittest tests.test_final_answer_processor.TestFinalAnswerProcessor.test_currency_formatting tests.test_final_answer_processor.TestFinalAnswerProcessor.test_enhanced_list_formatting tests.test_final_answer_processor.TestFinalAnswerProcessor.test_exact_match_enhancement -v 2>&1 | tee logs/test_phase1_enhancements.log
    
    if [ ${PIPESTATUS[0]} -eq 0 ]; then
        echo -e "${GREEN}Phase 1 enhancement tests passed!${NC}"
    else
        echo -e "${RED}Phase 1 enhancement tests failed!${NC}"
        exit 1
    fi
else
    echo -e "${RED}Final Answer Processor tests failed!${NC}"
    exit 1
fi

echo -e "\n${GREEN}All Final Answer Processor tests completed successfully!${NC}"
exit 0 