#!/usr/bin/env python3
"""
Demo script showing proper usage of the EnhancedAgent.

This script demonstrates how to initialize and use the EnhancedAgent
with the appropriate tools and model.
"""

import os
import sys
import logging
from pathlib import Path

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
logger = logging.getLogger("AgentDemo")

def main():
    """Run a demonstration of the EnhancedAgent."""
    logger.info("Starting EnhancedAgent demo...")
    
    try:
        # Import the enhanced agent
        from src.enhanced_agent import EnhancedAgent
        
        # Initialize the agent with verbose output and reasonable steps
        agent = EnhancedAgent(
            max_steps=8,
            verbose=True
        )
        logger.info("Successfully initialized the EnhancedAgent")
        
        # Display agent configuration
        tools = agent.tools
        logger.info(f"Agent loaded with {len(tools)} tools:")
        for tool in tools:
            logger.info(f"- {tool.name}: {tool.description}")
        
        # Test with a question that can be answered using tools
        question = "Who is the current CEO of OpenAI?"
        logger.info(f"Asking question: {question}")
        
        # Process the question
        answer = agent(question)
        logger.info(f"Answer: {answer}")
        
        return True
        
    except Exception as e:
        logger.error(f"Demo failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = main()
    sys.exit(0 if result else 1) 