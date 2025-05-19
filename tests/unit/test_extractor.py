#!/usr/bin/env python3
"""
Test script for the final answer extractor
"""

import os
import sys
import logging

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_script")

# Import extractors
try:
    from src.final_answer_extractor import extract_final_answer as new_extract
    logger.info("Imported new extractor")
except ImportError:
    logger.error("Failed to import new extractor")
    sys.exit(1)

try:
    from src.final_answer_processor import FinalAnswerProcessor
    old_processor = FinalAnswerProcessor()
    logger.info("Imported old processor")
except ImportError:
    logger.error("Failed to import old processor")
    old_processor = None

# Test cases that were problematic before
test_cases = [
    {
        "question": "In the video https://www.youtube.com/watch?v=L1vXCYZAYYM, what is the highest number of bird species shown simultaneously?",
        "verbose_answer": "After watching the video, the highest number of bird species shown simultaneously appears to be 6, which occurs at the 1:32 mark where you can see a variety of songbirds at a feeder including cardinals, chickadees, and finches."
    },
    {
        "question": "Who nominated the only Featured Article on English Wikipedia about a dinosaur that was promoted in November 2006?",
        "verbose_answer": "After researching, I found that the only Featured Article on English Wikipedia about a dinosaur that was promoted in November 2006 was nominated by User:Firsfron."
    },
    {
        "question": "What country had the least number of athletes at the 1928 Summer Olympics?",
        "verbose_answer": "The country that had the least number of athletes at the 1928 Summer Olympics was Malta, with only 1 athlete participating."
    },
    {
        "question": "Who are the pitchers with the number before and after Taishō Tamai's number as of July 2023?",
        "verbose_answer": "As of July 2023, the pitchers with the numbers before and after Taishō Tamai's number are:\n\nPitcher before: Masahiro Tanaka (wearing #18)\nPitcher after: Takahide Ikeda (wearing #20)\n\nTaishō Tamai wears #19 for the Tohoku Rakuten Golden Eagles in Japan's NPB."
    }
]

def run_comparison():
    """Run and compare both extractors on test cases"""
    logger.info("=== Testing Answer Extractors ===")
    
    for i, case in enumerate(test_cases):
        logger.info(f"\nTest case {i+1}:")
        logger.info(f"Question: {case['question']}")
        logger.info(f"Verbose answer: {case['verbose_answer']}")
        
        # Get results from new extractor
        new_result = new_extract(case['question'], case['verbose_answer'])
        logger.info(f"NEW EXTRACTOR: {new_result}")
        
        # Get results from old processor if available
        if old_processor:
            old_result = old_processor.process_answer(case['question'], case['verbose_answer'])
            logger.info(f"OLD PROCESSOR: {old_result}")
            
            # Compare
            if new_result != old_result:
                logger.info(f"DIFFERENT RESULTS: New changes answer by {100 - (len(new_result) / len(old_result) * 100):.1f}%")
            else:
                logger.info("SAME RESULT")
                
        logger.info("-" * 50)

if __name__ == "__main__":
    run_comparison() 