#!/usr/bin/env python3
"""
Direct test for final_answer_extractor to verify it extracts 'Paris' as the capital of France.
"""

import sys
import os
import logging
from datetime import datetime

# Add src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"logs/extractor_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("ExtractorTest")

def main():
    """Run the test to verify the final_answer_extractor can extract 'Paris'."""
    logger.info("Starting extractor test...")
    
    # Import the answer extractor
    from src.final_answer_extractor import extract_final_answer
    
    # Test question
    question = "What is the capital of France?"
    
    # Sample answer text from Wikipedia
    sample_answer = """
    Content from https://en.wikipedia.org/wiki/France:
    
    [...lots of content...]
    Capitaland largest cityParis48°51′N 2°21′E / 48.850°N 2.350°E / 48.850; 2.350
    [...]
    
    France,[IX] officially the French Republic,[X] is a country located primarily in Western Europe. 
    Its capital is Paris. The country has a rich history and culture.
    [...]
    """
    
    # Test the extractor
    extracted_answer = extract_final_answer(question, sample_answer)
    logger.info(f"Extracted answer: '{extracted_answer}'")
    
    # Check if "Paris" is in the answer
    if "Paris" in extracted_answer:
        logger.info("✅ TEST PASSED: The extractor correctly identified 'Paris' as the capital of France")
        return True
    else:
        logger.error("❌ TEST FAILED: The extractor did not extract 'Paris' as the capital of France")
        return False

if __name__ == "__main__":
    result = main()
    sys.exit(0 if result else 1) 