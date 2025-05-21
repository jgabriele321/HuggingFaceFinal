#!/usr/bin/env python3
"""
Standardized Error Handling Framework for SmolAgent

This module provides a consistent error handling and recovery framework
for all tools in the SmolAgent system.
"""

import logging
import time
import traceback
from typing import Dict, Any, Optional, Callable, List, Union
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ErrorHandler")

class ErrorCategory(Enum):
    """Categories of errors for better grouping and handling."""
    NETWORK = "network_error"
    FILE = "file_error"
    PARSING = "parsing_error"
    PERMISSION = "permission_error"
    TIMEOUT = "timeout_error"
    VALUE = "value_error"
    INITIALIZATION = "initialization_error"
    UNKNOWN = "unknown_error"

class ErrorHandler:
    """
    Standardized error handling and recovery framework.
    
    This class provides consistent error handling, retry mechanisms,
    and recovery strategies for different error categories.
    """
    
    def __init__(self):
        """Initialize the error handler."""
        # Default retry settings
        self.max_retries = 3
        self.initial_backoff = 1.0  # seconds
        self.backoff_factor = 2.0
        self.max_backoff = 15.0  # seconds
        
        # Register known error types with their categories
        self.error_types = {
            "ConnectionError": ErrorCategory.NETWORK,
            "TimeoutError": ErrorCategory.TIMEOUT,
            "ConnectionRefusedError": ErrorCategory.NETWORK,
            "ConnectionResetError": ErrorCategory.NETWORK,
            "FileNotFoundError": ErrorCategory.FILE,
            "PermissionError": ErrorCategory.PERMISSION,
            "JSONDecodeError": ErrorCategory.PARSING,
            "ValueError": ErrorCategory.VALUE,
            "TypeError": ErrorCategory.VALUE,
        }
    
    def categorize_error(self, error: Exception) -> ErrorCategory:
        """
        Categorize an error based on its type.
        
        Args:
            error: The exception to categorize
            
        Returns:
            ErrorCategory enum value
        """
        error_type = type(error).__name__
        
        # Look up the category for this error type
        if error_type in self.error_types:
            return self.error_types[error_type]
            
        # Check for known patterns in the error message
        error_msg = str(error).lower()
        
        if any(term in error_msg for term in ["timeout", "timed out"]):
            return ErrorCategory.TIMEOUT
        elif any(term in error_msg for term in ["network", "connection", "connect"]):
            return ErrorCategory.NETWORK
        elif any(term in error_msg for term in ["file", "path", "directory"]):
            return ErrorCategory.FILE
        elif any(term in error_msg for term in ["parse", "syntax", "format"]):
            return ErrorCategory.PARSING
        elif any(term in error_msg for term in ["permission", "access", "denied"]):
            return ErrorCategory.PERMISSION
        elif any(term in error_msg for term in ["value", "type", "argument"]):
            return ErrorCategory.VALUE
        elif any(term in error_msg for term in ["initialize", "setup", "configure"]):
            return ErrorCategory.INITIALIZATION
            
        # Default to unknown
        return ErrorCategory.UNKNOWN
    
    def format_error(self, error: Exception, tool_name: str = None) -> Dict[str, Any]:
        """
        Format an error into a standardized structure.
        
        Args:
            error: The exception to format
            tool_name: Optional name of the tool that raised the error
            
        Returns:
            Structured error information
        """
        # Get error category
        category = self.categorize_error(error)
        
        # Create structured error information
        error_info = {
            "error": True,
            "category": category.value,
            "message": str(error),
            "type": type(error).__name__,
            "tool": tool_name,
            "timestamp": time.time(),
            "traceback": traceback.format_exc(),
            "recoverable": self._is_recoverable(category)
        }
        
        return error_info
    
    def _is_recoverable(self, category: ErrorCategory) -> bool:
        """
        Determine if an error category is potentially recoverable.
        
        Args:
            category: The error category
            
        Returns:
            True if the error might be recoverable, False otherwise
        """
        # Network and timeout errors are often transient
        if category in [ErrorCategory.NETWORK, ErrorCategory.TIMEOUT]:
            return True
            
        # Parsing errors might be recoverable with different inputs
        if category == ErrorCategory.PARSING:
            return True
            
        # Value errors might be fixable with different inputs
        if category == ErrorCategory.VALUE:
            return True
            
        # File errors and permission errors are less likely to be recoverable
        if category in [ErrorCategory.FILE, ErrorCategory.PERMISSION]:
            return False
            
        # Default to True to encourage retry attempts
        return True
    
    def with_retry(self, func: Callable, *args, 
                  max_retries: int = None, 
                  tool_name: str = None, 
                  **kwargs) -> Any:
        """
        Execute a function with automatic retry on failure.
        
        Args:
            func: The function to call
            *args: Positional arguments to pass to the function
            max_retries: Maximum number of retries (defaults to self.max_retries)
            tool_name: Name of the tool for error reporting
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            The function result or error information dictionary
        """
        if max_retries is None:
            max_retries = self.max_retries
            
        retry_count = 0
        last_error = None
        backoff = self.initial_backoff
        
        while retry_count <= max_retries:
            try:
                # Attempt to call the function
                return func(*args, **kwargs)
            except Exception as e:
                last_error = e
                
                # Format the error
                error_info = self.format_error(e, tool_name)
                
                # Check if the error is potentially recoverable
                if not error_info["recoverable"]:
                    logger.warning(f"Non-recoverable error in {tool_name}: {str(e)}")
                    break
                    
                # If we've reached max retries, stop
                if retry_count >= max_retries:
                    logger.warning(f"Max retries ({max_retries}) reached for {tool_name}")
                    break
                    
                # Calculate backoff time with exponential backoff
                backoff = min(backoff * self.backoff_factor, self.max_backoff)
                
                # Log retry attempt
                logger.info(f"Retry {retry_count+1}/{max_retries} for {tool_name} after {backoff:.2f}s")
                
                # Wait before retrying
                time.sleep(backoff)
                
                # Increment retry counter
                retry_count += 1
        
        # If we get here, all retries failed
        return self.format_error(last_error, tool_name)
    
    def get_fallback_response(self, error_info: Dict[str, Any], tool_name: str) -> Dict[str, Any]:
        """
        Generate a fallback response based on the tool and error information.
        
        Args:
            error_info: The formatted error information
            tool_name: The name of the tool that failed
            
        Returns:
            A fallback response appropriate for the tool
        """
        category = error_info["category"]
        
        # Customize fallback responses based on tool and error category
        if tool_name == "web_search":
            if category == ErrorCategory.NETWORK.value:
                return {"error": "Search temporarily unavailable due to network issues. Please try again later."}
            elif category == ErrorCategory.TIMEOUT.value:
                return {"error": "Search timed out. Please try a more specific query."}
            else:
                return {"error": f"Search error: {error_info['message']}"}
                
        elif tool_name == "youtube":
            if category == ErrorCategory.NETWORK.value:
                return {"error": "YouTube content temporarily unavailable due to network issues."}
            elif category == ErrorCategory.PARSING.value:
                return {"error": "Could not extract information from the YouTube video."}
            else:
                return {"error": f"YouTube error: {error_info['message']}"}
                
        elif tool_name == "python":
            return {"error": f"Code execution error: {error_info['message']}"}
            
        elif tool_name == "file_handler":
            if category == ErrorCategory.FILE.value:
                return {"error": "File not found or cannot be accessed."}
            else:
                return {"error": f"File processing error: {error_info['message']}"}
                
        # Generic fallback for unknown tools
        return {"error": f"Operation failed: {error_info['message']}"}
    
    @staticmethod
    def wrap_tool_execution(tool_func: Callable) -> Callable:
        """
        Decorator to wrap tool execution with standardized error handling.
        
        Args:
            tool_func: The tool function to wrap
            
        Returns:
            Wrapped function with error handling
        """
        handler = ErrorHandler()
        
        def wrapper(*args, **kwargs):
            tool_name = getattr(tool_func, "__name__", "unknown_tool")
            try:
                return handler.with_retry(tool_func, *args, tool_name=tool_name, **kwargs)
            except Exception as e:
                error_info = handler.format_error(e, tool_name)
                return handler.get_fallback_response(error_info, tool_name)
                
        return wrapper

# Create a singleton instance for global use
error_handler = ErrorHandler()

def handle_error(error: Exception, tool_name: str = None) -> Dict[str, Any]:
    """
    Format and handle an error using the global error handler.
    
    Args:
        error: The exception to handle
        tool_name: Optional name of the tool that raised the error
        
    Returns:
        Formatted error information
    """
    return error_handler.format_error(error, tool_name)

def with_error_handling(tool_name: str = None) -> Callable:
    """
    Decorator to add error handling to a function.
    
    Args:
        tool_name: Name of the tool for error reporting
        
    Returns:
        Decorator function
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            nonlocal tool_name
            if tool_name is None:
                tool_name = func.__name__
            return error_handler.with_retry(func, *args, tool_name=tool_name, **kwargs)
        return wrapper
    return decorator 