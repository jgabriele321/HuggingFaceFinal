#!/usr/bin/env python3
"""
Direct OpenRouter API test script for Gemini 2.5 Flash Preview model.

This script makes a direct API call to OpenRouter to test using the Gemini model
without any wrappers or libraries in between.
"""

import os
import json
import requests
from dotenv import load_dotenv

# Load environment variables from config/.env file
load_dotenv("config/.env")

# Get API key
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    print("ERROR: OPENROUTER_API_KEY not found in environment variables")
    print("Please make sure it's set in config/.env file")
    exit(1)

print(f"Using OpenRouter API key: {OPENROUTER_API_KEY[:5]}...{OPENROUTER_API_KEY[-4:]}")

# Set the API endpoint and headers
API_URL = "https://openrouter.ai/api/v1/chat/completions"
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "HTTP-Referer": "https://huggingface.co/spaces",  # Optional for quotas
    "X-Title": "Test App"  # Optional
}

def call_gemini_model(prompt, model="google/gemini-2.5-flash-preview-05-20"):
    """
    Make a direct API call to the specified model via OpenRouter.
    
    Args:
        prompt: The user prompt to send to the model
        model: The model ID to use
        
    Returns:
        The model's response text
    """
    data = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    
    print(f"Sending request to model: {model}")
    print(f"Prompt: {prompt}")
    
    try:
        response = requests.post(API_URL, headers=HEADERS, json=data)
        
        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            model_used = result.get("model", model)
            
            print(f"Successfully received response from {model_used}")
            
            if "usage" in result:
                print(f"Token usage: {json.dumps(result['usage'])}")
                
            return content
        else:
            print(f"Error {response.status_code}: {response.text}")
            return f"Error {response.status_code}: {response.text}"
    
    except Exception as e:
        print(f"Exception: {str(e)}")
        return f"Exception: {str(e)}"

def main():
    """Run a series of test queries with the Gemini model."""
    
    # Test queries
    test_queries = [
        "What is the capital of France? Answer in one word.",
        "List the first 5 Fibonacci numbers.",
        "Write a haiku about artificial intelligence."
    ]
    
    print("\n=== Testing OpenRouter with google/gemini-2.5-flash-preview-05-20 ===\n")
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n--- Test Query {i} ---")
        response = call_gemini_model(query)
        print(f"\nResponse: {response}")
        print("-" * 60)
    
    print("\n=== Testing complete ===")

if __name__ == "__main__":
    main() 