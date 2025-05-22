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

# Import final answer processor - Replace with improved processor
# from src.final_answer_processor import FinalAnswerProcessor
from src.improved_answer_processor import ImprovedAnswerProcessor

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
                # Add nullable if present
                if "nullable" in param_info:
                    self.inputs[param_name]["nullable"] = param_info["nullable"]
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
                # Apply pre-processing based on tool type
                {self._get_preprocessing_code(param_names)}
                
                # Call the underlying function
                result = self._function({param_str})
                
                # Apply post-processing based on tool type
                return self._post_process_result(result)
            except Exception as e:
                logger.error(f"Error executing tool {{self.name}}: {{str(e)}}")
                return self._handle_tool_error(e)
        """
        
        # Create a new namespace and execute the forward method code
        namespace = {}
        exec(forward_code, globals(), namespace)
        
        # Bind the forward method to this instance
        self.forward = namespace["forward"].__get__(self, SmolTool)
        
        # Call setup method if it exists in the parent class
        if hasattr(self.__class__, 'setup') and callable(getattr(self.__class__, 'setup')):
            logger.info(f"Calling setup method for tool {self.name}")
            try:
                self.setup()
                # Verify setup was successful by checking for expected attributes
                self._verify_setup()
            except Exception as e:
                logger.error(f"Error during setup of tool {self.name}: {str(e)}")
                # Implement fallback behavior for failed setup
                self._setup_fallback()
    
    @property
    def function(self):
        """Property for backwards compatibility with code that accesses .function directly."""
        return self._function
    
    def _get_preprocessing_code(self, param_names: List[str]) -> str:
        """Generate tool-specific preprocessing code."""
        if not param_names:
            return "pass"
            
        preprocessing_code = []
        
        # Handle specific tools
        if self.name == "python":
            # Add precision handling for Python tool
            if "precision" in param_names:
                preprocessing_code.append("if precision is not None and precision == 2 and 'currency' in code.lower(): precision = 2")
        
        elif self.name == "web_search":
            # Add query normalization
            if "query" in param_names:
                preprocessing_code.append("query = query.strip()")
        
        # If no specific preprocessing, return pass
        if not preprocessing_code:
            return "pass"
            
        return "\n                ".join(preprocessing_code)
    
    def _post_process_result(self, result: Any) -> Any:
        """Apply post-processing to tool results."""
        # Handle None results
        if result is None:
            return "No results found."
            
        # Handle dictionary results with error key
        if isinstance(result, dict) and "error" in result:
            return f"Error: {result['error']}"
            
        # Handle specific tools
        if self.name == "python":
            # Ensure numeric results have consistent formatting
            if isinstance(result, (int, float)):
                # Format currency values with two decimal places
                if isinstance(result, float):
                    return str(result)
                return str(result)
                
        # Default: convert to string if not already
        if not isinstance(result, str):
            return str(result)
            
        return result
    
    def _handle_tool_error(self, error: Exception) -> str:
        """Handle tool errors with appropriate fallbacks."""
        error_type = type(error).__name__
        error_msg = str(error)
        
        # Import error handler if available
        try:
            from src.error_handler import handle_error
            error_info = handle_error(error, self.name)
            return f"Error: {error_info.get('message', error_msg)}"
        except ImportError:
            pass
            
        # Tool-specific error handling
        if self.name == "web_search":
            return f"Search failed: {error_msg}. Try a different search query."
        elif self.name == "youtube":
            return f"YouTube processing failed: {error_msg}. Check the video URL or try another video."
        elif self.name == "python":
            return f"Code execution error: {error_msg}"
        elif self.name == "file_handler":
            return f"File processing error: {error_msg}"
            
        # Generic error message
        return f"Tool execution failed: {error_msg}"
    
    def _verify_setup(self):
        """Verify that setup completed successfully by checking for expected attributes."""
        # For DuckDuckGoSearchTool, check if requests attribute exists
        if self.name == "web_search" and not hasattr(self, "requests"):
            logger.warning(f"Tool {self.name} missing 'requests' attribute after setup")
            self.requests = __import__('requests')
        
        # For YouTubeTool, check if youtube_transcript_api is available
        if self.name == "youtube" and not hasattr(self, "transcript_api"):
            try:
                # Try to import the youtube_transcript_api
                from youtube_transcript_api import YouTubeTranscriptApi
                self.transcript_api = YouTubeTranscriptApi
                logger.info(f"Added transcript_api attribute to {self.name} tool")
            except ImportError:
                logger.warning(f"Tool {self.name} could not import youtube_transcript_api")
                
        # For FileHandlerTool, ensure files directory exists
        if self.name == "file_handler":
            import os
            os.makedirs("files", exist_ok=True)
    
    def _setup_fallback(self):
        """Provide fallback implementation for tools with failed setup."""
        # For DuckDuckGoSearchTool
        if self.name == "web_search":
            import requests
            self.requests = requests
            logger.info(f"Applied fallback setup for {self.name} tool")
        
        # For YouTubeTool, create a minimal fallback implementation
        if self.name == "youtube":
            logger.info(f"Applied fallback setup for {self.name} tool")
            # Create minimal fallbacks for required attributes
            self.requests = __import__('requests')
            # Create a fallback for transcript_api if needed
            
        # For PythonInterpreterTool, ensure default parameters
        if self.name == "python":
            self.timeout_seconds = 10
            self.authorized_imports = [
                "math", "random", "datetime", "re", "json", 
                "collections", "itertools", "functools"
            ]
            logger.info(f"Applied fallback setup for {self.name} tool")

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
        
        # Initialize answer processor - Use the improved processor
        # self.answer_processor = FinalAnswerProcessor()
        self.answer_processor = ImprovedAnswerProcessor()
    
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
                # Attempt to create a minimal fallback tool if initialization fails
                fallback_tool = self._create_fallback_tool(tool_func.__name__)
                if fallback_tool:
                    tools.append(fallback_tool)
                    tool_names.append(fallback_tool.name)
                    logger.info(f"Created fallback for tool: {fallback_tool.name}")
        
        logger.info(f"Initialized {len(tools)} tools: {', '.join(tool_names)}")
        return tools
    
    def _create_fallback_tool(self, tool_name: str) -> Optional[Tool]:
        """Create a minimal fallback tool for a failed initialization."""
        base_name = tool_name.replace("get_", "").replace("_tool", "")
        
        if "file_handler" in base_name:
            return SmolTool(
                name="file_handler",
                description="Basic file handling capabilities (fallback mode)",
                function=lambda **kwargs: {"error": "File handler in fallback mode with limited functionality"},
                parameters={"type": "object", "properties": {"filename": {"type": "string", "description": "File to process"}, "task_id": {"type": "string", "description": "Task ID"}}}
            )
        elif "duckduckgo_search" in base_name or "web_search" in base_name:
            return SmolTool(
                name="web_search",
                description="Web search functionality (fallback mode)",
                function=lambda query, **kwargs: f"The web search tool is in fallback mode. Your query was: {query}",
                parameters={"type": "object", "properties": {"query": {"type": "string", "description": "Search query"}}}
            )
        
        # Add other fallbacks as needed
        return None
    
    def _initialize_model(self) -> HfApiModel:
        """Initialize the model for the agent."""
        return HfApiModel(
            model_id=self.model_id,
            token=self.hf_token
        )
    
    def _initialize_agent(self, **kwargs) -> CodeAgent:
        """Initialize the CodeAgent with tools and model."""
        # Default additional authorized imports based on smolagents recommendations
        additional_authorized_imports = [
            "math", "random", "datetime", "time", "re", "json", 
            "collections", "itertools", "functools", "operator",
            "string", "copy", "textwrap", "calendar", "fractions",
            "statistics", "decimal", "pathlib", "uuid",
            "os", "sys", "requests", "pandas", "numpy", 
            "csv", "xml", "html"
        ]
        
        # Add any custom imports from kwargs
        if "additional_authorized_imports" in kwargs:
            additional_authorized_imports.extend(kwargs.pop("additional_authorized_imports"))
        
        # Set planning interval for reflection (default to 3 steps)
        planning_interval = kwargs.pop("planning_interval", 3)
        
        return CodeAgent(
            tools=self.tools,
            model=self.model,
            additional_authorized_imports=additional_authorized_imports,
            planning_interval=planning_interval,
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
            
            # Process the result with the improved processor
            processed_answer = self.answer_processor.process_answer(query, processed_result, task_id)
            
            return processed_answer
            
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