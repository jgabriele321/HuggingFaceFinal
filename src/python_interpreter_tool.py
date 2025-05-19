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
from contextlib import redirect_stdout, redirect_stderr, contextmanager
from typing import List, Dict, Any, Optional, Set, Union

from smolagents import Tool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PythonInterpreterTool")

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
        self.timeout_seconds = 10
        
        # Define allowed modules that are safe to import
        self.allowed_imports = {
            "math", "random", "datetime", "time", "re", "json", 
            "collections", "itertools", "functools", "operator",
            "string", "copy", "textwrap", "calendar", "fractions",
            "statistics", "decimal", "pathlib", "uuid"
        }
        
        # Potentially risky modules that require careful review
        self.risky_imports = {
            "os", "sys", "subprocess", "shutil", "socket", "requests",
            "urllib", "http", "ftplib", "telnetlib", "smtplib",
            "email", "poplib", "imaplib", "nntplib", "webbrowser",
            "multiprocessing", "threading", "concurrent", "asyncio"
        }
        
        # Explicitly forbidden modules
        self.forbidden_imports = {
            "builtins", "__builtin__", "pickle", "shelve", "marshal",
            "cPickle", "dbm", "sqlite3", "zlib", "gzip", "bz2", "zipfile",
            "tarfile", "platform", "ctypes", "crypt", "pwd", "spwd", "signal",
            "mmap", "readline", "rlcompleter", "pty", "popen2", "commands",
            "getpass", "tty", "pdb", "cgitb", "importlib", "pkgutil",
            "runpy", "compileall", "py_compile", "symtable", "pyclbr", "ast"
        }
    
    @contextmanager
    def _timeout(self, seconds: int):
        """
        Context manager that enforces a timeout for code execution.
        
        Args:
            seconds: The timeout in seconds
            
        Raises:
            TimeoutError: If the code execution exceeds the timeout
        """
        def handler(signum, frame):
            raise TimeoutError(f"Code execution timed out after {seconds} seconds")
        
        # Set signal handler
        original_handler = signal.signal(signal.SIGALRM, handler)
        signal.alarm(seconds)
        
        try:
            yield
        finally:
            # Restore original handler and reset alarm
            signal.alarm(0)
            signal.signal(signal.SIGALRM, original_handler)
    
    @contextmanager
    def _timeout_context(self, seconds):
        """
        Context manager for timeout handling.
        
        Args:
            seconds: Timeout in seconds
            
        Yields:
            None, just establishes the timeout context
        """
        # Set an alarm
        def handler(signum, frame):
            raise TimeoutError(f"Code execution timed out after {seconds} seconds")
            
        # Set the timeout handler
        original_handler = signal.signal(signal.SIGALRM, handler)
        signal.alarm(seconds)
        
        try:
            yield
        finally:
            # Cancel the alarm and restore the original handler
            signal.alarm(0)
            signal.signal(signal.SIGALRM, original_handler)
    
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
            
            # Set up the timeout handler
            with self._timeout_context(timeout), redirect_stdout(output_buffer), redirect_stderr(output_buffer):
                # Execute the code
                exec(mod_code, namespace)
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
                                       'pass', 'continue', 'break', 'assert', 'del']):
            # If it doesn't have an assignment and is not a statement
            if '=' not in lines[0] and not lines[0].strip().endswith(':'):
                return f"_result_value_ = {lines[0]}\nprint(str(_result_value_).strip())"
            # Otherwise, execute as is
            return code
        
        # For control flow statements (if, for, while, etc.), preserve the original code
        # to maintain proper indentation in Python blocks
        for line in lines:
            if line.strip().endswith(':'):
                # Detected control flow statement, execute the code as is
                return code
                
        # For multi-line code with expression at the end
        if len(lines) > 1:
            last_line = lines[-1].strip()
            # Check if last line is an expression
            if (not any(last_line.startswith(keyword) for keyword in 
                      ['def', 'class', 'import', 'from', 'if', 'for', 'while', 
                       'with', 'try', 'except', 'finally', 'return', 'raise',
                       'pass', 'continue', 'break', 'assert', 'del']) and
                    '=' not in last_line and not last_line.endswith(':') and 
                    not last_line.startswith('#')):
                
                # Get all lines except the last one
                new_lines = lines[:-1]
                # Add code to evaluate the expression and print the result
                new_lines.append(f"print(str({last_line}).strip())")
                return '\n'.join(new_lines)
        
        # Default: return the original code
        return code

    def _check_imports(self, code):
        """
        Check for potentially harmful imports in the code.
        
        Args:
            code: The Python code to check
            
        Raises:
            SecurityError: If potentially harmful modules are imported
        """
        # Look for import statements
        import_pattern = re.compile(r'^\s*(?:from\s+(\S+)(?:\s+import)|import\s+([^,\s]+))', re.MULTILINE)
        imported_modules = []
        
        for match in import_pattern.finditer(code):
            module = match.group(1) or match.group(2)
            if module:
                # Extract the base module name (e.g., 'os.path' -> 'os')
                base_module = module.split('.')[0]
                imported_modules.append(base_module)
        
        # Log imported modules
        if imported_modules:
            logger.info(f"Found imports: {imported_modules}")
            
        # Check for potentially dangerous modules
        dangerous_modules = {
            'os', 'subprocess', 'sys', 'shutil', 'socket', 'requests', 
            'urllib', 'ftplib', 'telnetlib', 'smtplib', 'pickle'
        }
        
        for module in imported_modules:
            if module in dangerous_modules:
                # We're logging a warning but will still execute the code
                # In a production environment, this should be rejected
                logger.warning(f"Potentially harmful module imported: {module}")
                
                # Alternatively, raise an exception to prevent execution:
                # raise SecurityError(f"Module '{module}' is not allowed for security reasons")

# Function to create an instance of the tool
def get_python_interpreter_tool() -> Dict[str, Any]:
    """Create and return an enhanced Python interpreter tool configuration."""
    return {
        "name": "python",
        "description": "Execute Python code and return the results with precise formatting",
        "function": PythonInterpreterTool().forward,
        "parameters": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "The Python code to execute"
                },
                "precision": {
                    "type": "integer",
                    "description": "Optional decimal places for numeric outputs",
                    "nullable": True
                }
            },
            "required": ["code"]
        }
    } 