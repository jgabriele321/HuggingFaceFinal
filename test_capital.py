#!/usr/bin/env python3
"""
Simple test script to verify our enhanced agent correctly answers the capital of France.
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
        logging.FileHandler(f"logs/capital_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("CapitalTest")

def main():
    """Run the test to verify the enhanced agent can correctly identify Paris as the capital of France."""
    logger.info("Starting capital test...")
    
    try:
        # Import the enhanced agent
        from src.enhanced_agent import EnhancedAgent
        
        # Create the agent
        agent = EnhancedAgent(verbose=True)
        logger.info("Successfully created enhanced agent")
        
        # Test question
        question = "What is the capital of France?"
        logger.info(f"Testing question: {question}")
        
        # Get answer
        answer = agent(question)
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