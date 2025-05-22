#!/usr/bin/env python3
"""
Test script to verify Serper API integration works with the configured API key.
"""

import os
import json
import requests
from dotenv import load_dotenv

# Load environment variables from config/.env
load_dotenv("config/.env")

def test_serper_api():
    """Test the Serper API with the configured API key."""
    # Get API key from environment
    serper_api_key = os.environ.get("SERPER_API_KEY")
    
    if not serper_api_key:
        print("Error: SERPER_API_KEY environment variable is not set.")
        return False
    
    print(f"API Key found: {serper_api_key[:4]}...{serper_api_key[-4:]}")
    
    # Define search parameters
    url = "https://google.serper.dev/search"
    payload = json.dumps({
        "q": "Mercedes Sosa discography",
        "num": 5
    })
    headers = {
        'X-API-KEY': serper_api_key,
        'Content-Type': 'application/json'
    }
    
    # Perform search request
    print("Sending request to Serper API...")
    try:
        response = requests.post(url, headers=headers, data=payload)
        
        # Check if request was successful
        if response.status_code == 200:
            print(f"Success! Status code: {response.status_code}")
            data = response.json()
            
            # Print the number of results
            organic_results = data.get("organic", [])
            print(f"Retrieved {len(organic_results)} organic search results")
            
            # Print first result title as verification
            if organic_results:
                print(f"First result title: {organic_results[0].get('title', 'No title')}")
                return True
        else:
            print(f"Error: API request failed with status code {response.status_code}")
            print(f"Response: {response.text}")
            return False
    
    except Exception as e:
        print(f"Error making API request: {str(e)}")
        return False

if __name__ == "__main__":
    print("Testing Serper API integration...")
    success = test_serper_api()
    
    if success:
        print("\nSerper API test completed successfully! ✅")
        print("Your API key is correctly configured and working.")
    else:
        print("\nSerper API test failed! ❌")
        print("Please check your API key and network connection.") 