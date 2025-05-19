#!/usr/bin/env python3
"""
Tool Validator for SmolAgent

This module provides enhanced validation and filtering for tools to ensure
only authorized tools are used by the SmolAgent.
"""

import re
import os
import logging
from typing import Dict, List, Tuple, Optional, Any, Set

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("tool_validator")

class ToolValidator:
    """
    Validates and filters tools to ensure only authorized tools are used.
    Provides mechanisms to scrub tool references from prompts and validate tool
    usage before execution.
    """
    
    def __init__(self, authorized_tools: Dict[str, str], authorized_imports: List[str] = None):
        """
        Initialize the tool validator.
        
        Args:
            authorized_tools: Dictionary mapping tool names to descriptions
            authorized_imports: List of authorized imports for Python tools
        """
        self.authorized_tools = authorized_tools
        self.authorized_imports = authorized_imports or []
        
        # Create a mapping of tools that are known to be problematic or risky
        self.known_risky_tools = {
            "shell": "Can execute arbitrary shell commands",
            "bash": "Can execute arbitrary bash commands",
            "exec": "Can execute arbitrary code",
            "system": "Can execute system commands",
            "cmd": "Can execute Windows commands",
            "powershell": "Can execute PowerShell commands",
            "sql": "Can execute SQL queries",
            "file_write": "Can write to files",
            "file_delete": "Can delete files",
            "network": "Can make arbitrary network requests",
            "ssh": "Can make SSH connections",
            "ftp": "Can make FTP connections",
            "crypto": "Can perform cryptographic operations",
            "process": "Can manipulate system processes",
            "user": "Can manipulate user accounts",
            "admin": "Can perform administrative operations",
            "remote": "Can execute remote commands",
            "console": "Can access console",
            "terminal": "Can access terminal",
            "eval": "Can evaluate arbitrary code"
        }
        
        # Patterns for detecting unauthorized tool usage in code
        self.unauthorized_patterns = [
            r'subprocess\.(Popen|call|check_call|check_output|run)',
            r'os\.(system|popen|exec|spawn)',
            r'exec\(|eval\(',
            r'__import__\(',
            r'importlib',
            r'runpy',
            r'getattr\(.+,\s*[\'"]__',
            r'globals\(\)[^\w]',
            r'locals\(\)[^\w]',
            r'breakpoint\(\)'
        ]
        
        logger.info(f"Tool validator initialized with {len(authorized_tools)} authorized tools")
    
    def scrub_prompt(self, prompt: str) -> str:
        """
        Scrub prompts to remove references to unauthorized tools.
        
        Args:
            prompt: The original prompt
            
        Returns:
            Cleaned prompt with unauthorized tool references removed
        """
        # First, determine if the prompt has any references to tools
        tool_references = re.findall(r'(?:using|with|via|through|employ|run|execute|call)\s+the\s+([a-zA-Z0-9_]+)\s+(?:tool|function|command)', 
                                     prompt, re.IGNORECASE)
        
        cleaned_prompt = prompt
        
        for tool_ref in tool_references:
            tool_name = tool_ref.lower().strip()
            
            # Check if this is an unauthorized tool
            if (tool_name not in self.authorized_tools and 
                (tool_name in self.known_risky_tools or 
                 any(risky_name in tool_name for risky_name in self.known_risky_tools))):
                
                # Pattern to match the entire phrase mentioning the unauthorized tool
                pattern = re.compile(
                    fr'(?:using|with|via|through|employ|run|execute|call)\s+the\s+{re.escape(tool_ref)}\s+(?:tool|function|command)',
                    re.IGNORECASE
                )
                
                # Replace with a reference to an authorized alternative or remove entirely
                alternative = self._suggest_alternative_tool(tool_name)
                if alternative:
                    replacement = f"using the {alternative} tool"
                    cleaned_prompt = pattern.sub(replacement, cleaned_prompt)
                    logger.info(f"Replaced unauthorized tool '{tool_name}' with '{alternative}'")
                else:
                    # Simply remove the unauthorized tool reference
                    cleaned_prompt = pattern.sub("", cleaned_prompt)
                    logger.info(f"Removed unauthorized tool '{tool_name}' from prompt")
        
        # Secondary pattern: direct references like "use X tool"
        for match in re.finditer(r'(?:use|try|invoke|access)\s+(?:the\s+)?([a-zA-Z0-9_]+)\s+(?:tool|function|command)', 
                                cleaned_prompt, re.IGNORECASE):
            tool_name = match.group(1).lower().strip()
            
            if (tool_name not in self.authorized_tools and 
                (tool_name in self.known_risky_tools or 
                 any(risky_name in tool_name for risky_name in self.known_risky_tools))):
                
                # Pattern to match the entire phrase
                pattern = re.compile(
                    fr'(?:use|try|invoke|access)\s+(?:the\s+)?{re.escape(match.group(1))}\s+(?:tool|function|command)',
                    re.IGNORECASE
                )
                
                # Replace with an authorized alternative or remove
                alternative = self._suggest_alternative_tool(tool_name)
                if alternative:
                    replacement = f"use the {alternative} tool"
                    cleaned_prompt = pattern.sub(replacement, cleaned_prompt)
                    logger.info(f"Replaced direct reference to unauthorized tool '{tool_name}' with '{alternative}'")
                else:
                    cleaned_prompt = pattern.sub("", cleaned_prompt)
                    logger.info(f"Removed direct reference to unauthorized tool '{tool_name}' from prompt")
        
        return cleaned_prompt
    
    def validate_tool_usage(self, tool_name: str, code: Optional[str] = None) -> Tuple[bool, str]:
        """
        Validate if a tool can be used before attempting it.
        
        Args:
            tool_name: Name of the tool to validate
            code: Optional code to check for unauthorized imports or patterns
            
        Returns:
            Tuple of (valid, message)
        """
        # Check if tool exists and is authorized
        if tool_name not in self.authorized_tools:
            return False, f"Tool '{tool_name}' is not authorized. Available tools: {', '.join(self.authorized_tools.keys())}"
        
        # For Python tool, perform additional checks
        if tool_name == "python" and code:
            # Check for unauthorized imports
            import_issues = self._validate_imports(code)
            if import_issues:
                return False, f"Unauthorized imports detected: {import_issues}"
            
            # Check for other unsafe patterns in the code
            security_issues = self._validate_code_security(code)
            if security_issues:
                return False, f"Security concerns detected in code: {security_issues}"
        
        return True, f"Tool usage valid: {self.authorized_tools[tool_name]}"
    
    def _validate_imports(self, code: str) -> str:
        """
        Validate imports in Python code against authorized imports list.
        
        Args:
            code: Python code to check
            
        Returns:
            String with unauthorized imports or empty string if all imports are authorized
        """
        # Regular expression to find both 'import x' and 'from x import y' patterns
        import_regex = re.compile(r'(?:from\s+([a-zA-Z0-9_.]+)\s+import)|(?:import\s+([a-zA-Z0-9_.]+))')
        
        matches = import_regex.finditer(code)
        unauthorized = []
        
        for match in matches:
            # Handle both import forms
            if match.group(1):  # from x import y
                module = match.group(1)
            else:  # import x
                module = match.group(2)
            
            # Strip any trailing comments or whitespace
            module = module.strip()
            
            # Get the root module (before first dot)
            root_module = module.split('.')[0]
            
            if root_module not in self.authorized_imports:
                unauthorized.append(module)
        
        if unauthorized:
            return ", ".join(unauthorized)
        return ""
    
    def _validate_code_security(self, code: str) -> str:
        """
        Check for potentially unsafe code patterns.
        
        Args:
            code: Python code to check
            
        Returns:
            String describing security issues or empty string if no issues found
        """
        issues = []
        
        for pattern in self.unauthorized_patterns:
            if re.search(pattern, code):
                issues.append(f"Unauthorized pattern: {pattern}")
        
        return "; ".join(issues)
    
    def _suggest_alternative_tool(self, unauthorized_tool: str) -> Optional[str]:
        """
        Suggest an alternative authorized tool for an unauthorized one.
        
        Args:
            unauthorized_tool: The unauthorized tool name
            
        Returns:
            Name of an alternative authorized tool or None if no appropriate alternative
        """
        # Mapping of common unauthorized tools to authorized alternatives
        alternatives = {
            "shell": "python",
            "bash": "python",
            "exec": "python",
            "system": "python",
            "cmd": "python",
            "powershell": "python",
            "sql": "python",
            "file_write": "python",
            "file_read": "file_reader",
            "network": "webpage",
            "http": "webpage",
            "url": "webpage",
            "web": "search",
            "browser": "webpage",
            "google": "search",
            "search_engine": "search",
            "audio_processor": "audio",
            "speech": "audio",
            "voice": "audio",
            "youtube_scraper": "youtube",
            "video": "youtube"
        }
        
        # Check for direct match
        if unauthorized_tool in alternatives:
            alternative = alternatives[unauthorized_tool]
            # Verify the alternative is actually authorized
            if alternative in self.authorized_tools:
                return alternative
        
        # No direct match, try to find a similar tool
        for key, value in alternatives.items():
            if key in unauthorized_tool:
                if value in self.authorized_tools:
                    return value
        
        # Default to python if available, or final_answer
        if "python" in self.authorized_tools:
            return "python"
        elif "final_answer" in self.authorized_tools:
            return "final_answer"
        
        # No suitable alternative found
        return None

    def filter_tool_documentation(self, tool_docs: str) -> str:
        """
        Filter tool documentation to only include authorized tools.
        
        Args:
            tool_docs: Original tool documentation string
            
        Returns:
            Filtered tool documentation with only authorized tools
        """
        lines = tool_docs.split("\n")
        filtered_lines = []
        
        # Keep track of whether we're in the PYTHON TOOL section
        in_python_section = False
        
        for line in lines:
            # Check for section headers
            if line.strip() == "PYTHON TOOL:":
                in_python_section = True
                filtered_lines.append(line)
            elif line.strip() == "OTHER TOOLS:":
                in_python_section = False
                filtered_lines.append(line)
            elif in_python_section:
                # For Python section, only include authorized imports
                if line.strip().startswith("  - Execute Python"):
                    filtered_lines.append(line)
                elif line.strip().startswith("    * "):
                    import_name = line.strip()[6:].strip()  # Extract import name
                    if import_name in self.authorized_imports:
                        filtered_lines.append(line)
            else:
                # For other tools section, only include authorized tools
                match = re.match(r'\s*-\s*([a-zA-Z0-9_]+):', line)
                if match:
                    tool_name = match.group(1)
                    if tool_name in self.authorized_tools:
                        filtered_lines.append(line)
                else:
                    # Keep lines that don't specify tools (headers, etc.)
                    filtered_lines.append(line)
        
        return "\n".join(filtered_lines)

    def enhance_system_prompt(self, base_prompt: str) -> str:
        """
        Enhance the system prompt with specific guidance on tool usage.
        
        Args:
            base_prompt: The base system prompt
            
        Returns:
            Enhanced system prompt with additional tool usage guidance
        """
        # Create a string of available tool names for the prompt
        tool_names = ", ".join(sorted(self.authorized_tools.keys()))
        
        # Add specific guidance on how to use tools properly
        tool_guidance = [
            f"\nIMPORTANT TOOL USAGE GUIDELINES:",
            f"- Only use the following authorized tools: {tool_names}",
            f"- Never attempt to use tools that aren't in this list",
            f"- When using the python tool, only use authorized imports",
            f"- Tools must be used according to their documented purpose",
            f"- Validate tool availability before attempting to use it",
            f"- If a tool fails, try an alternative approach"
        ]
        
        # Combine the base prompt with the tool guidance
        enhanced_prompt = base_prompt + "\n" + "\n".join(tool_guidance)
        
        return enhanced_prompt 