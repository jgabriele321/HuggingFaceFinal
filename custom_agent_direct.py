#!/usr/bin/env python3
"""
Custom Agent Implementation with OpenRouter Gemini Model (Direct API Access)

This implementation overrides the enhanced_agent.py file to use the google/gemini-2.5-flash-preview-05-20 model
via direct OpenRouter API requests instead of using litellm or other libraries.
"""

import os
import json
import logging
import requests
from typing import List, Dict, Any, Optional, Union
from dotenv import load_dotenv
from src.enhanced_agent import EnhancedAgent
from smolagents import Tool, CodeAgent, HfApiModel

# Load environment variables from config/.env
load_dotenv("config/.env")

# Configure logging
logger = logging.getLogger("CustomAgentDirect")

class DirectOpenRouterModel:
    """Direct implementation of a model that calls OpenRouter API."""
    
    def __init__(self, api_key: Optional[str] = None, model_id: str = "google/gemini-2.5-flash-preview-05-20"):
        """Initialize the OpenRouter model."""
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable is not set. Please add it to your config/.env file.")
            
        self.model_id = model_id
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        
        logger.info(f"Initialized DirectOpenRouterModel with model: {model_id}")
    
    def __call__(self, messages, **kwargs):
        """Process messages using the OpenRouter API."""
        # Headers for the request
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://huggingface.co",  # Optional
            "X-Title": "CustomGeminiAgent"  # Optional
        }
        
        # Format messages in the expected format if they're not already
        formatted_messages = []
        for msg in messages:
            if isinstance(msg, dict) and "role" in msg and "content" in msg:
                formatted_messages.append(msg)
            elif hasattr(msg, "role") and hasattr(msg, "content"):
                formatted_messages.append({"role": msg.role, "content": msg.content})
            else:
                logger.warning(f"Skipping improperly formatted message: {msg}")
        
        # Request body
        data = {
            "model": self.model_id,
            "messages": formatted_messages,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 1000)
        }
        
        # Remove None values
        data = {k: v for k, v in data.items() if v is not None}
        
        try:
            # Make the API request
            response = requests.post(self.api_url, headers=headers, json=data)
            
            # Check if the request was successful
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                
                # Create a response object compatible with smolagents
                class ResponseObj:
                    def __init__(self, content):
                        self.content = content
                
                return ResponseObj(content)
            else:
                error_msg = f"OpenRouter API Error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                
                # Return error in a compatible format
                class ErrorResponseObj:
                    def __init__(self, error):
                        self.content = f"Error: {error}"
                
                return ErrorResponseObj(error_msg)
                
        except Exception as e:
            logger.error(f"Exception calling OpenRouter API: {str(e)}")
            
            # Return error in a compatible format
            class ErrorResponseObj:
                def __init__(self, error):
                    self.content = f"Error: {error}"
            
            return ErrorResponseObj(str(e))

class GeminiAgentDirect(EnhancedAgent):
    """
    Custom agent implementation that uses direct OpenRouter API calls for Gemini.
    """
    
    def _initialize_model(self):
        """
        Override the default model initialization to use direct OpenRouter API calls.
        """
        logger.info("Initializing DirectOpenRouterModel with google/gemini-2.5-flash-preview-05-20")
        
        # Get OpenRouter API key from environment
        openrouter_api_key = os.environ.get("OPENROUTER_API_KEY")
        if not openrouter_api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable is not set. Please add it to your config/.env file.")
            
        # Use our direct OpenRouter model implementation
        model = DirectOpenRouterModel(
            api_key=openrouter_api_key,
            model_id="google/gemini-2.5-flash-preview-05-20"
        )
        
        return model
    
    def _initialize_agent(self, **kwargs):
        """
        Initialize the CodeAgent with optimized settings for Gemini.
        """
        # Default additional authorized imports
        additional_authorized_imports = [
            "math", "random", "datetime", "time", "re", "json", 
            "collections", "itertools", "functools", "operator",
            "string", "copy", "textwrap", "calendar", "fractions",
            "statistics", "decimal", "pathlib", "uuid",
            "os", "sys", "requests", "pandas", "numpy", 
            "csv", "xml", "html"
        ]
        
        # Add any custom imports from kwargs
        if "additional_authorized_imports" in kwargs:
            additional_authorized_imports.extend(kwargs.pop("additional_authorized_imports"))
        
        # Set planning interval for reflection (default to 4 steps for Gemini)
        planning_interval = kwargs.pop("planning_interval", 4)
        
        # Create the agent with Gemini-optimized settings
        return CodeAgent(
            tools=self.tools,
            model=self.model,
            additional_authorized_imports=additional_authorized_imports,
            planning_interval=planning_interval,
            max_steps=self.max_steps,
            temperature=0.4,  # Slightly lower temperature for more focused outputs
            **kwargs
        )

# For direct usage
if __name__ == "__main__":
    try:
        # Create agent instance
        print("Creating GeminiAgentDirect...")
        agent = GeminiAgentDirect()
        
        # Test with a sample query
        query = "What is the capital of France? Answer in one word."
        print(f"Query: {query}")
        
        result = agent(query)
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error: {str(e)}") 