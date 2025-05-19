#!/usr/bin/env python3
"""
Python Interpreter Tool for SmolAgent.

This tool provides functionality to execute Python code securely.
"""

import re
import io
import sys
import logging
import inspect
import traceback
from contextlib import redirect_stdout, redirect_stderr
from typing import List, Dict, Any, Optional, Set

from smolagents import Tool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PythonInterpreterTool")

class PythonInterpreterTool(Tool):
    """Tool for executing Python code securely."""
    
    name = "python"
    description = "Execute Python code and return the results"
    
    inputs = {
        "code": {
            "type": "string",
            "description": "The Python code to execute"
        }
    }
    
    output_type = "string"
    
    def __init__(self, **kwargs):
        """Initialize the tool with secure defaults."""
        super().__init__(**kwargs)
        
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
    
    def forward(self, code: str) -> str:
        """
        Execute Python code and return the results.
        
        Args:
            code: The Python code to execute
            
        Returns:
            The output of the code execution or error messages
        """
        if not code:
            return "Error: No code provided"
        
        logger.info(f"Executing Python code of length {len(code)}")
        
        # Validate the code for security issues
        security_check_result = self._check_security(code)
        if security_check_result:
            return f"Security violation: {security_check_result}"
        
        # Execute the code with captured output and error handling
        try:
            # Capture stdout and stderr
            out_buffer = io.StringIO()
            err_buffer = io.StringIO()
            result = None
            
            # Create a new namespace for execution
            namespace = {'__builtins__': __builtins__}
            
            with redirect_stdout(out_buffer), redirect_stderr(err_buffer):
                exec(code, namespace)
            
            # Get the output
            stdout = out_buffer.getvalue()
            stderr = err_buffer.getvalue()
            
            # Format the response
            response = ""
            
            if stdout:
                response += f"Output:\n{stdout}\n"
            
            if stderr:
                response += f"Errors:\n{stderr}\n"
            
            if not response:
                response = "Code executed without output."
            
            return response
            
        except Exception as e:
            # Get detailed error information
            exc_type, exc_value, exc_traceback = sys.exc_info()
            tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
            
            error_message = f"Error executing code: {str(e)}\n\nTraceback:\n{''.join(tb_lines)}"
            logger.error(error_message)
            
            return error_message
    
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

# Function to create an instance of the tool
def get_python_interpreter_tool() -> Dict[str, Any]:
    """Create and return a Python interpreter tool configuration."""
    return {
        "name": "python",
        "description": "Execute Python code and return the results",
        "function": PythonInterpreterTool().forward,
        "parameters": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "The Python code to execute"
                }
            },
            "required": ["code"]
        }
    } 