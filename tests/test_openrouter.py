#!/usr/bin/env python3
"""
Simple test script for OpenRouter with Gemini model
"""

import os
from dotenv import load_dotenv
import litellm

# Load environment variables from config/.env
load_dotenv("config/.env")

# Get the OpenRouter API key
api_key = os.environ.get("OPENROUTER_API_KEY")
if not api_key:
    print("WARNING: OPENROUTER_API_KEY not found in environment")
    print("Make sure it exists in config/.env file")
    api_key = "your_actual_api_key_here"  # Replace with your actual key

print(f"Testing OpenRouter with Gemini model")

try:
    # Set up the OpenRouter model - use openrouter/ prefix for litellm
    model_name = "openrouter/google/gemini-2.5-flash-preview-05-20"
    
    # Test a completion
    messages = [{"role": "user", "content": "What is the capital of France? Answer in one word."}]
    
    print(f"Sending request to model: {model_name}")
    
    response = litellm.completion(
        model=model_name,
        messages=messages,
        api_key=api_key,
        api_base="https://openrouter.ai/api/v1"
    )
    
    print("\nResponse:")
    print(f"Content: {response.choices[0].message.content}")
    print(f"Model: {response.model}")
    print(f"Usage: {response.usage}")
    
except Exception as e:
    print(f"Error: {str(e)}") 