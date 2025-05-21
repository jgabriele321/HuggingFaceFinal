#!/usr/bin/env python3
"""
Run the application with the custom Gemini agent implementation.

This script is a wrapper around app.py that replaces the default agent with our custom
GeminiAgent that uses the OpenRouter Gemini model.
"""

import os
import sys
import importlib
from dotenv import load_dotenv

# Load environment variables from config/.env file
load_dotenv("config/.env")

# Import the custom agent
from custom_agent import GeminiAgent

# Check if OpenRouter API key is set
if not os.environ.get("OPENROUTER_API_KEY"):
    print("ERROR: OPENROUTER_API_KEY environment variable is not set.")
    print("Please set it in your config/.env file.")
    print("Example: OPENROUTER_API_KEY=your_api_key_here")
    sys.exit(1)

# Monkey patch the EnhancedAgent class in the app module
try:
    import app
    from src import agent
    
    # Back up the original class for safety
    OriginalEnhancedAgent = agent.EnhancedAgent
    
    # Replace the EnhancedAgent class with our GeminiAgent
    agent.EnhancedAgent = GeminiAgent
    
    print("\n=== Running app with custom Gemini agent ===")
    print("Using model: google/gemini-2.5-flash-preview-05-20 via OpenRouter")
    print("====================================\n")
    
    # Run the app by executing the file directly
    if hasattr(app, 'demo'):
        # Running with Gradio demo
        print("Launching Gradio interface...")
        app.demo.launch(debug=True, share=False)
    else:
        # Fall back to executing app.py directly
        print("Running app.py directly...")
        os.system('python app.py')
    
except ImportError as e:
    print(f"ERROR: Failed to import required modules: {e}")
    print("Make sure you have all dependencies installed.")
    sys.exit(1)
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1) 