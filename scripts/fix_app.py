#!/usr/bin/env python3
"""
Fix App Script

This script patches the app.py file to use the agent_adapter module
instead of directly importing from agent, making it compatible with
both OpenRouter and OpenAI implementations.
"""

import os
import re
import sys
import shutil
import logging
from pathlib import Path
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("FixApp")

def patch_app_file(app_file="app.py", backup=True, force=False):
    """
    Patch the app.py file to use the agent_adapter module.
    
    Args:
        app_file: Path to the app.py file
        backup: Whether to create a backup of the original file
        force: Whether to force patching even if already patched
        
    Returns:
        True if patching was successful, False otherwise
    """
    if not Path(app_file).exists():
        logger.error(f"❌ {app_file} not found")
        return False
    
    # Check if agent_adapter.py exists
    if not Path("agent_adapter.py").exists():
        logger.error("❌ agent_adapter.py not found. Run the installation first.")
        return False
    
    # Create backup
    if backup:
        backup_file = f"{app_file}.bak"
        logger.info(f"Creating backup of {app_file} to {backup_file}")
        shutil.copy2(app_file, backup_file)
    
    # Read the app file
    with open(app_file, "r") as f:
        content = f.read()
    
    # Check if already patched
    if "from agent_adapter import SmolAgent" in content and not force:
        logger.info(f"✅ {app_file} already patched")
        return True
    
    # Replace import statement
    patterns = [
        r"from agent import SmolAgent",
        r"from agent import \*",
        r"import agent"
    ]
    
    replacement = "from agent_adapter import SmolAgent"
    original_content = content
    
    for pattern in patterns:
        content = re.sub(pattern, replacement, content)
    
    if content == original_content and not force:
        logger.warning(f"⚠️ Could not identify import pattern in {app_file}")
        logger.info("Searching for other potential import patterns...")
        
        # Additional patterns to look for
        alt_patterns = [
            r"from\s+agent\s+import",
            r"import\s+agent\s+as",
            r"import\s+agent"
        ]
        
        found = False
        for pattern in alt_patterns:
            matches = re.findall(pattern, original_content)
            if matches:
                found = True
                logger.info(f"Found import pattern: {matches[0]}")
                break
        
        if not found:
            logger.error(f"❌ Could not find agent import in {app_file}")
            return False
    
    # Write patched content back to file
    with open(app_file, "w") as f:
        f.write(content)
    
    logger.info(f"✅ Successfully patched {app_file}")
    return True

def main():
    parser = argparse.ArgumentParser(description="Patch app.py to use agent_adapter")
    parser.add_argument("--file", default="app.py", help="Path to the app.py file")
    parser.add_argument("--no-backup", action="store_true", help="Do not create backup file")
    parser.add_argument("--force", action="store_true", help="Force patching even if already patched")
    
    args = parser.parse_args()
    
    if patch_app_file(args.file, not args.no_backup, args.force):
        logger.info("🎉 Successfully patched app file")
        logger.info("You can now run your app normally and it will use the chosen implementation")
        return 0
    else:
        logger.error("❌ Failed to patch app file")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 