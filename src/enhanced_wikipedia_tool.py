#!/usr/bin/env python3
"""
Enhanced Wikipedia Tool for SmolAgent with REST API integration.

This tool provides advanced Wikipedia content extraction capabilities
using efficient REST API endpoints instead of HTML scraping to avoid truncation issues.
"""

import re
import json
import logging
import requests
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import quote_plus, unquote
import os
import time

from smolagents import Tool

# Configure logging
logger = logging.getLogger("EnhancedWikipediaTool")

class EnhancedWikipediaTool(Tool):
    """Enhanced Wikipedia tool with REST API integration and smart content targeting."""
    
    name = "enhanced_wikipedia_search"
    description = """
    Advanced Wikipedia content extraction tool optimized for accurate data retrieval.
    
    Key Features:
    - Uses Wikipedia REST API for efficient data access (avoids 50KB+ downloads)
    - Hierarchical search strategy: categories → summaries → sections → full content
    - Specialized discography and structured data extraction
    - Date range filtering for albums/releases within specified years
    - Smart fallback strategies for maximum reliability
    
    Best for: Artist discographies, biographical data, structured information, research queries.
    
    Example: For "Mercedes Sosa albums", it checks Category:Mercedes_Sosa_albums first 
    (2KB) instead of downloading the full 50KB biography page.
    """
    
    inputs = {
        "query": {
            "type": "string", 
            "description": "Wikipedia search query (artist name, topic, etc.). Be specific for best results."
        },
        "section_filter": {
            "type": "string",
            "description": "Optional: Target specific sections like 'Discography', 'Studio albums', 'Career', 'Biography'",
            "nullable": True
        },
        "year_range": {
            "type": "string", 
            "description": "Optional: Filter results by year range 'YYYY-YYYY' or single year 'YYYY'",
            "nullable": True
        },
        "data_type": {
            "type": "string",
            "description": "Optional: Specify data type - 'albums', 'discography', 'biography', 'summary', 'general'",
            "nullable": True
        }
    }
    
    output_type = "string"
    
    def __init__(self, **kwargs):
        """Initialize with Wikipedia REST API configuration."""
        super().__init__(**kwargs)
        
        # API endpoints
        self.rest_api_base = "https://en.wikipedia.org/api/rest_v1"
        self.legacy_api_base = "https://en.wikipedia.org/w/api.php"
        
        # Headers for API requests
        user_agent = os.environ.get("WIKIPEDIA_API_USER_AGENT", "EnhancedAgent/1.0")
        self.headers = {
            'User-Agent': user_agent,
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip, deflate'
        }
        
        # Cache for repeated requests
        self._cache = {}
        
    def forward(self, query: str, section_filter: str = None, year_range: str = None, 
                data_type: str = None) -> str:
        """
        Execute hierarchical Wikipedia search with smart content targeting.
        """
        if not query:
            return "Error: No search query provided"
        
        logger.info(f"🔍 Wikipedia search: '{query}' | Section: {section_filter} | Years: {year_range} | Type: {data_type}")
        
        try:
            # Step 1: Determine optimal search strategy
            search_strategy = self._determine_search_strategy(query, data_type)
            logger.info(f"📋 Using search strategy: {search_strategy}")
            
            # Step 2: Execute hierarchical search
            result = self._execute_hierarchical_search(query, section_filter, year_range, search_strategy)
            
            if result:
                return result
            else:
                return f"❌ No relevant Wikipedia content found for: {query}"
                
        except Exception as e:
            logger.error(f"❌ Error in Wikipedia search '{query}': {str(e)}")
            return f"Error searching Wikipedia: {str(e)}"
    
    def _determine_search_strategy(self, query: str, data_type: str = None) -> str:
        """Determine the optimal search strategy based on query and data type."""
        query_lower = query.lower()
        
        # Strategy 1: Albums/Discography (check categories first)
        if (data_type == "albums" or data_type == "discography" or 
            any(keyword in query_lower for keyword in ["albums", "discography", "songs", "releases"])):
            return "category_first"
        
        # Strategy 2: Quick facts (use summary API)
        if (data_type == "summary" or 
            any(keyword in query_lower for keyword in ["born", "died", "when", "where", "what is"])):
            return "summary_first"
        
        # Strategy 3: Biographical (target sections)
        if (data_type == "biography" or 
            any(keyword in query_lower for keyword in ["life", "career", "history", "biography"])):
            return "sections_first"
        
        # Strategy 4: General (balanced approach)
        return "balanced"
    
    def _execute_hierarchical_search(self, query: str, section_filter: str, 
                                   year_range: str, strategy: str) -> Optional[str]:
        """Execute search using the determined strategy."""
        
        if strategy == "category_first":
            return self._category_first_search(query, year_range)
        elif strategy == "summary_first":
            return self._summary_first_search(query, section_filter)
        elif strategy == "sections_first":
            return self._sections_first_search(query, section_filter, year_range)
        else:  # balanced
            return self._balanced_search(query, section_filter, year_range)
    
    def _category_first_search(self, query: str, year_range: str) -> Optional[str]:
        """Strategy 1: Check category pages first (most efficient for albums/discography)."""
        logger.info("🎵 Using category-first strategy")
        
        # Try various category patterns
        category_patterns = [
            f"Category:{query}_albums",
            f"Category:{query}_discography", 
            f"Category:{query}_songs",
            f"Category:{query.replace(' ', '_')}_albums",
            f"Category:Albums_by_{query}",
            f"Category:Songs_by_{query}"
        ]
        
        for category in category_patterns:
            try:
                logger.info(f"🔍 Checking category: {category}")
                category_data = self._get_category_content(category)
                if category_data and len(category_data) > 100:
                    logger.info(f"✅ Found data in {category}")
                    return self._format_category_output(category_data, category, query, year_range)
            except Exception as e:
                logger.debug(f"Category {category} failed: {str(e)}")
                continue
        
        # Fallback to artist page with section targeting
        logger.info("🔄 Category search failed, trying artist page with discography section")
        return self._sections_first_search(query, "discography", year_range)
    
    def _get_category_content(self, category_title: str) -> Optional[str]:
        """Get category page content using REST API."""
        try:
            # First try summary endpoint
            encoded_title = quote_plus(category_title.replace(' ', '_'))
            summary_url = f"{self.rest_api_base}/page/summary/{encoded_title}"
            
            response = requests.get(summary_url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'extract' in data:
                    return data['extract']
            
            # Fallback to mobile sections
            sections_url = f"{self.rest_api_base}/page/mobile-sections/{encoded_title}"
            response = requests.get(sections_url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'sections' in data:
                    content_parts = []
                    for section in data['sections']:
                        if 'text' in section:
                            content_parts.append(section['text'])
                    return '\n'.join(content_parts)
            
            return None
            
        except Exception as e:
            logger.debug(f"Error getting category content: {str(e)}")
            return None
    
    def _summary_first_search(self, query: str, section_filter: str) -> Optional[str]:
        """Strategy 2: Use summary API for quick facts."""
        logger.info("📄 Using summary-first strategy")
        
        # Search for the page
        page_title = self._search_wikipedia(query)
        if not page_title:
            return None
        
        # Get summary via REST API
        summary_data = self._get_page_summary(page_title)
        if summary_data:
            return self._format_summary_output(summary_data, page_title, query)
        
        return None
    
    def _get_page_summary(self, page_title: str) -> Optional[Dict]:
        """Get page summary using REST API."""
        try:
            encoded_title = quote_plus(page_title.replace(' ', '_'))
            url = f"{self.rest_api_base}/page/summary/{encoded_title}"
            
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.debug(f"Error getting summary: {str(e)}")
            return None
    
    def _sections_first_search(self, query: str, section_filter: str, year_range: str) -> Optional[str]:
        """Strategy 3: Target specific sections using mobile API."""
        logger.info("📖 Using sections-first strategy")
        
        # Search for the page
        page_title = self._search_wikipedia(query)
        if not page_title:
            return None
        
        # Get sections data
        sections_data = self._get_page_sections(page_title)
        if sections_data:
            return self._format_sections_output(sections_data, page_title, query, section_filter, year_range)
        
        return None
    
    def _get_page_sections(self, page_title: str) -> Optional[Dict]:
        """Get page sections using mobile REST API."""
        try:
            encoded_title = quote_plus(page_title.replace(' ', '_'))
            url = f"{self.rest_api_base}/page/mobile-sections/{encoded_title}"
            
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.debug(f"Error getting sections: {str(e)}")
            return None
    
    def _balanced_search(self, query: str, section_filter: str, year_range: str) -> Optional[str]:
        """Strategy 4: Balanced approach - summary + targeted sections."""
        logger.info("⚖️ Using balanced strategy")
        
        # Search for the page
        page_title = self._search_wikipedia(query)
        if not page_title:
            return None
        
        # Get both summary and sections
        summary_data = self._get_page_summary(page_title)
        sections_data = self._get_page_sections(page_title)
        
        if summary_data or sections_data:
            return self._format_balanced_output(summary_data, sections_data, page_title, query, 
                                              section_filter, year_range)
        
        return None
    
    def _search_wikipedia(self, query: str) -> Optional[str]:
        """Search Wikipedia and return the best matching page title."""
        try:
            params = {
                'action': 'query',
                'format': 'json',
                'list': 'search',
                'srsearch': query,
                'srlimit': 5,
                'srinfo': 'suggestion'
            }
            
            response = requests.get(self.legacy_api_base, params=params, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'query' in data and 'search' in data['query']:
                results = data['query']['search']
                if results:
                    # Return the title of the most relevant result
                    return results[0]['title']
            
            return None
            
        except Exception as e:
            logger.error(f"Error searching Wikipedia: {str(e)}")
            return None
    
    def _format_category_output(self, content: str, category: str, query: str, year_range: str) -> str:
        """Format category page output with album counting."""
        output_parts = [
            f"📂 Wikipedia Category: {category}",
            f"🔍 Search Query: {query}",
            "=" * 60
        ]
        
        # Count albums/items in category
        album_count = self._count_albums_in_content(content)
        if album_count > 0:
            output_parts.append(f"\n🎵 ALBUM COUNT: {album_count}")
        
        # Filter by year range if specified
        if year_range:
            filtered_content = self._filter_by_year_range(content, year_range)
            if filtered_content != content:
                filtered_count = self._count_albums_in_content(filtered_content)
                output_parts.append(f"📅 Albums in {year_range}: {filtered_count}")
                content = filtered_content
        
        # Add content
        output_parts.append(f"\n📋 CATEGORY CONTENT:")
        output_parts.append(content[:2000] + ("..." if len(content) > 2000 else ""))
        
        return "\n".join(output_parts)
    
    def _format_summary_output(self, summary_data: Dict, page_title: str, query: str) -> str:
        """Format summary output for quick facts."""
        output_parts = [
            f"📄 Wikipedia Article: {page_title}",
            f"🔍 Search Query: {query}",
            "=" * 60
        ]
        
        # Add key information
        if 'extract' in summary_data:
            output_parts.append(f"\n📖 SUMMARY:")
            output_parts.append(summary_data['extract'])
        
        # Add structured data if available
        if 'description' in summary_data:
            output_parts.append(f"\n🏷️ DESCRIPTION: {summary_data['description']}")
        
        if 'coordinates' in summary_data:
            coords = summary_data['coordinates']
            output_parts.append(f"\n🌍 COORDINATES: {coords.get('lat', 'N/A')}, {coords.get('lon', 'N/A')}")
        
        return "\n".join(output_parts)
    
    def _format_sections_output(self, sections_data: Dict, page_title: str, query: str, 
                              section_filter: str, year_range: str) -> str:
        """Format sections output with targeted content extraction."""
        output_parts = [
            f"📖 Wikipedia Article: {page_title}",
            f"🔍 Search Query: {query}",
            "=" * 60
        ]
        
        if 'sections' not in sections_data:
            return "❌ No sections data available"
        
        # Filter sections based on section_filter
        relevant_sections = self._filter_relevant_sections(sections_data['sections'], section_filter)
        
        if not relevant_sections:
            # If no specific sections found, show summary
            for section in sections_data['sections'][:2]:  # First 2 sections
                if 'line' in section:
                    output_parts.append(f"\n📖 {section['line']}:")
                if 'text' in section:
                    text = section['text'][:1000] + ("..." if len(section['text']) > 1000 else "")
                    output_parts.append(text)
        else:
            # Show filtered sections
            for section in relevant_sections:
                if 'line' in section:
                    output_parts.append(f"\n📖 {section['line']}:")
                if 'text' in section:
                    text = section['text']
                    # Apply year filtering if specified
                    if year_range:
                        text = self._filter_by_year_range(text, year_range)
                    # Count albums if this looks like discography
                    if any(keyword in section.get('line', '').lower() 
                          for keyword in ['discography', 'albums', 'releases']):
                        album_count = self._count_albums_in_content(text)
                        if album_count > 0:
                            output_parts.append(f"🎵 Albums found: {album_count}")
                    
                    output_parts.append(text[:1500] + ("..." if len(text) > 1500 else ""))
        
        return "\n".join(output_parts)
    
    def _format_balanced_output(self, summary_data: Optional[Dict], sections_data: Optional[Dict], 
                              page_title: str, query: str, section_filter: str, year_range: str) -> str:
        """Format balanced output combining summary and sections."""
        output_parts = [
            f"📄 Wikipedia Article: {page_title}",
            f"🔍 Search Query: {query}",
            "=" * 60
        ]
        
        # Add summary if available
        if summary_data and 'extract' in summary_data:
            output_parts.append(f"\n📖 SUMMARY:")
            output_parts.append(summary_data['extract'][:500] + ("..." if len(summary_data['extract']) > 500 else ""))
        
        # Add relevant sections
        if sections_data and 'sections' in sections_data:
            relevant_sections = self._filter_relevant_sections(sections_data['sections'], section_filter)
            
            if relevant_sections:
                output_parts.append(f"\n📖 RELEVANT SECTIONS:")
                for section in relevant_sections[:3]:  # Limit to 3 sections
                    if 'line' in section:
                        output_parts.append(f"\n• {section['line']}:")
                    if 'text' in section:
                        text = section['text']
                        if year_range:
                            text = self._filter_by_year_range(text, year_range)
                        output_parts.append(text[:800] + ("..." if len(text) > 800 else ""))
        
        return "\n".join(output_parts)
    
    def _filter_relevant_sections(self, sections: List[Dict], section_filter: str) -> List[Dict]:
        """Filter sections based on section_filter criteria."""
        if not section_filter:
            # Default relevant keywords for music/biography articles
            keywords = ['discography', 'albums', 'career', 'life', 'biography', 'history', 
                       'releases', 'singles', 'works', 'filmography']
        else:
            keywords = [term.strip().lower() for term in section_filter.split(',')]
        
        relevant = []
        for section in sections:
            if 'line' in section:
                section_title = section['line'].lower()
                if any(keyword in section_title for keyword in keywords):
                    relevant.append(section)
        
        return relevant
    
    def _count_albums_in_content(self, content: str) -> int:
        """Count albums/releases in content."""
        # Look for numbered lists, bullet points, or table rows that might indicate albums
        patterns = [
            r'^\s*\d+\.\s+.*album',  # Numbered list with "album"
            r'^\s*[•*-]\s+.*\(\d{4}\)',  # Bullet points with years
            r'^\s*\d{4}\s+.*',  # Lines starting with years
            r'following \d+ (?:pages|albums|items)',  # "following X albums"
            r'(\d+)\s+(?:studio\s+)?albums?',  # "X albums" or "X studio albums"
            r'(\d+)\s+(?:total|pages|items)'  # "X total" etc.
        ]
        
        max_count = 0
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
            if matches:
                try:
                    # Try to extract numbers from matches
                    for match in matches:
                        if isinstance(match, tuple):
                            match = match[0]
                        if isinstance(match, str):
                            numbers = re.findall(r'\d+', match)
                            if numbers:
                                count = int(numbers[0])
                                max_count = max(max_count, count)
                        else:
                            max_count = max(max_count, len(matches))
                except:
                    continue
        
        # Also count lines that look like album entries
        lines = content.split('\n')
        album_lines = 0
        for line in lines:
            line = line.strip()
            if (line and 
                (re.search(r'\b\d{4}\b', line) or  # Contains a year
                 any(keyword in line.lower() for keyword in ['album', 'ep', 'single', 'release']))):
                album_lines += 1
        
        return max(max_count, min(album_lines, 20))  # Cap at reasonable number
    
    def _filter_by_year_range(self, content: str, year_range: str) -> str:
        """Filter content by year range."""
        try:
            start_year, end_year = self._parse_year_range(year_range)
            if not start_year:
                return content
            
            filtered_lines = []
            for line in content.split('\n'):
                years = re.findall(r'\b(19|20)\d{2}\b', line)
                if years:
                    line_years = [int(year) for year in years]
                    if any(start_year <= year <= (end_year or start_year) for year in line_years):
                        filtered_lines.append(line)
                else:
                    # Keep lines without years (headers, descriptions, etc.)
                    if len(line.strip()) < 100:  # Short lines are likely headers
                        filtered_lines.append(line)
            
            return '\n'.join(filtered_lines) if filtered_lines else content
            
        except:
            return content
    
    def _parse_year_range(self, year_range: str) -> Tuple[Optional[int], Optional[int]]:
        """Parse year range string into start and end years."""
        if not year_range:
            return None, None
        
        try:
            year_range = year_range.strip()
            if '-' in year_range:
                parts = year_range.split('-', 1)
                start = int(parts[0].strip())
                end = int(parts[1].strip())
                return start, end
            else:
                year = int(year_range)
                return year, year
        except (ValueError, TypeError):
            return None, None

def get_enhanced_wikipedia_tool():
    """Create and return an enhanced Wikipedia tool instance."""
    return EnhancedWikipediaTool() 