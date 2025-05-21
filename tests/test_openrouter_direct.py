#!/usr/bin/env python3
"""
Direct test script for OpenRouter with Gemini model using requests
"""

import os
import json
import requests
from dotenv import load_dotenv

# Load environment variables from config/.env
load_dotenv("config/.env")

# Get the OpenRouter API key
api_key = os.environ.get("OPENROUTER_API_KEY")
if not api_key:
    print("ERROR: OPENROUTER_API_KEY environment variable is not set.")
    print("Please set it in your config/.env file.")
    exit(1)

print(f"API key found: {api_key[:10]}...{api_key[-4:]}")

# OpenRouter API endpoint
api_url = "https://openrouter.ai/api/v1/chat/completions"

# Headers for the request
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}",
    "HTTP-Referer": "https://github.com/yourusername/yourproject",  # Optional
    "X-Title": "Test OpenRouter with Gemini"  # Optional
}

# Request body
data = {
    "model": "google/gemini-2.5-flash-preview-05-20",
    "messages": [
        {"role": "user", "content": "What is the capital of France? Answer in one word."}
    ]
}

print(f"Making request to OpenRouter API with model: {data['model']}")

try:
    # Make the API request
    response = requests.post(api_url, headers=headers, json=data)
    
    # Check if the request was successful
    if response.status_code == 200:
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        model = result.get("model", "Unknown")
        
        print("\nResponse:")
        print(f"Content: {content}")
        print(f"Model: {model}")
        if "usage" in result:
            print(f"Usage: {json.dumps(result['usage'])}")
    else:
        print(f"\nError: {response.status_code}")
        print(f"Response: {response.text}")
        
except Exception as e:
    print(f"\nException: {str(e)}") 