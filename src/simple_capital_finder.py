#!/usr/bin/env python3
"""
Simple Capital Finder

This module shows how to properly use the web_search tool from smolagents.
It serves as an example for agents on how to handle the search queries.
"""

from smolagents import Tool, ToolCallingAgent, HfApiModel
from smolagents.tools.duckduckgo_search import DuckDuckGoSearchTool

def find_capital(country: str) -> str:
    """
    Find the capital of a country using the DuckDuckGoSearchTool.
    
    Args:
        country: The country to find the capital of
        
    Returns:
        The capital of the country
    """
    # Create the search tool
    search_tool = DuckDuckGoSearchTool()
    
    # Create a simple agent with the search tool
    model = HfApiModel(model_id="meta-llama/Llama-3.1-8B-Instruct")
    agent = ToolCallingAgent(
        tools=[search_tool],
        model=model
    )
    
    # Run the agent with the query
    query = f"What is the capital of {country}?"
    result = agent.run(query)
    
    # Return the result
    return result

def main():
    """Run the capital finder with France as the country."""
    country = "France"
    capital = find_capital(country)
    print(f"The capital of {country} is: {capital}")

if __name__ == "__main__":
    main() 