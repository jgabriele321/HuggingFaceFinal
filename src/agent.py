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

# Import final answer processor - Replace with improved processor
# from src.final_answer_processor import FinalAnswerProcessor
from src.improved_answer_processor import ImprovedAnswerProcessor

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
        
        # Import the actual tool classes directly
        from src.youtube_tool import YouTubeTool
        from src.duckduckgo_search_tool import DuckDuckGoSearchTool
        from src.webpage_tool import WebpageTool
        from src.python_interpreter_tool import PythonInterpreterTool
        from src.file_handler_tool import get_file_handler_tool
        from src.enhanced_wikipedia_tool import EnhancedWikipediaTool
        from src.chess_analysis_tool import ChessAnalysisTool
        
        # Initialize file handler tool using the configuration function
        try:
            logger.info("Initializing file handler tool")
            file_handler_config = get_file_handler_tool()
            
            # Create a proper Tool class for the file handler
            class FileHandlerToolWrapper(Tool):
                name = file_handler_config["name"]
                description = file_handler_config["description"]
                
                inputs = {
                    "task_id": {"type": "string", "description": "The task ID associated with the file"},
                    "filename": {"type": "string", "description": "The name of the file to process"}
                }
                output_type = "string"
                
                def __init__(self):
                    super().__init__()
                    self._function = file_handler_config["function"]
                    
                def forward(self, task_id: str, filename: str):
                    try:
                        result = self._function(task_id=task_id, filename=filename)
                        return str(result) if not isinstance(result, str) else result
                    except Exception as e:
                        logger.error(f"Error in file handler: {str(e)}")
                        return f"Error: File not found: {filename}"
            
            file_tool = FileHandlerToolWrapper()
            tools.append(file_tool)
            tool_names.append("file_handler")
            logger.info("Successfully initialized file handler tool")
            
        except Exception as e:
            logger.error(f"Error initializing file handler tool: {str(e)}")
        
        # List of other tool classes to initialize
        tool_classes = [
            ("youtube", YouTubeTool), 
            ("web_search", DuckDuckGoSearchTool),
            ("visit_webpage", WebpageTool),
            ("python", PythonInterpreterTool),
            ("enhanced_wikipedia", EnhancedWikipediaTool),
            ("chess_analyzer", ChessAnalysisTool)
        ]
        
        # Initialize each tool with proper error handling
        for tool_name, tool_class in tool_classes:
            try:
                # Create tool instance directly
                tool = tool_class()
                
                # Call setup if it exists
                if hasattr(tool, 'setup') and callable(getattr(tool, 'setup')):
                    logger.info(f"Calling setup method for tool {tool_name}")
                    try:
                        tool.setup()
                        logger.info(f"Successfully initialized tool: {tool_name}")
                    except Exception as setup_error:
                        logger.warning(f"Setup failed for tool {tool_name}: {str(setup_error)}")
                        # Continue with tool even if setup fails
                        
                tools.append(tool)
                tool_names.append(tool_name)
                logger.info(f"Successfully initialized tool: {tool_name}")
                
            except Exception as e:
                logger.error(f"Error initializing tool {tool_name}: {str(e)}")
                # Attempt to create a minimal fallback tool if initialization fails
                fallback_tool = self._create_fallback_tool(tool_name)
                if fallback_tool:
                    tools.append(fallback_tool)
                    tool_names.append(fallback_tool.name)
                    logger.info(f"Created fallback for tool: {fallback_tool.name}")
        
        logger.info(f"Initialized {len(tools)} tools: {', '.join(tool_names)}")
        return tools
    
    def _create_fallback_tool(self, tool_name: str) -> Optional[Tool]:
        """Create a minimal fallback tool for a failed initialization."""
        
        if "web_search" in tool_name:
            # Import the minimal search tool implementation directly
            try:
                # Try to re-import the proper tool
                from src.duckduckgo_search_tool import DuckDuckGoSearchTool
                logger.info("Attempting to recreate web search tool")
                tool = DuckDuckGoSearchTool()
                if hasattr(tool, 'setup'):
                    tool.setup()
                return tool
            except Exception as e:
                logger.error(f"Failed to create web search tool: {str(e)}")
                
                # Create a minimal fallback search tool
                class MinimalSearchTool(Tool):
                    name = "web_search"
                    description = "Minimal web search functionality"
                    inputs = {
                        "query": {"type": "string", "description": "Search query"},
                        "num_results": {"type": "integer", "description": "Number of results", "nullable": True}
                    }
                    output_type = "string"
                    
                    def forward(self, query: str, num_results: int = 5) -> str:
                        return self._minimal_web_search(query, num_results=num_results)
                        
                    def _minimal_web_search(self, query: str, **kwargs) -> str:
                        """Minimal web search implementation as last resort fallback."""
                        try:
                            # First, optimize the query similar to the main search tool
                            search_query = self._optimize_search_query(query)
                            logger.info(f"Using optimized search query in fallback: {search_query}")
                            
                            # Now attempt the minimal search
                            import requests
                            from urllib.parse import quote_plus
                            import re
                            
                            # Use the HTML endpoint which is more reliable
                            search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(search_query)}"
                            
                            response = requests.get(search_url, headers={
                                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                            })
                            
                            if response.status_code != 200:
                                return f"Search error: Failed with status code {response.status_code}"
                            
                            # Extract results using simple regex
                            html = response.text
                            
                            # Basic title and snippet extraction
                            titles = re.findall(r'<a class="result__a" href="([^"]+)"[^>]*>(.*?)</a>', html, re.DOTALL)
                            snippets = re.findall(r'<a class="result__snippet"[^>]*>(.*?)</a>', html, re.DOTALL)
                            
                            if not titles:
                                return f"No results found for query: {search_query}"
                            
                            # Format results
                            num_results = min(5, len(titles)) 
                            formatted_results = f"Search results for: {search_query}\n\n"
                            
                            for i in range(num_results):
                                url, title = titles[i] if i < len(titles) else ("", "No title")
                                snippet = snippets[i] if i < len(snippets) else "No description available"
                                
                                # Clean up HTML tags
                                title = re.sub(r'<[^>]+>', '', title)
                                snippet = re.sub(r'<[^>]+>', '', snippet)
                                
                                formatted_results += f"{i+1}. {title.strip()}\n"
                                formatted_results += f"   {snippet.strip()}\n"
                                formatted_results += f"   Source: DuckDuckGo - {url}\n\n"
                            
                            return formatted_results
                            
                        except Exception as e:
                            return f"Search error: {str(e)}"
                            
                    def _optimize_search_query(self, query: str) -> str:
                        """
                        Optimize search queries by adding relevant keywords.
                        This is a copy of the same functionality in DuckDuckGoSearchTool.
                        """
                        # Start with the original query
                        search_query = query
                        
                        # Enhance album discography queries with better search terms
                        if re.search(r'albums?.*between.*\d{4}.*\d{4}', query.lower()):
                            artist_match = re.search(r'(.*?)\s+albums?', query.lower())
                            year_range_match = re.search(r'between\s+(\d{4})\s+and\s+(\d{4})', query.lower())
                            
                            if artist_match and year_range_match:
                                artist = artist_match.group(1).strip()
                                start_year = year_range_match.group(1)
                                end_year = year_range_match.group(2)
                                search_query = f"{artist} studio albums discography between {start_year} and {end_year} wikipedia"
                                
                        # Add wiki terms for factual questions
                        elif any(term in query.lower() for term in ["who", "when", "where", "how many"]):
                            search_query = f"{query} facts wiki"
                            
                        return search_query
                
                return MinimalSearchTool()
        
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
            "csv", "xml", "html", "chess"
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
                file_info = self.tools[0].forward(task_id=task_id, filename=filename)
                
                # Parse the result if it's a string representation of a dict
                if isinstance(file_info, str):
                    try:
                        import json
                        file_info = json.loads(file_info)
                    except:
                        # If it's not JSON, treat as error message
                        file_context = f"\nFile Processing Error: {file_info}"
                        file_info = {"error": file_info}
                
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
6. For Wikipedia research and discography data, use the enhanced_wikipedia_search tool
7. For chess position analysis, use the chess_position_analyzer tool

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