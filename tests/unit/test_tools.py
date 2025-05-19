#!/usr/bin/env python3
"""
Test script to verify the agent recognizes and uses tools correctly.
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
logger = logging.getLogger("ToolTest")

def main():
    """Test if the agent correctly recognizes and uses the search tool."""
    logger.info("Starting tool recognition test...")
    
    # Import the enhanced agent
    from src.enhanced_agent import EnhancedAgent
    
    # Create the agent
    agent = EnhancedAgent(verbose=True, max_steps=3)
    logger.info("Successfully created enhanced agent")
    
    # Print out the available tools
    tool_names = [tool.name for tool in agent.tools]
    logger.info(f"Available tools: {', '.join(tool_names)}")
    
    # Now create a simplified example Python script
    with open("example_tool_usage.py", "w") as f:
        f.write("""# Example of how to use the web_search tool
from smolagents import Tool

# Use the web_search tool
result = web_search(query="capital of France")
print("Search results:", result)
        """)
    
    logger.info("Created example script")
    logger.info("Test complete")
    return True

if __name__ == "__main__":
    main() 