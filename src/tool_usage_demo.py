#!/usr/bin/env python3
"""
Tool Usage Demo

This script shows how to properly use the tools available to the EnhancedAgent.
It provides explicit examples that the agent can follow.
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
logger = logging.getLogger("ToolUsageDemo")

def main():
    """Run the tool usage demonstration."""
    logger.info("Starting tool usage demonstration...")
    
    # Import the necessary components
    from smolagents import CodeAgent, HfApiModel, Tool
    from smolagents.tools import DuckDuckGoSearchTool, VisitWebpageTool
    
    # Create the search tool
    search_tool = DuckDuckGoSearchTool()
    
    # Create the webpage tool
    webpage_tool = VisitWebpageTool()
    
    # Create a simple model
    model = HfApiModel(model_id="meta-llama/Llama-3.1-8B-Instruct")
    
    # Create a simple agent with the tools
    agent = CodeAgent(
        tools=[search_tool, webpage_tool],
        model=model,
        max_steps=5
    )
    
    # Run a test query
    query = "Who is the current CEO of OpenAI?"
    logger.info(f"Running query: {query}")
    
    # Here's how the agent should use the tools
    demo_code = """
# This is how to use the web_search tool:
search_results = web_search(query="OpenAI CEO")
print(search_results)  # Display search results

# This is how to use the visit_webpage tool:
webpage_content = visit_webpage(url="https://openai.com/about")
print(webpage_content)  # Display webpage content

# This is how to use string operations to extract information:
import re
ceo_match = re.search(r'CEO[:\s]+([A-Za-z\s]+)', webpage_content)
if ceo_match:
    ceo_name = ceo_match.group(1).strip()
    print(f"The CEO of OpenAI is: {ceo_name}")
"""
    
    logger.info(f"Example code for the agent:\n{demo_code}")
    
    try:
        # Run the query with the agent
        result = agent.run(query)
        logger.info(f"Result: {result}")
        return True
    except Exception as e:
        logger.error(f"Error running agent: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main() 