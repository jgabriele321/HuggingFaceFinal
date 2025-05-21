#!/usr/bin/env python3
"""
Test script to use the google/gemini-2.5-flash-preview-05-20 model via OpenRouter
"""

import os
from dotenv import load_dotenv
from src.enhanced_agent import EnhancedAgent
from smolagents import LiteLLMModel

# Load environment variables from config/.env file
load_dotenv("config/.env")

# Create a custom agent class that overrides the model initialization
class GeminiAgent(EnhancedAgent):
    def _initialize_model(self):
        """Initialize the model for the agent using OpenRouter with Gemini."""
        print("Initializing model: google/gemini-2.5-flash-preview-05-20 via OpenRouter")
        
        # Get OpenRouter API key from environment
        openrouter_api_key = os.environ.get("OPENROUTER_API_KEY")
        if not openrouter_api_key:
            # You need to replace 'your_actual_api_key_here' with your real API key
            # or set it in the config/.env file
            print("WARNING: Using hardcoded placeholder API key - REPLACE WITH YOUR ACTUAL KEY!")
            print("Make sure the OPENROUTER_API_KEY is set in config/.env file")
            openrouter_api_key = "your_actual_api_key_here"
            
        # Use LiteLLMModel for OpenRouter access
        model = LiteLLMModel(
            model_id="google/gemini-2.5-flash-preview-05-20",
            api_key=openrouter_api_key,
            base_url="https://openrouter.ai/api/v1"
        )
        return model

def main():
    """Main function to test the GeminiAgent."""
    try:
        print("Creating GeminiAgent...")
        agent = GeminiAgent()
        
        print("\n--- Testing with a simple question ---")
        query = "What is the capital of France? Answer in one word."
        print(f"Query: {query}")
        
        result = agent(query)
        print(f"Result: {result}")
        
        print("\n--- Testing completed successfully ---")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main() 