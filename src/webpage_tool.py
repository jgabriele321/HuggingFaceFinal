#!/usr/bin/env python3
"""
Webpage Content Tool for SmolAgent.

This tool provides functionality to fetch and extract content from webpages.
"""

import re
import logging
import json
import requests
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse

from smolagents import Tool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("WebpageTool")

class WebpageTool(Tool):
    """Tool for fetching and extracting content from webpages."""
    
    name = "visit_webpage"
    description = "Visit a webpage and extract its content for analysis"
    
    inputs = {
        "url": {
            "type": "string",
            "description": "URL of the webpage to visit"
        },
        "extract_mode": {
            "type": "string",
            "description": "Mode for content extraction: 'full' for all content, 'summary' for a summary, or 'structured' for structured data",
            "enum": ["full", "summary", "structured"],
            "default": "full",
            "nullable": True
        }
    }
    
    output_type = "string"
    
    def __init__(self, **kwargs):
        """Initialize the tool with session and headers."""
        super().__init__(**kwargs)
        
        # Create a session for requests
        self.session = requests.Session()
        
        # Set default headers
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # Apply headers to session
        self.session.headers.update(self.headers)
    
    def forward(self, url: str, extract_mode: str = "full") -> str:
        """
        Visit a webpage and extract its content.
        
        Args:
            url: URL of the webpage to visit
            extract_mode: Mode for content extraction
            
        Returns:
            Extracted content as a string
        """
        if not url:
            return "Error: No URL provided"
        
        # Log the operation
        logger.info(f"Visiting webpage: {url}")
        logger.info(f"Extraction mode: {extract_mode}")
        
        try:
            # Fetch the webpage
            response = self.session.get(url, timeout=10)
            
            # Check if request was successful
            if response.status_code != 200:
                return f"Error: Failed to fetch webpage. Status code: {response.status_code}"
            
            # Get the content
            html_content = response.text
            
            # Extract content based on mode
            if extract_mode == "full":
                return self._extract_full_content(html_content, url)
            elif extract_mode == "summary":
                return self._extract_summary(html_content, url)
            elif extract_mode == "structured":
                return self._extract_structured_data(html_content, url)
            else:
                return f"Error: Invalid extraction mode: {extract_mode}"
            
        except Exception as e:
            logger.error(f"Error visiting webpage {url}: {str(e)}")
            return f"Error visiting webpage: {str(e)}"
    
    def _extract_full_content(self, html_content: str, url: str) -> str:
        """Extract full content from HTML."""
        # Simple extraction of text content
        # Remove script and style elements
        html_content = re.sub(r'<script.*?</script>', '', html_content, flags=re.DOTALL)
        html_content = re.sub(r'<style.*?</style>', '', html_content, flags=re.DOTALL)
        
        # Replace image tags with their alt text
        html_content = re.sub(r'<img.*?alt="(.*?)".*?>', r'[Image: \1]', html_content)
        
        # Replace line breaks and paragraphs with newlines
        html_content = re.sub(r'<br.*?>', '\n', html_content)
        html_content = re.sub(r'<p.*?>', '\n', html_content)
        
        # Remove all HTML tags
        text_content = re.sub(r'<.*?>', '', html_content)
        
        # Replace multiple newlines with single newlines
        text_content = re.sub(r'\n{3,}', '\n\n', text_content)
        
        # Remove leading and trailing whitespace
        text_content = text_content.strip()
        
        # Limit content to reduce token usage (first ~5000 characters)
        max_length = 5000
        if len(text_content) > max_length:
            text_content = text_content[:max_length] + f"\n\n[Content truncated. Total length: {len(text_content)} characters]"
        
        return f"Content from {url}:\n\n{text_content}"
    
    def _extract_summary(self, html_content: str, url: str) -> str:
        """Extract a summary from HTML."""
        # Extract title
        title_match = re.search(r'<title>(.*?)</title>', html_content)
        title = title_match.group(1) if title_match else "Unknown title"
        
        # Extract meta description
        desc_match = re.search(r'<meta\s+name="description"\s+content="(.*?)"', html_content)
        description = desc_match.group(1) if desc_match else ""
        
        # Extract first paragraph or some content
        text_content = self._extract_full_content(html_content, url)
        first_paragraphs = "\n\n".join(text_content.split("\n\n")[:3])
        
        return f"Summary of {url}:\n\nTitle: {title}\n\nDescription: {description}\n\nContent snippet:\n{first_paragraphs}"
    
    def _extract_structured_data(self, html_content: str, url: str) -> str:
        """Extract structured data from HTML."""
        # Extract schema.org structured data
        json_ld_matches = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html_content, re.DOTALL)
        
        structured_data = []
        
        # Process JSON-LD data
        for json_ld in json_ld_matches:
            try:
                data = json.loads(json_ld)
                structured_data.append(data)
            except json.JSONDecodeError:
                continue
        
        # If no structured data found, extract basic structure
        if not structured_data:
            # Extract headings
            headings = re.findall(r'<h[1-3][^>]*>(.*?)</h[1-3]>', html_content)
            
            # Create simple structured representation
            structured_data = {
                "url": url,
                "headings": headings[:10],  # Limit to first 10 headings
                "has_images": bool(re.search(r'<img', html_content)),
                "has_videos": bool(re.search(r'<video|youtube.com/embed|vimeo.com/video', html_content)),
                "has_tables": bool(re.search(r'<table', html_content)),
                "domain": urlparse(url).netloc
            }
        
        return f"Structured data from {url}:\n\n{json.dumps(structured_data, indent=2)}"

def get_webpage_tool() -> Dict[str, Any]:
    """Create and return a webpage tool configuration."""
    return {
        "name": "visit_webpage",
        "description": "Visit a webpage and extract its content for analysis",
        "function": WebpageTool().forward,
        "parameters": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "URL of the webpage to visit"
                },
                "extract_mode": {
                    "type": "string",
                    "description": "Mode for content extraction: 'full' for all content, 'summary' for a summary, or 'structured' for structured data",
                    "enum": ["full", "summary", "structured"],
                    "default": "full"
                }
            },
            "required": ["url"]
        }
    }
    
def simple_extract_content(url: str) -> str:
    """
    Helper function to directly extract content from a webpage without using the Tool class.
    Useful for direct integration in scripts.
    
    Args:
        url: URL of the webpage to visit
        
    Returns:
        Extracted content as a string
    """
    try:
        import requests
        
        # Set user agent headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml'
        }
        
        # Fetch the webpage
        response = requests.get(url, headers=headers, timeout=10)
        
        # Check if request was successful
        if response.status_code != 200:
            return f"Error: Failed to fetch webpage. Status code: {response.status_code}"
        
        # Extract content
        html_content = response.text
        
        # Simple extraction of text content
        # Remove script and style elements
        html_content = re.sub(r'<script.*?</script>', '', html_content, flags=re.DOTALL)
        html_content = re.sub(r'<style.*?</style>', '', html_content, flags=re.DOTALL)
        
        # Remove all HTML tags
        text_content = re.sub(r'<.*?>', ' ', html_content)
        
        # Replace multiple spaces with single space
        text_content = re.sub(r'\s+', ' ', text_content)
        
        # Remove leading and trailing whitespace
        text_content = text_content.strip()
        
        return f"Content from {url}:\n\n{text_content}"
        
    except Exception as e:
        return f"Error visiting webpage: {str(e)}" 