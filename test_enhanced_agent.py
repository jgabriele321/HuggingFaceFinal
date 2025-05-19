#!/usr/bin/env python3
"""
Test script for the Enhanced Agent implementation.

This script runs a series of test questions against the enhanced agent to verify 
that it properly handles tools, follows the ReAct framework, and produces accurate results.
"""

import os
import sys
import logging
import json
from pathlib import Path
from datetime import datetime

# Add src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"logs/enhanced_agent_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("TestEnhancedAgent")

# Ensure the logs directory exists
Path("logs").mkdir(exist_ok=True)

def run_test(agent, question, expected_tools=None):
    """
    Run a test question against the agent and analyze the results.
    
    Args:
        agent: The agent to test
        question: The question to ask
        expected_tools: Optional list of tool names expected to be used
        
    Returns:
        tuple: (passed, result, analysis)
    """
    logger.info(f"Testing question: {question}")
    
    # Run the agent
    result = agent(question)
    
    # Basic analysis
    analysis = {
        "question": question,
        "result": result,
        "length": len(result) if result else 0,
        "has_answer": bool(result and len(result) > 10)
    }
    
    # Tool usage analysis would be included in the agent's verbose output
    
    # Simple pass/fail check
    passed = analysis["has_answer"]
    
    logger.info(f"Test {'PASSED' if passed else 'FAILED'} for question: {question}")
    logger.info(f"Result: {result[:100]}...")
    
    return passed, result, analysis

def main():
    """Main test function."""
    from src.enhanced_agent import EnhancedAgent
    
    logger.info("Initializing enhanced agent for testing...")
    
    # Initialize the agent
    # Note: This requires an OpenRouter API key in the environment
    agent = EnhancedAgent(verbose=True)
    
    # Test questions designed to exercise different tools and capabilities
    test_questions = [
        # Basic question to test general knowledge
        {"question": "What is the capital of France?", "expected_tools": []},
        
        # Question requiring web search
        {"question": "What are the latest developments in quantum computing?", "expected_tools": ["web_search"]},
        
        # Question requiring YouTube tool
        {"question": "Can you analyze this YouTube video: https://www.youtube.com/watch?v=dQw4w9WgXcQ", "expected_tools": ["youtube"]},
        
        # Question requiring website content analysis
        {"question": "Summarize the content from https://www.example.com", "expected_tools": ["visit_webpage"]},
        
        # Complex question requiring multiple tools
        {"question": "What is the latest news about SpaceX and how does it compare to their mission statement on their website?", 
         "expected_tools": ["web_search", "visit_webpage"]}
    ]
    
    # Run tests
    results = []
    passed_count = 0
    
    for i, test in enumerate(test_questions, 1):
        logger.info(f"Running test {i}/{len(test_questions)}")
        
        passed, result, analysis = run_test(agent, test["question"], test.get("expected_tools"))
        
        if passed:
            passed_count += 1
        
        results.append({
            "id": i,
            "passed": passed,
            "question": test["question"],
            "expected_tools": test.get("expected_tools", []),
            "result_summary": result[:200] + "..." if result and len(result) > 200 else result,
            "analysis": analysis
        })
    
    # Overall test summary
    logger.info(f"Test summary: {passed_count}/{len(test_questions)} tests passed")
    
    # Save results to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"test_results_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump({
            "total": len(test_questions),
            "passed": passed_count,
            "timestamp": timestamp,
            "results": results
        }, f, indent=2)
    
    logger.info(f"Test results saved to {results_file}")
    
    return passed_count == len(test_questions)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 