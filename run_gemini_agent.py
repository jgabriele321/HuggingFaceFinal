#!/usr/bin/env python3
"""
Run the application with the custom Gemini agent implementation.

This script is a wrapper around app.py that replaces the default agent with our custom
GeminiAgent that uses the OpenRouter Gemini model.

Usage:
    python run_gemini_agent.py [question_limit]

    question_limit: Optional integer that limits the number of questions to process.
"""

import os
import sys
import json
import importlib
import argparse
from typing import Dict, Any, Optional, Tuple
from dotenv import load_dotenv

# Load environment variables from config/.env file
load_dotenv("config/.env")

# Import the custom agent
from custom_agent import GeminiAgent

# Parse command line arguments
parser = argparse.ArgumentParser(description='Run Gemini agent with optional question limit')
parser.add_argument('question_limit', type=int, nargs='?', default=None, 
                    help='Limit the number of questions to process')
args = parser.parse_args()

# Check if OpenRouter API key is set
if not os.environ.get("OPENROUTER_API_KEY"):
    print("Error: OPENROUTER_API_KEY environment variable is not set")
    print("Please set it in config/.env file")
    sys.exit(1)
    
# Check if Serper API key is set
if not os.environ.get("SERPER_API_KEY"):
    print("Warning: SERPER_API_KEY environment variable is not set")
    print("Web search functionality will be limited")
    print("Please set it in config/.env file for full functionality")

# The most direct approach: Completely replace requests.get
# This guarantees that we can control exactly how many questions are returned
import requests
from unittest.mock import MagicMock

# Save the original get function
original_get = requests.get

# Create a custom response function for the questions endpoint
def get_limited_questions(url, **kwargs):
    if "questions" in url:
        print(f"\n{'='*80}")
        print(f"INTERCEPTING QUESTIONS REQUEST")
        
        # First get all the questions (we need to see what's available)
        real_response = original_get(url, **kwargs)
        
        if real_response.status_code == 200:
            # Get all questions
            all_questions = real_response.json()
            total_questions = len(all_questions)
            
            # Determine how many questions to return
            limit = args.question_limit if args.question_limit is not None else total_questions
            limit = min(limit, total_questions)
            
            # Take only the first 'limit' questions
            limited_questions = all_questions[:limit]
            
            print(f"QUESTION LIMIT ACTIVE: Processing only {limit} out of {total_questions} questions")
            print(f"{'='*80}\n")
            
            # Create a mock response with our limited questions
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json = lambda: limited_questions
            mock_response._content = json.dumps(limited_questions).encode('utf-8')
            mock_response.text = json.dumps(limited_questions)
            mock_response.raise_for_status = lambda: None
            
            return mock_response
        
    # For all other URLs, use the original get function
    return original_get(url, **kwargs)

# Replace the original get function with our custom one
# This is the key to making this approach work reliably
requests.get = get_limited_questions

# Import app.py module AFTER we've patched requests.get
spec = importlib.util.spec_from_file_location("app", "app.py")
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)

# Replace the default agent with our custom agent
app.agent = GeminiAgent()

# Print startup banner
print("\n=== Running app with custom Gemini agent ===")
print(f"Using model: google/gemini-2.5-flash-preview-05-20 via OpenRouter")
if args.question_limit:
    print(f"Question limit: {args.question_limit}")
print("====================================\n")

# Start the application
print("Launching Gradio interface...")
app.demo.launch() 