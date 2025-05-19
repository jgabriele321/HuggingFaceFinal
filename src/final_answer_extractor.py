#!/usr/bin/env python3
"""
Simplified Final Answer Extractor

This module provides a simpler and more reliable approach to extract final answers
without aggressive transformations that might lose the actual content.
"""

import re
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("final_answer_extractor")

def extract_final_answer(question: str, raw_answer: str) -> str:
    """
    Extract the final answer from the raw response.
    
    Args:
        question: The original question
        raw_answer: The raw response from the agent
        
    Returns:
        The extracted final answer
    """
    logger.info(f"Processing answer for question: {question[:100]}...")
    logger.debug(f"FULL QUESTION: {question}")
    logger.debug(f"RAW ANSWER: {raw_answer}")
    
    # If raw_answer is not a string (e.g., it's a number), convert it to string
    if not isinstance(raw_answer, str):
        return str(raw_answer)
    
    # If the answer contains an error message, return it
    if "error" in raw_answer.lower():
        return raw_answer
        
    # Try to find a final answer section
    final_answer_match = re.search(r"Final answer:?\s*(.*?)(?:\n|$)", raw_answer, re.IGNORECASE | re.MULTILINE)
    if final_answer_match:
        return final_answer_match.group(1).strip()
        
    # If no final answer section found, return the raw answer
    return raw_answer.strip()

# Backward compatibility function for existing code
def process_final_answer(question: str, verbose_answer: str) -> str:
    """Wrapper for backward compatibility"""
    return extract_final_answer(question, verbose_answer) 