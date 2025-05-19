#!/usr/bin/env python3
"""
Debug script for SmolAgent initialization
Provides detailed error tracing for agent initialization issues
"""

import os
import sys
import traceback
import logging

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

# Import required modules
try:
    from src.agent_adapter import SmolAgent
    print("Successfully imported SmolAgent from agent_adapter")
except Exception as e:
    print(f"Error importing SmolAgent: {e}")
    traceback.print_exc()
    sys.exit(1)

def debug_youtube_tool():
    """Debug the YouTube tool initialization."""
    try:
        from src.youtube_tool import YouTubeTool, get_youtube_tool
        print("\nYouTube Tool class definition:")
        print(f"  - Name: {YouTubeTool.name}")
        print(f"  - Description: {YouTubeTool.description}")
        print(f"  - Output type: {YouTubeTool.output_type}")
        print(f"  - Input types: {YouTubeTool.inputs}")
        
        # Try to instantiate the tool
        youtube_tool = get_youtube_tool()
        print("Successfully instantiated YouTubeTool")
        return youtube_tool
    except Exception as e:
        print(f"Error in YouTube tool: {e}")
        traceback.print_exc()
        return None

def debug_tools_initialization():
    """Debug tools initialization process."""
    try:
        print("\nTrying to import tool-related classes from smolagents:")
        from smolagents import (
            CodeAgent, 
            PythonInterpreterTool, 
            FinalAnswerTool,
            DuckDuckGoSearchTool,
            VisitWebpageTool,
            SpeechToTextTool
        )
        print("Successfully imported tools from smolagents")
        
        print("\nInitializing basic tools:")
        # Try creating each tool
        tools = []
        
        try:
            python_tool = PythonInterpreterTool(
                authorized_imports=["os", "json", "re", "math", "pathlib"]
            )
            print("✓ PythonInterpreterTool initialized")
            tools.append(python_tool)
        except Exception as e:
            print(f"✗ Error initializing PythonInterpreterTool: {e}")
            traceback.print_exc()
            
        try:
            final_answer_tool = FinalAnswerTool()
            print("✓ FinalAnswerTool initialized")
            tools.append(final_answer_tool)
        except Exception as e:
            print(f"✗ Error initializing FinalAnswerTool: {e}")
            traceback.print_exc()
            
        try:
            search_tool = DuckDuckGoSearchTool(max_results=5)
            print("✓ DuckDuckGoSearchTool initialized")
            tools.append(search_tool)
        except Exception as e:
            print(f"✗ Error initializing DuckDuckGoSearchTool: {e}")
            traceback.print_exc()
        
        try:
            webpage_tool = VisitWebpageTool()
            print("✓ VisitWebpageTool initialized")
            tools.append(webpage_tool)
        except Exception as e:
            print(f"✗ Error initializing VisitWebpageTool: {e}")
            traceback.print_exc()
        
        try:
            audio_tool = SpeechToTextTool()
            print("✓ SpeechToTextTool initialized")
            tools.append(audio_tool)
        except Exception as e:
            print(f"✗ Error initializing SpeechToTextTool: {e}")
            traceback.print_exc()
            
        # Debug YouTube tool
        youtube_tool = debug_youtube_tool()
        if youtube_tool:
            tools.append(youtube_tool)
            
        print(f"\nSuccessfully initialized {len(tools)} tools")
        return tools
    except Exception as e:
        print(f"Error in tools initialization: {e}")
        traceback.print_exc()
        return []

def main():
    print("=== SmolAgent Debug Script ===")
    
    # Debug tools initialization
    tools = debug_tools_initialization()
    
    # Try to initialize the agent
    try:
        print("\nInitializing SmolAgent...")
        agent = SmolAgent(use_mock=False)
        print("✓ SmolAgent successfully initialized!")
        
        # Test a simple query
        print("\nTesting agent with a simple query:")
        try:
            response = agent("What is 2+2?")
            print(f"Agent response: {response}")
        except Exception as e:
            print(f"Error running test query: {e}")
            traceback.print_exc()
            
    except Exception as e:
        print(f"✗ Error initializing SmolAgent: {e}")
        traceback.print_exc()
        
    print("\n=== Debug complete ===")

if __name__ == "__main__":
    main() 