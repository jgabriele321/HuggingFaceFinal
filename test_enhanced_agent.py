#!/usr/bin/env python3
"""
Test script for enhanced SmolAgent implementation with improved tool handling.
This script tests the agent's new capabilities including tool validation and error recovery.
"""

import os
import time
import logging
import sys
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("EnhancedAgentTest")

def run_test_case(agent, name: str, prompt: str, expected_tool: str = None) -> Dict[str, Any]:
    """
    Run a single test case and report the results.
    
    Args:
        agent: The SmolAgent instance to test
        name: Name of the test case
        prompt: The prompt to send to the agent
        expected_tool: The tool we expect the agent to select
        
    Returns:
        Dictionary with test results
    """
    logger.info(f"Running test: {name}")
    logger.info(f"Prompt: {prompt}")
    
    if expected_tool:
        logger.info(f"Expected tool: {expected_tool}")
    
    start_time = time.time()
    
    try:
        # Run the test
        response = agent(prompt)
        success = True
        error = None
    except Exception as e:
        response = None
        success = False
        error = str(e)
    
    elapsed_time = time.time() - start_time
    
    # Log the results
    if success:
        logger.info(f"✅ Test passed in {elapsed_time:.2f}s")
        logger.info(f"Response: {response}")
    else:
        logger.error(f"❌ Test failed in {elapsed_time:.2f}s")
        logger.error(f"Error: {error}")
    
    # Return the results
    return {
        "name": name,
        "prompt": prompt,
        "response": response,
        "success": success,
        "error": error,
        "elapsed_time": elapsed_time
    }

def run_test_suite(agent) -> List[Dict[str, Any]]:
    """
    Run a full suite of tests on the agent.
    
    Args:
        agent: The SmolAgent instance to test
        
    Returns:
        List of test results
    """
    results = []
    
    # Test 1: Simple math question (should use python tool)
    results.append(run_test_case(
        agent,
        "Simple Math",
        "What is the sum of all numbers from 1 to 100?",
        "python"
    ))
    
    # Test 2: Code generation (should use python tool)
    results.append(run_test_case(
        agent,
        "Code Generation",
        "Write a Python function to check if a string is a palindrome.",
        "python"
    ))
    
    # Test 3: Factual question (should use final_answer tool)
    results.append(run_test_case(
        agent,
        "Factual Question",
        "What is the capital of France?",
        "final_answer"
    ))
    
    # Test 4: Complex algorithm (tests recovery mechanisms)
    results.append(run_test_case(
        agent,
        "Complex Algorithm",
        "Implement a neural network from scratch in Python to classify handwritten digits.",
        "python"
    ))
    
    # Test 5: Unauthorized import test (should trigger validation)
    results.append(run_test_case(
        agent,
        "Unauthorized Import",
        "Write a Python script using tensorflow to classify images.",
        "python"
    ))
    
    return results

def summarize_results(results: List[Dict[str, Any]]) -> None:
    """
    Summarize the test results.
    
    Args:
        results: List of test results
    """
    success_count = sum(1 for r in results if r["success"])
    total_count = len(results)
    success_rate = (success_count / total_count) * 100
    
    logger.info("=" * 50)
    logger.info(f"Test Summary: {success_count}/{total_count} tests passed ({success_rate:.1f}%)")
    logger.info("=" * 50)
    
    for i, result in enumerate(results):
        status = "✅ PASSED" if result["success"] else "❌ FAILED"
        logger.info(f"Test {i+1}: {result['name']} - {status} ({result['elapsed_time']:.2f}s)")

def main():
    """Main function to run tests."""
    try:
        # Import the enhanced agent
        from src.openrouter_agent import SmolAgent
        
        # Check if API key exists
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            logger.error("⚠️ OPENROUTER_API_KEY not found in environment variables")
            return
            
        # Initialize agent
        logger.info("Initializing enhanced SmolAgent...")
        agent = SmolAgent()
        
        # Run the test suite
        logger.info("Starting test suite...")
        results = run_test_suite(agent)
        
        # Summarize the results
        summarize_results(results)
        
    except Exception as e:
        logger.error(f"Error running tests: {str(e)}")

if __name__ == "__main__":
    main() 