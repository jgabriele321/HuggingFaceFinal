#!/usr/bin/env python3
"""
DuckDuckGo Search Tool for SmolAgent.

This tool provides web search functionality using DuckDuckGo.
"""

import re
import requests
import logging
import json
from typing import List, Dict, Any, Optional
from urllib.parse import quote_plus

from smolagents import Tool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DuckDuckGoSearchTool")

class DuckDuckGoSearchTool(Tool):
    """Tool for performing web searches using DuckDuckGo."""
    
    name = "web_search"
    description = "Search the web for information using DuckDuckGo"
    
    inputs = {
        "query": {
            "type": "string",
            "description": "The search query"
        },
        "num_results": {
            "type": "integer",
            "description": "Number of results to return (default: 5)",
            "nullable": True
        }
    }
    
    output_type = "string"
    
    def setup(self):
        """Set up the tool with required dependencies."""
        try:
            import requests
            self.requests = requests
        except ImportError:
            logger.warning("Requests library not found. Tool will have limited functionality.")
            self.requests = None
    
    def forward(self, query: str, num_results: int = 5) -> str:
        """
        Perform a web search using DuckDuckGo and return the results.
        
        Args:
            query: The search query
            num_results: Number of results to return (default: 5)
            
        Returns:
            Formatted search results
        """
        if not self.requests:
            return "Error: Requests library not available for web search"
        
        if not query:
            return "Error: Empty search query provided"
        
        logger.info(f"Performing web search for: {query}")
        
        try:
            # Format the query for URL inclusion
            encoded_query = quote_plus(query)
            
            # Make the DuckDuckGo search request
            url = f"https://api.duckduckgo.com/?q={encoded_query}&format=json"
            response = self.requests.get(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            })
            
            if response.status_code != 200:
                logger.error(f"DuckDuckGo search failed with status code: {response.status_code}")
                return f"Error: Search request failed with status code {response.status_code}"
            
            data = response.json()
            
            # Fallback to a more detailed API if the simple one doesn't return good results
            if not data.get("AbstractText") and not data.get("RelatedTopics"):
                logger.info("Using fallback search method")
                return self._fallback_search(query, num_results)
            
            # Format the results
            results = []
            
            # Add the abstract if available
            if data.get("AbstractText"):
                results.append({
                    "title": data.get("Heading", "Abstract"),
                    "snippet": data.get("AbstractText"),
                    "source": data.get("AbstractSource", "DuckDuckGo"),
                    "url": data.get("AbstractURL", "")
                })
            
            # Add related topics
            for topic in data.get("RelatedTopics", [])[:num_results - len(results)]:
                if "Text" in topic and "FirstURL" in topic:
                    results.append({
                        "title": self._extract_title(topic.get("Text", "")),
                        "snippet": topic.get("Text", ""),
                        "source": "DuckDuckGo",
                        "url": topic.get("FirstURL", "")
                    })
            
            # Format the results as text
            if not results:
                return f"No results found for query: {query}"
            
            formatted_results = f"Search results for: {query}\n\n"
            for i, result in enumerate(results, 1):
                formatted_results += f"{i}. {result['title']}\n"
                formatted_results += f"   {result['snippet']}\n"
                formatted_results += f"   Source: {result['source']} - {result['url']}\n\n"
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error during web search: {str(e)}")
            return f"Error performing web search: {str(e)}"
    
    def _extract_title(self, text: str) -> str:
        """Extract a title from the text, usually the first few words."""
        if not text:
            return "No title"
        
        # Take the first sentence or up to 50 characters
        parts = text.split(" - ", 1)
        if len(parts) > 1:
            return parts[0]
        
        parts = text.split(". ", 1)
        if len(parts) > 1:
            return parts[0]
        
        return text[:50] + "..." if len(text) > 50 else text
    
    def _fallback_search(self, query: str, num_results: int) -> str:
        """
        Fallback search method using an alternative API.
        
        This is used when the primary DuckDuckGo API doesn't return useful results.
        """
        try:
            # Use a different endpoint or approach for searching
            # This is a simplified implementation
            search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
            
            response = self.requests.get(search_url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            })
            
            if response.status_code != 200:
                return f"Fallback search failed with status code {response.status_code}"
            
            # Parse the HTML response to extract results (simplified for brevity)
            # In a real implementation, this would use a proper HTML parser
            text = response.text
            results = []
            
            # Extract titles and snippets (very simplified approach)
            title_pattern = r'<a class="result__a" href="([^"]+)"[^>]*>(.*?)</a>'
            snippet_pattern = r'<a class="result__snippet"[^>]*>(.*?)</a>'
            
            titles = re.findall(title_pattern, text)
            snippets = re.findall(snippet_pattern, text)
            
            # Combine the results
            for i in range(min(num_results, len(titles), len(snippets))):
                url, title = titles[i]
                snippet = snippets[i]
                
                # Clean up HTML tags
                title = re.sub(r'<[^>]+>', '', title)
                snippet = re.sub(r'<[^>]+>', '', snippet)
                
                results.append({
                    "title": title,
                    "snippet": snippet,
                    "source": "DuckDuckGo",
                    "url": url
                })
            
            # Format the results as text
            if not results:
                return f"No results found for query: {query}"
            
            formatted_results = f"Search results for: {query}\n\n"
            for i, result in enumerate(results, 1):
                formatted_results += f"{i}. {result['title']}\n"
                formatted_results += f"   {result['snippet']}\n"
                formatted_results += f"   Source: {result['source']} - {result['url']}\n\n"
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error during fallback search: {str(e)}")
            return f"Error performing fallback search: {str(e)}"

# Function to create an instance of the tool
def get_duckduckgo_search_tool() -> Dict[str, Any]:
    """Create and return a DuckDuckGo search tool configuration."""
    return {
        "name": "web_search",
        "description": "Search the web for information using DuckDuckGo",
        "function": DuckDuckGoSearchTool().forward,
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query"
                },
                "num_results": {
                    "type": "integer",
                    "description": "Number of results to return (default: 5)",
                    "default": 5
                }
            },
            "required": ["query"]
        }
    } 