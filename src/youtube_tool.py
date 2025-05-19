#!/usr/bin/env python3
"""
Custom YouTube tool for SmolAgent.
This tool provides functionality to extract information from YouTube videos.
"""

import os
import re
import json
import logging
from typing import Optional, Dict, Any
from urllib.parse import urlparse, parse_qs

from smolagents import Tool, tool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("YouTubeTool")

class YouTubeTool(Tool):
    """Tool for extracting information from YouTube videos."""
    
    description = "Extract information from YouTube videos, including metadata, transcripts, and summaries"
    name = "youtube"
    
    inputs = {
        "video_url": {
            "type": str,
            "description": "URL of the YouTube video to process"
        },
        "action": {
            "type": str,
            "description": "Action to perform: 'metadata', 'transcript', or 'summary'"
        }
    }
    
    output_type = str
    
    def setup(self):
        """Initialize the tool with required libraries."""
        # Check for required libraries
        try:
            import requests
            self.requests = requests
        except ImportError:
            logger.warning("Requests library not found. Limited functionality available.")
            self.requests = None
    
    def forward(self, video_url: str, action: str = "metadata") -> str:
        """
        Process a YouTube video to extract the requested information.
        
        Args:
            video_url: URL of the YouTube video
            action: Action to perform (metadata, transcript, summary)
            
        Returns:
            Extracted information based on the requested action
        """
        # Validate URL
        if not self._is_valid_youtube_url(video_url):
            return "Error: Invalid YouTube URL provided"
        
        # Extract video ID
        video_id = self._extract_video_id(video_url)
        if not video_id:
            return "Error: Could not extract video ID from URL"
        
        # Process based on requested action
        if action.lower() == "metadata":
            return self._get_video_metadata(video_id)
        elif action.lower() == "transcript":
            return self._get_video_transcript(video_id)
        elif action.lower() == "summary":
            return self._get_video_summary(video_id)
        else:
            return f"Error: Unsupported action '{action}'. Use 'metadata', 'transcript', or 'summary'."
    
    def _is_valid_youtube_url(self, url: str) -> bool:
        """Check if a URL is a valid YouTube URL."""
        if not url:
            return False
        
        # Check if it's a YouTube URL
        youtube_regex = (
            r'(https?://)?(www\.)?'
            r'(youtube|youtu|youtube-nocookie)\.(com|be)/'
            r'(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
        )
        
        youtube_match = re.match(youtube_regex, url)
        return youtube_match is not None
    
    def _extract_video_id(self, url: str) -> Optional[str]:
        """Extract the video ID from a YouTube URL."""
        # Handle different URL formats
        parsed_url = urlparse(url)
        
        if parsed_url.hostname in ('youtu.be', 'www.youtu.be'):
            return parsed_url.path.lstrip('/')
        
        if parsed_url.hostname in ('youtube.com', 'www.youtube.com'):
            if parsed_url.path == '/watch':
                query = parse_qs(parsed_url.query)
                return query.get('v', [None])[0]
            elif parsed_url.path.startswith('/embed/'):
                return parsed_url.path.split('/')[2]
            elif parsed_url.path.startswith('/v/'):
                return parsed_url.path.split('/')[2]
        
        return None
    
    def _get_video_metadata(self, video_id: str) -> str:
        """
        Get metadata about a YouTube video.
        
        In a production environment, this would use the YouTube API.
        For this implementation, we'll use a simplified approach.
        """
        if not self.requests:
            return "Error: Requests library not available for fetching metadata"
        
        try:
            # Use oEmbed endpoint for basic metadata (doesn't require API key)
            oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
            response = self.requests.get(oembed_url)
            
            if response.status_code == 200:
                data = response.json()
                return json.dumps({
                    "title": data.get("title", "Unknown"),
                    "author": data.get("author_name", "Unknown"),
                    "channel_url": data.get("author_url", ""),
                    "thumbnail": data.get("thumbnail_url", ""),
                    "video_id": video_id,
                    "video_url": f"https://www.youtube.com/watch?v={video_id}"
                }, indent=2)
            else:
                return f"Error: Could not fetch metadata. Status code: {response.status_code}"
        except Exception as e:
            return f"Error fetching metadata: {str(e)}"
    
    def _get_video_transcript(self, video_id: str) -> str:
        """
        Get transcript of a YouTube video.
        
        In a production environment, this would use the YouTube API or youtube-transcript-api.
        For this implementation, we provide a simplified response.
        """
        return (
            "This is a simplified transcript response. In a production environment, "
            "this would use youtube-transcript-api or YouTube Data API to fetch the actual transcript. "
            f"Video ID: {video_id}"
        )
    
    def _get_video_summary(self, video_id: str) -> str:
        """
        Get a summary of a YouTube video.
        
        In a production environment, this would fetch the transcript and use NLP to summarize.
        For this implementation, we provide a simplified response.
        """
        return (
            "This is a simplified summary response. In a production environment, "
            "this would fetch the transcript and use NLP to generate a proper summary. "
            f"Video ID: {video_id}"
        )

# Function to get a YouTube tool instance
def get_youtube_tool() -> YouTubeTool:
    """Create and return a YouTube tool instance."""
    return YouTubeTool() 