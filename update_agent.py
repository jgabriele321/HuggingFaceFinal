#!/usr/bin/env python3
"""
Update Agent Utility

This script helps users choose between OpenRouter and OpenAI implementations
and integrates them with the existing SmolAgent project.
"""

import os
import argparse
import shutil
import logging
from pathlib import Path
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("UpdateAgent")

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Try to load from .env file in the current directory
    env_path = Path('.env')
    if env_path.exists():
        logger.info(f"Loading environment from {env_path.absolute()}")
        load_dotenv(dotenv_path=env_path)
    else:
        # Try to load from the full path (for the specific case mentioned)
        specific_path = Path('/Users/giovannigabriele/Documents/Code/HuggingFaceAgent/Final_Assignment_Template/.env')
        if specific_path.exists():
            logger.info(f"Loading environment from {specific_path}")
            load_dotenv(dotenv_path=specific_path)
except ImportError:
    logger.warning("Warning: python-dotenv not installed. Environment variables must be set manually.")

def validate_api_keys():
    """Check if required API keys are available."""
    # Check OpenRouter API key
    openrouter_key = os.environ.get("OPENROUTER_API_KEY")
    if not openrouter_key:
        logger.warning("⚠️ OPENROUTER_API_KEY not found in environment variables")
    else:
        logger.info("✅ OPENROUTER_API_KEY is set")
    
    # Check OpenAI API key
    openai_key = os.environ.get("OPENAI_API_KEY")
    if not openai_key:
        logger.warning("⚠️ OPENAI_API_KEY not found in environment variables")
    else:
        logger.info("✅ OPENAI_API_KEY is set")
    
    return openrouter_key is not None, openai_key is not None

def update_with_openrouter(force=False):
    """Update the agent.py file with OpenRouter implementation."""
    # Check if openrouter_agent.py exists
    if not Path("openrouter_agent.py").exists():
        logger.error("❌ openrouter_agent.py not found")
        return False
    
    # Check if agent.py exists
    if Path("agent.py").exists() and not force:
        backup_file = "agent.py.bak"
        logger.info(f"Creating backup of existing agent.py to {backup_file}")
        shutil.copy2("agent.py", backup_file)
    
    # Copy openrouter_agent.py to agent.py
    try:
        # Read openrouter_agent.py
        with open("openrouter_agent.py", "r") as f:
            content = f.read()
        
        # Write to agent.py with module docstring modification
        with open("agent.py", "w") as f:
            f.write('"""\nSmolAgent Implementation using OpenRouter API\n\nThis is an auto-generated file. Do not edit directly.\n"""\n\n')
            f.write(content)
        
        logger.info("✅ Successfully updated agent.py with OpenRouter implementation")
        return True
    except Exception as e:
        logger.error(f"❌ Error updating agent.py: {str(e)}")
        return False

def update_with_openai(force=False):
    """Update the agent.py file with OpenAI implementation."""
    # Check if openai_agent.py exists
    if not Path("openai_agent.py").exists():
        logger.error("❌ openai_agent.py not found")
        return False
    
    # Check if agent.py exists
    if Path("agent.py").exists() and not force:
        backup_file = "agent.py.bak"
        logger.info(f"Creating backup of existing agent.py to {backup_file}")
        shutil.copy2("agent.py", backup_file)
    
    # Copy openai_agent.py to agent.py
    try:
        # Read openai_agent.py
        with open("openai_agent.py", "r") as f:
            content = f.read()
        
        # Write to agent.py with module docstring modification
        with open("agent.py", "w") as f:
            f.write('"""\nSmolAgent Implementation using OpenAI API\n\nThis is an auto-generated file. Do not edit directly.\n"""\n\n')
            f.write(content)
        
        logger.info("✅ Successfully updated agent.py with OpenAI implementation")
        return True
    except Exception as e:
        logger.error(f"❌ Error updating agent.py: {str(e)}")
        return False

def update_env_file(openrouter_key=None, openai_key=None):
    """Create or update .env file with API keys."""
    env_content = []
    env_path = Path('.env')
    specific_path = Path('/Users/giovannigabriele/Documents/Code/HuggingFaceAgent/Final_Assignment_Template/.env')
    
    # Choose the right path
    if specific_path.exists():
        env_path = specific_path
    
    # Read existing content if file exists
    if env_path.exists():
        try:
            with open(env_path, "r") as f:
                lines = f.readlines()
                
            for line in lines:
                line = line.strip()
                if line and not line.startswith(("OPENROUTER_API_KEY", "OPENAI_API_KEY")):
                    env_content.append(line)
        except Exception as e:
            logger.warning(f"⚠️ Error reading existing .env file: {str(e)}")
    
    # Add API keys if provided
    if openrouter_key:
        env_content.append(f"OPENROUTER_API_KEY={openrouter_key}")
    
    if openai_key:
        env_content.append(f"OPENAI_API_KEY={openai_key}")
    
    # Write back to file
    try:
        with open(env_path, "w") as f:
            for line in env_content:
                f.write(f"{line}\n")
        
        logger.info(f"✅ Successfully updated {env_path}")
        return True
    except Exception as e:
        logger.error(f"❌ Error updating .env file: {str(e)}")
        return False

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Update SmolAgent Implementation")
    parser.add_argument("--implementation", choices=["openrouter", "openai"], 
                        help="Choose implementation: 'openrouter' or 'openai'")
    parser.add_argument("--force", action="store_true", 
                        help="Force update without confirmation")
    parser.add_argument("--openrouter-key", type=str, 
                        help="OpenRouter API key (optional)")
    parser.add_argument("--openai-key", type=str, 
                        help="OpenAI API key (optional)")
    parser.add_argument("--env-file", type=str,
                        help="Path to .env file (optional)")
    
    args = parser.parse_args()
    
    # Check if custom env file path is provided
    if args.env_file and Path(args.env_file).exists():
        try:
            from dotenv import load_dotenv
            logger.info(f"Loading environment from custom path: {args.env_file}")
            load_dotenv(dotenv_path=args.env_file)
        except ImportError:
            logger.warning("Warning: python-dotenv not installed. Cannot load custom env file.")
    
    # Check existing API keys
    has_openrouter, has_openai = validate_api_keys()
    
    # If no implementation specified, guide user based on available keys
    if not args.implementation:
        if has_openrouter and has_openai:
            print("\nBoth OpenRouter and OpenAI API keys are available.")
            print("Please specify which implementation to use:")
            print("1. OpenRouter (Claude 3 Haiku)")
            print("2. OpenAI (GPT-3.5-Turbo)")
            choice = input("Enter choice (1/2): ").strip()
            if choice == "1":
                args.implementation = "openrouter"
            elif choice == "2":
                args.implementation = "openai"
            else:
                logger.error("❌ Invalid choice")
                return 1
        elif has_openrouter:
            logger.info("Only OpenRouter API key found. Using OpenRouter implementation.")
            args.implementation = "openrouter"
        elif has_openai:
            logger.info("Only OpenAI API key found. Using OpenAI implementation.")
            args.implementation = "openai"
        else:
            logger.warning("⚠️ No API keys found. You need to provide at least one.")
            if args.openrouter_key:
                logger.info("Using provided OpenRouter API key")
                args.implementation = "openrouter"
            elif args.openai_key:
                logger.info("Using provided OpenAI API key")
                args.implementation = "openai"
            else:
                print("\nPlease choose an implementation and provide an API key:")
                print("1. OpenRouter (Claude 3 Haiku)")
                print("2. OpenAI (GPT-3.5-Turbo)")
                choice = input("Enter choice (1/2): ").strip()
                if choice == "1":
                    args.implementation = "openrouter"
                    if not args.openrouter_key:
                        args.openrouter_key = input("Enter OpenRouter API key: ").strip()
                elif choice == "2":
                    args.implementation = "openai"
                    if not args.openai_key:
                        args.openai_key = input("Enter OpenAI API key: ").strip()
                else:
                    logger.error("❌ Invalid choice")
                    return 1
    
    # Check if the correct API key is available for the chosen implementation
    if args.implementation == "openrouter" and not (has_openrouter or args.openrouter_key):
        if not args.force:
            print("\nWarning: No OpenRouter API key found.")
            arg_key = input("Enter OpenRouter API key (or press Enter to exit): ").strip()
            if not arg_key:
                logger.error("❌ No OpenRouter API key provided. Exiting.")
                return 1
            args.openrouter_key = arg_key
    
    if args.implementation == "openai" and not (has_openai or args.openai_key):
        if not args.force:
            print("\nWarning: No OpenAI API key found.")
            arg_key = input("Enter OpenAI API key (or press Enter to exit): ").strip()
            if not arg_key:
                logger.error("❌ No OpenAI API key provided. Exiting.")
                return 1
            args.openai_key = arg_key
    
    # Update .env file with API keys if provided
    if args.openrouter_key or args.openai_key:
        update_env_file(args.openrouter_key, args.openai_key)
    
    # Update agent.py with chosen implementation
    if args.implementation == "openrouter":
        if update_with_openrouter(args.force):
            logger.info("🎉 Successfully updated to OpenRouter implementation")
            logger.info("You can now use app.py with OpenRouter")
        else:
            logger.error("❌ Failed to update to OpenRouter implementation")
            return 1
    else:  # openai
        if update_with_openai(args.force):
            logger.info("🎉 Successfully updated to OpenAI implementation")
            logger.info("You can now use app.py with OpenAI")
        else:
            logger.error("❌ Failed to update to OpenAI implementation")
            return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 