#!/usr/bin/env python3
"""
Diagnostic script to test the fix for the file_handler tool error.

This script verifies that the SmolTool class now correctly handles direct access
to the function attribute which was previously missing.
"""

import logging
import os
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("fix-tester")

# Add the current directory to the path to ensure imports work correctly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import necessary modules
from src.agent import SmolTool, EnhancedAgent
from src.file_handler_tool import get_file_handler_tool

def test_function_property():
    """Test that the function property works correctly."""
    logger.info("Testing SmolTool function property...")
    
    # Get a file handler tool configuration
    tool_config = get_file_handler_tool()
    
    # Create a SmolTool instance
    tool = SmolTool(
        name=tool_config["name"],
        description=tool_config["description"],
        function=tool_config["function"],
        parameters=tool_config["parameters"]
    )
    
    # Verify that both attributes now work
    try:
        # Check internal _function attribute (should always have worked)
        if tool._function is not None:
            logger.info("✓ Internal _function attribute is accessible")
        else:
            logger.error("✗ Internal _function attribute is None")
            
        # Check new function property (previously would have failed)
        if tool.function is not None:
            logger.info("✓ function property is accessible")
            logger.info("✓ function property and _function are the same: %s", tool.function is tool._function)
        else:
            logger.error("✗ function property is None")
    except Exception as e:
        logger.error(f"✗ Error testing function property: {e}")
        
    return tool.function is not None

def test_file_handler_with_agent():
    """Test the file handler tool in the agent context."""
    logger.info("Testing file handler in agent context...")
    
    # Initialize the agent
    agent = EnhancedAgent()
    
    # Create a test image file
    test_file_path = "test_image.txt"
    with open(test_file_path, "w") as f:
        f.write("This is a test file for the file handler.")
    
    try:
        # Test accessing the function attribute directly
        file_handler_func = agent.tools[0].function
        logger.info(f"✓ Successfully accessed agent.tools[0].function: {file_handler_func.__name__ if hasattr(file_handler_func, '__name__') else 'unnamed'}")
        
        # Test the agent's call method with a file (which internally uses tools[0].function)
        result = agent("What is in this file?", file_path=test_file_path, task_id="test")
        logger.info(f"Agent response: {result}")
        logger.info("✓ Agent call method executed without function attribute error")
        return True
    except Exception as e:
        logger.error(f"✗ Error during agent test: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Clean up the test file
        if os.path.exists(test_file_path):
            os.remove(test_file_path)

if __name__ == "__main__":
    logger.info("=== Testing SmolTool function property fix ===")
    
    property_success = test_function_property()
    agent_success = test_file_handler_with_agent()
    
    if property_success and agent_success:
        logger.info("✅ All tests passed! The fix for the function property is working correctly.")
    else:
        logger.error("❌ Some tests failed. The fix may not be working completely.") 