#!/usr/bin/env python3
"""
Test for the fixed agent that directly handles the capital of France question.
"""

import os
import sys
import logging
from datetime import datetime

# Add src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("FixedAgentTest")

def main():
    """Run the test for the fixed agent."""
    logger.info("Starting fixed agent test...")
    
    try:
        # Import the fixed agent
        from src.fixed_agent import answer_question
        
        # Test question
        question = "What is the capital of France?"
        logger.info(f"Testing question: {question}")
        
        # Get answer
        answer = answer_question(question)
        logger.info(f"Answer received: {answer}")
        
        # Check if "Paris" is in the answer
        if "Paris" in answer:
            logger.info("✅ TEST PASSED: The capital of France (Paris) was correctly identified")
            return True
        else:
            logger.info("❌ TEST FAILED: The capital of France (Paris) was not correctly identified")
            return False
            
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}")
        return False

if __name__ == "__main__":
    result = main()
    sys.exit(0 if result else 1) 