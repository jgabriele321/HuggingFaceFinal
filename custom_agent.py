#!/usr/bin/env python3
"""
Custom Agent Implementation with OpenRouter Gemini Model

This implementation overrides the enhanced_agent.py file to use the google/gemini-2.5-flash-preview-05-20 model
via OpenRouter instead of the default Llama model.
"""

import os
import logging
import functools
from src.enhanced_agent import EnhancedAgent
from smolagents import LiteLLMModel, CodeAgent
from dotenv import load_dotenv

# Load environment variables from config/.env
load_dotenv("config/.env")

# Configure logging
logger = logging.getLogger("CustomAgent")

# Create a custom model class that properly displays the model name
class OpenRouterGeminiModel(LiteLLMModel):
    """Custom model class that properly displays the Gemini model name in the UI."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._display_name = "google/gemini-2.5-flash-preview-05-20"
    
    def __str__(self):
        return f"OpenRouterModel - {self._display_name}"

class GeminiAgent(EnhancedAgent):
    """
    Custom agent implementation that uses the OpenRouter Gemini model.
    """
    
    def _initialize_model(self):
        """
        Override the default model initialization to use OpenRouter with Gemini.
        """
        logger.info("Initializing OpenRouter with google/gemini-2.5-flash-preview-05-20 model")
        
        # Get OpenRouter API key from environment
        openrouter_api_key = os.environ.get("OPENROUTER_API_KEY")
        if not openrouter_api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable is not set. "
                            "Please set it in your config/.env file.")
        
        # Define model parameters
        model_id = "openrouter/google/gemini-2.5-flash-preview-05-20"
        
        # Create custom OpenRouter model with proper display name
        model = OpenRouterGeminiModel(
            model_id=model_id,
            api_key=openrouter_api_key,
        )
        
        # Print a clear indication that we're using Gemini
        print("\n")
        print("=" * 80)
        print(f"USING OPENROUTER GEMINI MODEL: {model_id}")
        print("=" * 80)
        print("\n")
        
        return model
    
    def run(self, query, **kwargs):
        """
        Override the run method to ensure we're showing the correct model name
        in the display.
        """
        print("\n")
        print("=" * 80)
        print(f"RUNNING WITH OPENROUTER GEMINI MODEL: google/gemini-2.5-flash-preview-05-20")
        print("=" * 80)
        print("\n")
        
        return super().run(query, **kwargs)
    
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
    # Create agent instance
    agent = GeminiAgent()
    
    # Test with a sample query
    result = agent("What is the capital of France?")
    print(f"Result: {result}") 