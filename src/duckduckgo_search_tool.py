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
from src.error_handler import with_error_handling, error_handler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DuckDuckGoSearchTool")

class DuckDuckGoSearchTool(Tool):
    """Tool for performing web searches using DuckDuckGo."""
    
    name = "web_search"
    description = "Search the web for information using DuckDuckGo and other search providers"
    
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
            logger.info("DuckDuckGoSearchTool initialized successfully with requests library")
            
            # Set up search providers
            self.search_providers = [
                self._duckduckgo_search,
                self._serper_search,
                self._custom_search_engine
            ]
            
            # Initialize provider retry counts
            self.provider_failures = {i: 0 for i in range(len(self.search_providers))}
            self.max_provider_failures = 3  # Maximum consecutive failures before blacklisting
            
            # Check for API keys for alternative search providers
            import os
            self.serper_api_key = os.environ.get("SERPER_API_KEY")
            self.cse_api_key = os.environ.get("GOOGLE_CSE_API_KEY")
            self.cse_engine_id = os.environ.get("GOOGLE_CSE_ID")
            
        except ImportError:
            logger.warning("Requests library not found. Tool will have limited functionality.")
            self.requests = None
    
    @with_error_handling(tool_name="web_search")
    def _perform_search(self, query: str, num_results: int = 5) -> str:
        """
        Internal method to perform the search with multiple fallback providers.
        
        Args:
            query: The search query
            num_results: Number of results to return
            
        Returns:
            Formatted search results
        """
        if not self.requests:
            raise ImportError("Requests library not available for web search")
        
        if not query:
            raise ValueError("Empty search query provided")
        
        # Track errors to report if all providers fail
        all_errors = []
        
        # Try each search provider in order until one succeeds
        for i, provider in enumerate(self.search_providers):
            # Skip provider if it has failed too many times consecutively
            if self.provider_failures.get(i, 0) >= self.max_provider_failures:
                logger.warning(f"Skipping search provider {i} due to too many failures")
                continue
                
            try:
                # Try this provider
                logger.info(f"Trying search provider {i}")
                results = provider(query, num_results)
                
                # Reset failure count on success
                self.provider_failures[i] = 0
                
                # Return results if we got them
                if results and not (isinstance(results, str) and "No results found" in results):
                    return results
                
                # No results case - log but try next provider
                logger.info(f"Provider {i} returned no results")
                
            except Exception as e:
                # Increment failure count for this provider
                self.provider_failures[i] = self.provider_failures.get(i, 0) + 1
                logger.warning(f"Search provider {i} failed: {str(e)}")
                all_errors.append(f"Provider {i}: {str(e)}")
        
        # If all providers failed, return the errors
        if all_errors:
            return f"All search providers failed for query '{query}':\n" + "\n".join(all_errors)
            
        # If all providers returned no results, return a standard message
        return f"No results found for query: {query}"
    
    def _duckduckgo_search(self, query: str, num_results: int) -> str:
        """Original DuckDuckGo search implementation."""
        # Format the query for URL inclusion
        encoded_query = quote_plus(query)
        
        # Make the DuckDuckGo search request
        url = f"https://api.duckduckgo.com/?q={encoded_query}&format=json"
        response = self.requests.get(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        })
        
        if response.status_code != 200:
            raise ConnectionError(f"DuckDuckGo search failed with status code: {response.status_code}")
        
        data = response.json()
        
        # Fallback to a more detailed API if the simple one doesn't return good results
        if not data.get("AbstractText") and not data.get("RelatedTopics"):
            logger.info("Using fallback DuckDuckGo HTML search method")
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
    
    def _serper_search(self, query: str, num_results: int) -> str:
        """
        Alternative search using Serper.dev API if available.
        
        Args:
            query: The search query
            num_results: Number of results to return
            
        Returns:
            Formatted search results
        """
        if not self.serper_api_key:
            raise ValueError("Serper API key not configured")
            
        url = "https://google.serper.dev/search"
        payload = json.dumps({
            "q": query,
            "num": min(num_results, 10)
        })
        headers = {
            'X-API-KEY': self.serper_api_key,
            'Content-Type': 'application/json'
        }
        
        response = self.requests.post(url, headers=headers, data=payload)
        
        if response.status_code != 200:
            raise ConnectionError(f"Serper search failed with status code: {response.status_code}")
            
        data = response.json()
        results = []
        
        # Process organic search results
        for item in data.get("organic", [])[:num_results]:
            results.append({
                "title": item.get("title", "No title"),
                "snippet": item.get("snippet", "No description available"),
                "source": "Google via Serper",
                "url": item.get("link", "")
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
        
    def _custom_search_engine(self, query: str, num_results: int) -> str:
        """
        Use Google Custom Search Engine as another fallback.
        
        Args:
            query: The search query
            num_results: Number of results to return
            
        Returns:
            Formatted search results
        """
        if not self.cse_api_key or not self.cse_engine_id:
            raise ValueError("Google Custom Search Engine not configured")
            
        url = f"https://www.googleapis.com/customsearch/v1"
        params = {
            "key": self.cse_api_key,
            "cx": self.cse_engine_id,
            "q": query,
            "num": min(num_results, 10)
        }
        
        response = self.requests.get(url, params=params)
        
        if response.status_code != 200:
            raise ConnectionError(f"Google CSE search failed with status code: {response.status_code}")
            
        data = response.json()
        results = []
        
        # Process search results
        for item in data.get("items", [])[:num_results]:
            results.append({
                "title": item.get("title", "No title"),
                "snippet": item.get("snippet", "No description available"),
                "source": "Google Custom Search",
                "url": item.get("link", "")
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
    
    def forward(self, query: str, num_results: int = 5) -> str:
        """
        Perform a web search using DuckDuckGo and return the results.
        
        Args:
            query: The search query
            num_results: Number of results to return (default: 5)
            
        Returns:
            Formatted search results
        """
        try:
            # Log the search query
            logger.info(f"Performing web search for: {query}")
            
            # Call the internal method with error handling
            result = self._perform_search(query, num_results)
            return result
            
        except Exception as e:
            # Format any unhandled errors
            error_info = error_handler.format_error(e, "web_search")
            logger.error(f"Error in web search: {error_info['message']}")
            
            # Get appropriate fallback response
            fallback = error_handler.get_fallback_response(error_info, "web_search")
            return fallback.get("error", f"Search error: {str(e)}")
    
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
    
    @with_error_handling(tool_name="web_search")
    def _fallback_search(self, query: str, num_results: int) -> str:
        """
        Fallback search method using an alternative API.
        
        This is used when the primary DuckDuckGo API doesn't return useful results.
        
        Args:
            query: The search query
            num_results: Number of results to return
            
        Returns:
            Formatted search results
        """
        # Use a different endpoint or approach for searching
        # This is a simplified implementation
        search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
        
        response = self.requests.get(search_url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        })
        
        if response.status_code != 200:
            raise ConnectionError(f"Fallback search failed with status code {response.status_code}")
        
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

def get_duckduckgo_search_tool():
    """Create and return a DuckDuckGo search tool instance."""
    tool = DuckDuckGoSearchTool()
    
    # Ensure the tool is properly set up
    if not hasattr(tool, 'setup'):
        logger.warning("DuckDuckGoSearchTool missing setup method, adding it")
        tool.setup = lambda: None
    
    # Call setup explicitly to initialize the tool
    try:
        tool.setup()
        
        # Verify that setup worked
        if not hasattr(tool, 'requests'):
            logger.warning("DuckDuckGoSearchTool setup did not create requests attribute, setting manually")
            import requests
            tool.requests = requests
            
    except Exception as e:
        logger.error(f"Error setting up DuckDuckGoSearchTool: {str(e)}")
        # Fall back to module-level requests import
        import requests
        tool.requests = requests
    
    return tool 