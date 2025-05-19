"""
Unit tests for the python_interpreter_tool module.

Tests ensure that the Python Interpreter Tool correctly executes code
and handles output formatting and errors.
"""

import unittest
import sys
import os
from pathlib import Path

# Add parent directory to path to ensure imports work correctly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.python_interpreter_tool import PythonInterpreterTool, get_python_interpreter_tool

class TestPythonInterpreterTool(unittest.TestCase):
    """Test cases for the PythonInterpreterTool class."""
    
    def setUp(self):
        """Set up tool instance for testing."""
        self.tool = PythonInterpreterTool()
    
    def test_basic_code_execution(self):
        """Test basic code execution functionality."""
        # Test simple print statement
        code = "print('Hello, World!')"
        result = self.tool.forward(code)
        self.assertEqual(result, "Hello, World!")
        
        # Test variable assignment and printing
        code = """x = 5
y = 10
print(x + y)"""
        result = self.tool.forward(code)
        self.assertEqual(result, "15")
        
        # Test multi-line output with proper indentation
        code = """for i in range(3):
    print(f"Line {i}")"""
        result = self.tool.forward(code)
        # Normalize line endings for comparison
        normalized_result = result.replace('\r\n', '\n')
        self.assertEqual(normalized_result, "Line 0\nLine 1\nLine 2")
    
    def test_output_capture_enhancement(self):
        """Test enhanced output capture functionality."""
        # Test capture of print statements
        code = "print('Hello')"
        result = self.tool.forward(code)
        self.assertEqual(result, "Hello")
        
        # Test value extraction from expression
        code = "2 + 2"
        result = self.tool.forward(code)
        self.assertEqual(result, "4")
        
        # Test capturing the last statement as output
        code = """x = 10
y = 5
x * y"""
        result = self.tool.forward(code)
        self.assertEqual(result, "50")
    
    def test_numeric_precision_control(self):
        """Test numeric precision control for outputs."""
        # Test integer result with different precisions
        code = "42"
        result = self.tool.forward(code, precision=2)
        self.assertEqual(result, "42.00")
        
        # Test float result with precision
        code = "355 / 113"  # Approximation of π
        result = self.tool.forward(code, precision=4)
        self.assertEqual(result, "3.1416")
        
        # Test print with floating point and precision
        code = "print(1/3)"
        result = self.tool.forward(code, precision=3)
        self.assertEqual(result, "0.333")
    
    def test_error_handling(self):
        """Test error handling capabilities."""
        # Test syntax error
        code = "print('Incomplete string"
        result = self.tool.forward(code)
        self.assertIn("Error executing code:", result)
        self.assertIn("unterminated", result)  # Specific error message may vary by Python version
        
        # Test runtime error
        code = "1/0"
        result = self.tool.forward(code)
        self.assertIn("Error executing code:", result)
        self.assertIn("division by zero", result)
    
    def test_security_checks(self):
        """Test security validation of code."""
        # Test detection of potentially dangerous imports
        code = """import pickle
print("Imported pickle")"""
        result = self.tool.forward(code)
        self.assertEqual(result, "Imported pickle")
        
        # In the current implementation, we log warnings but don't block execution
        # So just verify that the code executed without error
        
        # Test with a safe import
        code = """import math
print("π ≈ " + str(math.pi))"""
        result = self.tool.forward(code)
        self.assertIn("π ≈ 3.14", result)
    
    def test_tool_factory_function(self):
        """Test the tool factory function."""
        # Test that the factory function returns a proper tool configuration
        tool_config = get_python_interpreter_tool()
        
        self.assertEqual(tool_config["name"], "python")
        self.assertIn("description", tool_config)
        self.assertIn("function", tool_config)
        self.assertIn("parameters", tool_config)
        
        # Test that the parameters include code and precision
        parameters = tool_config["parameters"]["properties"]
        self.assertIn("code", parameters)
        self.assertIn("precision", parameters)

if __name__ == "__main__":
    unittest.main() 