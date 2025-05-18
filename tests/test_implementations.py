#!/usr/bin/env python3
"""
Test script for SmolAgent implementations with OpenRouter and OpenAI APIs.
This script validates both implementations and demonstrates their usage.
"""

import os
import time
import logging
import sys
from argparse import ArgumentParser

# Add the parent directory to Python path to allow imports from src
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("SmolAgentTest")

def test_openrouter_agent():
    """Test the OpenRouter implementation."""
    try:
        from src.openrouter_agent import SmolAgent as OpenRouterAgent
        
        # Check if API key exists
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            logger.error("⚠️ OPENROUTER_API_KEY not found in environment variables")
            return False
            
        # Initialize agent
        logger.info("Initializing OpenRouter agent...")
        agent = OpenRouterAgent()
        
        # Test simple question
        logger.info("Testing simple question...")
        question = "What is 2 + 2?"
        start_time = time.time()
        response = agent(question)
        elapsed = time.time() - start_time
        
        logger.info(f"Response (in {elapsed:.2f}s): {response}")
        
        # Test code generation
        logger.info("Testing code generation...")
        code_question = "Write a Python function to calculate the Fibonacci sequence up to n terms."
        start_time = time.time()
        code_response = agent(code_question)
        elapsed = time.time() - start_time
        
        logger.info(f"Code Response (in {elapsed:.2f}s):\n{code_response}")
        
        return True
    except Exception as e:
        logger.error(f"Error testing OpenRouter agent: {str(e)}")
        return False

def test_openai_agent():
    """Test the OpenAI implementation."""
    try:
        from src.openai_agent import SmolAgent as OpenAIAgent
        
        # Check if API key exists
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            logger.error("⚠️ OPENAI_API_KEY not found in environment variables")
            return False
            
        # Initialize agent
        logger.info("Initializing OpenAI agent...")
        agent = OpenAIAgent()
        
        # Test simple question
        logger.info("Testing simple question...")
        question = "What is 2 + 2?"
        start_time = time.time()
        response = agent(question)
        elapsed = time.time() - start_time
        
        logger.info(f"Response (in {elapsed:.2f}s): {response}")
        
        # Test code generation
        logger.info("Testing code generation...")
        code_question = "Write a Python function to calculate the Fibonacci sequence up to n terms."
        start_time = time.time()
        code_response = agent(code_question)
        elapsed = time.time() - start_time
        
        logger.info(f"Code Response (in {elapsed:.2f}s):\n{code_response}")
        
        return True
    except Exception as e:
        logger.error(f"Error testing OpenAI agent: {str(e)}")
        return False

def main():
    """Main function to run tests."""
    parser = ArgumentParser(description="Test SmolAgent implementations")
    parser.add_argument("--openrouter", action="store_true", help="Test OpenRouter implementation")
    parser.add_argument("--openai", action="store_true", help="Test OpenAI implementation")
    parser.add_argument("--all", action="store_true", help="Test all implementations")
    
    args = parser.parse_args()
    
    # If no specific tests are requested, test all
    if not args.openrouter and not args.openai and not args.all:
        args.all = True
    
    # Run tests
    if args.openrouter or args.all:
        logger.info("=== Testing OpenRouter Implementation ===")
        if test_openrouter_agent():
            logger.info("✅ OpenRouter implementation test passed")
        else:
            logger.error("❌ OpenRouter implementation test failed")
        
    if args.openai or args.all:
        logger.info("=== Testing OpenAI Implementation ===")
        if test_openai_agent():
            logger.info("✅ OpenAI implementation test passed")
        else:
            logger.error("❌ OpenAI implementation test failed")

if __name__ == "__main__":
    main() 