#!/usr/bin/env python3
"""
Direct Environment Variable Checker
This utility script helps diagnose issues with environment variables.
"""

import os
import sys
from pathlib import Path

def check_env_file(env_path):
    """Check if the env file exists and read its contents"""
    try:
        if env_path.exists():
            print(f"✅ .env file found at: {env_path}")
            
            # Read the file content
            with open(env_path, 'r') as f:
                content = f.read()
            
            # Check for specific keys
            lines = content.split('\n')
            keys_found = []
            
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key = line.split('=')[0].strip()
                        keys_found.append(key)
            
            print(f"Keys found in .env file: {', '.join(keys_found) or 'None'}")
            return True
        else:
            print(f"❌ .env file not found at: {env_path}")
            return False
    except Exception as e:
        print(f"❌ Error reading .env file: {str(e)}")
        return False

def check_env_variables():
    """Check for environment variables directly"""
    # Critical variables to check
    critical_vars = ["OPENROUTER_API_KEY", "OPENAI_API_KEY", "HF_TOKEN", "SMOL_IMPLEMENTATION"]
    
    print("\nEnvironment variables check:")
    for var in critical_vars:
        value = os.environ.get(var)
        if value:
            # Mask the value for security
            masked = value[:4] + "*" * (len(value) - 8) + value[-4:] if len(value) > 8 else "****"
            print(f"✅ {var} = {masked}")
        else:
            print(f"❌ {var} not found in environment")

def main():
    """Main function"""
    print("🔍 Environment Variable Checker 🔍")
    print("="*50)
    
    # Check current directory
    current_dir = Path.cwd()
    print(f"Current directory: {current_dir}")
    
    # Check common env file locations
    env_paths = [
        Path('.env'),  # Current directory
        Path('/Users/giovannigabriele/Documents/Code/HuggingFaceAgent/Final_Assignment_Template/.env'),  # Specific path
        Path('../.env'),  # Parent directory
        Path('~/.env')  # Home directory
    ]
    
    found_any = False
    for path in env_paths:
        resolved_path = path.expanduser().resolve()
        if check_env_file(resolved_path):
            found_any = True
    
    if not found_any:
        print("\n❌ No .env files found in common locations.")
    
    # Check env variables
    check_env_variables()
    
    # Try to load with python-dotenv
    try:
        from dotenv import load_dotenv
        print("\nAttempting to load with python-dotenv:")
        
        for path in env_paths:
            resolved_path = path.expanduser().resolve()
            if resolved_path.exists():
                print(f"Loading {resolved_path}...")
                success = load_dotenv(dotenv_path=resolved_path, override=True)
                print(f"{'✅ Loaded successfully' if success else '❌ Failed to load'}")
                
                # Check if variables were loaded
                if success:
                    check_env_variables()
    except ImportError:
        print("❌ python-dotenv not installed. Please install with: pip install python-dotenv")

if __name__ == "__main__":
    main() 