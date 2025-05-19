#!/usr/bin/env python3
"""
Enhanced SmolAgent Implementation using proper ReAct Framework

This module implements a more robust agent using the ReAct framework from smolagents.
It provides proper tool tracking, thinking steps, and robust error handling.
"""

import os
import json
import logging
import random
import time
import re
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
import inspect

# Import smolagents components
from smolagents import Tool, CodeAgent, HfApiModel

# Configure logging
from config.logging_config import configure_logging
configure_logging()
logger = logging.getLogger("EnhancedAgent")

# Import tools
from src.youtube_tool import get_youtube_tool
from src.duckduckgo_search_tool import get_duckduckgo_search_tool
from src.webpage_tool import get_webpage_tool
from src.python_interpreter_tool import get_python_interpreter_tool
from src.file_handler_tool import get_file_handler_tool

class SmolTool(Tool):
    """Custom Tool class that ensures proper attribute initialization."""
    
    def __init__(self, name: str, description: str, function: callable, parameters: dict):
        """Initialize the tool with required attributes."""
        super().__init__()
        # Set required class attributes
        self.name = name
        self.description = description
        self._function = function
        
        # Convert parameters to the format smolagents expects
        self.inputs = {}
        if "properties" in parameters:
            for param_name, param_info in parameters["properties"].items():
                self.inputs[param_name] = {
                    "type": param_info["type"],
                    "description": param_info["description"]
                }
        else:
            # If no properties, use the parameters directly
            for param_name, param_info in parameters.items():
                self.inputs[param_name] = {
                    "type": param_info.get("type", "string"),
                    "description": param_info.get("description", "")
                }
        
        # Set output type (defaulting to string if not specified)
        self.output_type = "string"
        
        # Create a dynamic forward method with explicit parameter names
        param_names = list(self.inputs.keys())
        param_str = ", ".join(param_names)
        forward_code = f"""def forward(self, {param_str}):
            try:
                return self._function({param_str})
            except Exception as e:
                logger.error(f"Error executing tool {{self.name}}: {{str(e)}}")
                return f"Error: {{str(e)}}"
        """
        
        # Create a new namespace and execute the forward method code
        namespace = {}
        exec(forward_code, globals(), namespace)
        
        # Bind the forward method to this instance
        self.forward = namespace["forward"].__get__(self, SmolTool)

class EnhancedAgent:
    """Enhanced agent with file handling capabilities."""
    
    def __init__(self, 
                 model_id: str = "meta-llama/Llama-3.3-70B-Instruct",
                 hf_token: Optional[str] = None,
                 **kwargs):
        """Initialize the enhanced agent."""
        self.model_id = model_id
        self.hf_token = hf_token
        self.tools = self._initialize_tools()
        self.model = self._initialize_model()
        self.agent = self._initialize_agent(**kwargs)
    
    def _initialize_tools(self) -> List[Tool]:
        """Initialize and return the tools for the agent."""
        tools = []
        tool_names = []
        
        # List of tool initialization functions
        tool_functions = [
            get_file_handler_tool,
            get_youtube_tool,
            get_duckduckgo_search_tool,
            get_webpage_tool,
            get_python_interpreter_tool
        ]
        
        # Initialize each tool with proper error handling
        for tool_func in tool_functions:
            try:
                # Get the tool configuration
                tool_config = tool_func()
                
                # Create a SmolTool instance
                tool = SmolTool(
                    name=tool_config["name"],
                    description=tool_config["description"],
                    function=tool_config["function"],
                    parameters=tool_config["parameters"]
                )
                tools.append(tool)
                tool_names.append(tool.name)
                logger.info(f"Successfully initialized tool: {tool.name}")
            except Exception as e:
                logger.error(f"Error initializing tool {tool_func.__name__}: {str(e)}")
        
        logger.info(f"Initialized {len(tools)} tools: {', '.join(tool_names)}")
        return tools
    
    def _initialize_model(self) -> HfApiModel:
        """Initialize the model for the agent."""
        return HfApiModel(
            model_id=self.model_id,
            token=self.hf_token
        )
    
    def _initialize_agent(self, **kwargs) -> CodeAgent:
        """Initialize the CodeAgent with tools and model."""
        return CodeAgent(
            tools=self.tools,
            model=self.model,
            **kwargs
        )
    
    def run(self, task: str) -> str:
        """Run the agent on a task."""
        return self.agent.run(task)

    def __call__(self, query: str, file_path: Optional[str] = None, file_name: Optional[str] = None, task_id: Optional[str] = None) -> str:
        """
        Process a query and return a response.
        
        Args:
            query: The query to process
            file_path: Optional file path for file-based queries
            file_name: Alternative file path (for compatibility)
            task_id: Optional task ID for tracking
            
        Returns:
            The agent's response
        """
        logger.info(f"Processing query: {query}")
        
        # Handle file-based query
        file_context = ""
        if task_id and (file_name or file_path):
            filename = file_name or os.path.basename(file_path)
            try:
                # Use the file handler tool to process the file
                file_info = self.tools[0].function(task_id=task_id, filename=filename)
                if "error" not in file_info:
                    file_type = file_info.get("type", "unknown")
                    if file_type == "text":
                        file_context = f"\nFile Content:\n```\n{file_info['content']}\n```"
                    elif file_type == "image":
                        file_context = f"\nImage Information: Size={file_info['size']}, Mode={file_info['mode']}, Format={file_info['format']}"
                    elif file_type == "excel":
                        file_context = f"\nExcel Data: {len(file_info['rows'])} rows, Columns={', '.join(file_info['columns'])}"
                    elif file_type == "audio":
                        file_context = f"\nAudio File: Size={file_info['size']} bytes"
                else:
                    logger.warning(f"Error processing file: {file_info['error']}")
                    file_context = f"\nFile Error: {file_info['error']}"
            except Exception as e:
                logger.error(f"Error handling file: {str(e)}")
                file_context = f"\nFile Processing Error: {str(e)}"
        
        # Enhance query with file context and tool information
        tool_descriptions = "\n".join([f"- {tool.name}: {tool.description}" for tool in self.tools])
        enhanced_query = f"""
Query: {query}{file_context}

Available Tools:
{tool_descriptions}

Instructions:
1. If working with files, use the file_handler tool first to access file contents
2. For web searches, use the duckduckgo_search tool
3. For webpage content, use the webpage_tool
4. For YouTube videos, use the youtube_tool
5. For calculations or data processing, use the python_interpreter tool

Please process the query and provide a clear, concise answer.
"""
        
        try:
            # Use the agent to process the query
            result = self.agent.run(enhanced_query)
            
            # Post-process the result
            processed_result = self._post_process_result(result, query)
            return processed_result
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return f"I encountered an error: {str(e)}. Please try again."
    
    def _post_process_result(self, result: str, original_query: str) -> str:
        """Post-process the result from the agent."""
        if not isinstance(result, str):
            return str(result)
            
        if not result or result.isspace():
            return "The model did not provide a response."
        
        # Extract final answer if present
        final_answer_match = re.search(r'(?:Final Answer|Answer):\s*(.+?)(?:\n|$)', result, re.IGNORECASE | re.DOTALL)
        if final_answer_match:
            return final_answer_match.group(1).strip()
        
        # Handle specific query types
        if 'chess' in original_query.lower():
            move_pattern = r'\b[KQRBN]?[a-h]?[1-8]?x?[a-h][1-8](?:=[QRBN])?\+?\#?\b'
            moves = re.findall(move_pattern, result)
            if moves:
                return moves[0]
        
        return result.strip() 