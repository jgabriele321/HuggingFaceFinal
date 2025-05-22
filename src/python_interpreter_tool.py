#!/usr/bin/env python3
"""
Python Interpreter Tool for SmolAgent.

This tool provides functionality to execute Python code securely with enhanced output
formatting and timeout handling.
"""

import re
import io
import sys
import logging
import inspect
import traceback
import signal
import os
import time
import threading
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from contextlib import redirect_stdout, redirect_stderr, contextmanager
from typing import List, Dict, Any, Optional, Set, Union
import ast

from smolagents import Tool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PythonInterpreterTool")

class TimeoutError(Exception):
    """Exception raised when code execution times out."""
    pass

class PythonInterpreterTool(Tool):
    """Tool for executing Python code securely with enhanced output formatting."""
    
    name = "python"
    description = "Execute Python code and return the results with precise formatting and error handling"
    
    inputs = {
        "code": {
            "type": "string",
            "description": "The Python code to execute"
        },
        "precision": {
            "type": "integer",
            "description": "Optional decimal places for numeric outputs",
            "nullable": True
        }
    }
    
    output_type = "string"
    
    def __init__(self, **kwargs):
        """Initialize the tool with secure defaults."""
        super().__init__(**kwargs)
        
        # Default execution timeout (in seconds)
        self.timeout_seconds = kwargs.get("timeout_seconds", 10)
        
        # Define allowed modules that are safe to import
        self.authorized_imports = kwargs.get("authorized_imports", [
            "math", "random", "datetime", "time", "re", "json", 
            "collections", "itertools", "functools", "operator",
            "string", "copy", "textwrap", "calendar", "fractions",
            "statistics", "decimal", "pathlib", "uuid"
        ])
        
        # Potentially risky modules that require careful review
        self.risky_imports = kwargs.get("risky_imports", [
            "os", "sys", "subprocess", "shutil", "socket", "requests",
            "urllib", "http", "ftplib", "telnetlib", "smtplib",
            "email", "poplib", "imaplib", "nntplib", "webbrowser",
            "multiprocessing", "threading", "concurrent", "asyncio"
        ])
        
        # Explicitly forbidden modules
        self.forbidden_imports = kwargs.get("forbidden_imports", [
            "builtins", "__builtin__", "pickle", "shelve", "marshal",
            "cPickle", "dbm", "sqlite3", "zlib", "gzip", "bz2", "zipfile",
            "tarfile", "platform", "ctypes", "crypt", "pwd", "spwd", "signal",
            "mmap", "readline", "rlcompleter", "pty", "popen2", "commands",
            "getpass", "tty", "pdb", "cgitb", "importlib", "pkgutil",
            "runpy", "compileall", "py_compile", "symtable", "pyclbr", "ast"
        ])
    
    @contextmanager
    def _timeout_thread(self, seconds: int):
        """
        Use threading.Timer for timeout instead of signal.
        This works in all threads, not just the main thread.
        
        Args:
            seconds: Timeout in seconds
            
        Yields:
            None
        
        Raises:
            TimeoutError: If the execution times out
        """
        timer_canceled = threading.Event()
        timeout_occurred = threading.Event()
        
        def timeout_handler():
            if not timer_canceled.is_set():
                timeout_occurred.set()
                # Since we can't interrupt the thread directly,
                # we just set a flag which we'll check after execution
        
        timer = threading.Timer(seconds, timeout_handler)
        timer.daemon = True  # Don't let the timer block process exit
        timer.start()
        
        try:
            yield
        finally:
            timer_canceled.set()
            timer.cancel()
            
        # Check if timeout occurred
        if timeout_occurred.is_set():
            raise TimeoutError(f"Code execution timed out after {seconds} seconds")
    
    def _execute_with_timeout(self, func, args=None, kwargs=None, timeout=10):
        """
        Execute a function with a timeout using ThreadPoolExecutor.
        This works in any thread, not just the main thread.
        
        Args:
            func: Function to execute
            args: Arguments to pass to the function
            kwargs: Keyword arguments to pass to the function
            timeout: Timeout in seconds
            
        Returns:
            The result of the function
            
        Raises:
            TimeoutError: If execution times out
            Exception: Any exception raised by the function
        """
        if args is None:
            args = ()
        if kwargs is None:
            kwargs = {}
            
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(func, *args, **kwargs)
            try:
                return future.result(timeout=timeout)
            except FutureTimeoutError:
                # Attempt to cancel the future (doesn't stop the thread but marks it for cancellation)
                future.cancel()
                raise TimeoutError(f"Code execution timed out after {timeout} seconds")
    
    def _capture_output(self, code, timeout=5, precision=None):
        """
        Execute the Python code and capture its output with proper indentation preservation.
        
        Args:
            code: The Python code to execute
            timeout: Maximum execution time in seconds
            precision: Optional decimal precision for numeric outputs
            
        Returns:
            The output of the code execution or an error message
        """
        # Ensure code is properly indented
        code_lines = code.splitlines()
        
        # Check for common indentation errors and fix them
        if len(code_lines) > 1:
            # Check if there are indentation issues that need fixing
            # Keep the code as is, Python's exec will enforce proper indentation
            fixed_code = code
        else:
            fixed_code = code
        
        # Create a clean namespace for execution
        namespace = {'__builtins__': __builtins__.copy()}
        
        # Capture stdout
        output_buffer = io.StringIO()
        
        try:
            # Check for potentially harmful imports
            self._check_imports(fixed_code)
            
            # Create a modified version of the code that captures both printed output and return values
            mod_code = self._prepare_code_capture(fixed_code)
            
            # Execute with timeout using thread-based approach
            def execute_code():
                with redirect_stdout(output_buffer), redirect_stderr(output_buffer):
                    exec(mod_code, namespace)
                
            # Use executor pattern that works in any thread
            self._execute_with_timeout(execute_code, timeout=timeout)
            
        except TimeoutError as e:
            return f"Error executing code: {str(e)}"
        except Exception as e:
            return f"Error executing code: {str(e)}"
        
        # Get captured output
        stdout = output_buffer.getvalue()
        
        # Clean up output
        if stdout:
            # Remove trailing newlines and None output
            stdout = re.sub(r'\nNone\n?$', '', stdout)
            # Trim trailing whitespace and newlines
            stdout = stdout.rstrip()
            
            # Check if it's a numeric value that needs to be formatted with specific precision
            if precision is not None and re.match(r'^-?\d+(\.\d+)?$', stdout):
                return self._format_numeric_output(stdout, precision)
            
            return stdout
        
        # If no response content, indicate successful execution
        return "Code executed without output."
    
    def _format_numeric_output(self, value: Any, precision: Optional[int] = None) -> str:
        """
        Format numeric outputs with consistent precision control.
        
        Args:
            value: The value to format
            precision: Optional decimal places for numeric values
            
        Returns:
            Formatted output string
        """
        try:
            # Convert to float for decimal places control
            num_value = float(value)
            
            # Apply precision formatting if specified
            if precision is not None:
                return f"{num_value:.{precision}f}"
            
            # Default formatting - keep integers as integers
            if num_value.is_integer():
                return str(int(num_value))
            
            # Keep float as is without extra formatting
            return str(num_value)
        except (ValueError, TypeError):
            # If not a number, return as is
            return str(value)
    
    def forward(self, code, precision=None) -> str:
        """
        Execute Python code and return the results.
        
        Args:
            code: The Python code to execute
            precision: Optional decimal precision for numeric outputs
            
        Returns:
            String representation of the execution result
        """
        try:
            # Log execution
            logger.info(f"Executing Python code of length {len(code)}")
            
            # Execute code in a controlled environment with timeout
            result = self._capture_output(code, timeout=self.timeout_seconds, precision=precision)
            
            # Return the result
            return result
        except Exception as e:
            # Log and return error
            logger.error(f"Error executing Python code: {str(e)}")
            return f"Error executing code: {str(e)}"
    
    def _check_security(self, code: str) -> Optional[str]:
        """
        Check the code for security issues.
        
        Args:
            code: The Python code to check
            
        Returns:
            Error message if security issues are found, None otherwise
        """
        # Check for imports
        import_pattern = re.compile(r'^\s*(?:import|from)\s+([a-zA-Z0-9_.]+)', re.MULTILINE)
        imports = import_pattern.findall(code)
        
        if imports:
            logger.info(f"Found imports: {imports}")
            
            # Check for forbidden imports
            for module in imports:
                base_module = module.split('.')[0]
                
                if base_module in self.forbidden_imports:
                    return f"Import of forbidden module '{base_module}' is not allowed"
                
                if base_module in self.risky_imports:
                    # Allow risky imports but log them
                    logger.warning(f"Risky module import: {base_module}")
        
        # Check for dangerous built-ins
        dangerous_builtins = [
            'eval', 'exec', 'compile', 'globals', 'locals', 'getattr',
            '__import__', 'open', 'input', 'breakpoint',
        ]
        
        for builtin in dangerous_builtins:
            if re.search(rf'\b{builtin}\s*\(', code):
                return f"Use of dangerous built-in '{builtin}' is not allowed"
        
        # Check for os and sys modules access
        if re.search(r'\bos\.\w+', code) and 'os' not in imports:
            return "Potential indirect use of 'os' module detected"
        
        if re.search(r'\bsys\.\w+', code) and 'sys' not in imports:
            return "Potential indirect use of 'sys' module detected"
        
        return None

    def _prepare_code_capture(self, code):
        """
        Prepare code for execution with output capture, preserving indentation.
        
        Args:
            code: The Python code to execute
            
        Returns:
            Modified code that captures both printed output and return values
        """
        lines = code.splitlines()
        
        # If it's a single line and likely an expression (not a statement)
        if len(lines) == 1 and not any(lines[0].strip().startswith(keyword) for keyword in 
                                      ['def', 'class', 'import', 'from', 'if', 'for', 'while', 
                                       'with', 'try', 'except', 'finally', 'return', 'raise',
                                       'assert', 'print', 'yield', 'break', 'continue', 'pass']):
            # For a simple expression, print its value
            mod_code = f"print({lines[0].strip()})"
            return mod_code
        
        # For multi-line code, handle indentation and print the final value if it's an expression
        has_assignment = any(re.search(r'^\s*[a-zA-Z_][a-zA-Z0-9_]*\s*=', line) for line in lines)
        has_control_flow = any(re.search(r'^\s*(if|for|while|def|class|with|try)', line) for line in lines)
        
        if not has_assignment and not has_control_flow and len(lines) == 1:
            # If it's a single line without assignment or control flow, it's likely an expression
            # Print its value
            mod_code = f"print({lines[0].strip()})"
        else:
            # Keep multi-line code as is - it should include its own print statements
            mod_code = code
            
        return mod_code

    def _check_imports(self, code):
        """
        Check that all imports in the code are authorized.
        
        Args:
            code: The Python code to check
            
        Raises:
            ValueError: If unauthorized imports are found
        """
        try:
            # Parse the code into an AST
            tree = ast.parse(code)
            
            # Check all import statements
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        module_name = alias.name.split('.')[0]
                        if module_name in self.forbidden_imports:
                            raise ValueError(f"Import of module '{module_name}' is forbidden")
                        elif module_name not in self.authorized_imports and module_name not in self.risky_imports:
                            logger.warning(f"Import of unauthorized module: {module_name}")
                            # Allow but log unauthorized imports
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        module_name = node.module.split('.')[0]
                        if module_name in self.forbidden_imports:
                            raise ValueError(f"Import from module '{module_name}' is forbidden")
                        elif module_name not in self.authorized_imports and module_name not in self.risky_imports:
                            logger.warning(f"Import from unauthorized module: {module_name}")
                            # Allow but log unauthorized imports
        except SyntaxError as e:
            # If there's a syntax error, let the execution handle it
            logger.warning(f"Syntax error while checking imports: {e}")
        except Exception as e:
            logger.error(f"Error checking imports: {e}")
            # Continue execution, let the execution handle any issues

# Function to create an instance of the tool
def get_python_interpreter_tool():
    """Create and return an enhanced Python interpreter tool instance."""
    return PythonInterpreterTool() 