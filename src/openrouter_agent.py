import os
import json
import requests
import time
import random
import logging
import base64
import re
from typing import List, Dict, Any, Optional, Union
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("OpenRouterAgent")

class ChatMessage:
    """Message class compatible with OpenRouter API and smolagents."""
    
    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content
        
    def to_dict(self):
        return {"role": self.role, "content": self.content}
        
    def __str__(self):
        return self.content

class OpenRouterModel:
    """Model that uses OpenRouter API to access various LLMs."""
    
    def __init__(self, api_key: Optional[str] = None, model_id: str = "anthropic/claude-3-haiku"):
        """
        Initialize the OpenRouter model.
        
        Args:
            api_key: OpenRouter API key (get one at https://openrouter.ai/keys)
            model_id: Model identifier on OpenRouter
        """
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OpenRouter API key is required. Get one at https://openrouter.ai/keys")
            
        self.model_id = model_id
        self.base_url = "https://openrouter.ai/api/v1"
        
        logger.info(f"Initialized OpenRouterModel with model: {model_id}")
    
    def __call__(self, prompt_or_messages) -> ChatMessage:
        """Send a request to the OpenRouter API and return the response."""
        # Ensure proper message format
        messages = self._prepare_messages(prompt_or_messages)
        
        url = f"{self.base_url}/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://huggingface.co/spaces",  # Helps with quotas
            "X-Title": "SmolAgent"  # Optional app name
        }
        
        data = {
            "model": self.model_id,
            "messages": messages
        }
        
        # Add retry logic with exponential backoff
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.post(url, headers=headers, json=data, timeout=60)
                response.raise_for_status()
                
                response_data = response.json()
                content = response_data["choices"][0]["message"]["content"]
                
                return ChatMessage(role="assistant", content=content)
                
            except requests.exceptions.HTTPError as e:
                logger.error(f"HTTP error with OpenRouter API (attempt {attempt+1}/{max_retries}): {str(e)}")
                if e.response.status_code in [429, 500, 502, 503, 504]:
                    # Retryable errors (rate limits, server errors)
                    backoff = (2 ** attempt) + random.uniform(0, 1)
                    logger.info(f"Retrying in {backoff:.2f} seconds...")
                    time.sleep(backoff)
                else:
                    # Non-retryable client errors
                    logger.error(f"Non-retryable error: {e.response.status_code} {e.response.text}")
                    return ChatMessage(
                        role="assistant", 
                        content=f"I encountered an API error: {e.response.status_code}. Please try again later."
                    )
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                # Network-related errors
                logger.error(f"Network error (attempt {attempt+1}/{max_retries}): {str(e)}")
                backoff = (2 ** attempt) + random.uniform(0, 1)
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {backoff:.2f} seconds...")
                    time.sleep(backoff)
                else:
                    return ChatMessage(
                        role="assistant", 
                        content="I encountered a network issue connecting to the language model. Please try again."
                    )
            except Exception as e:
                # Unexpected errors
                logger.error(f"Unexpected error (attempt {attempt+1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    backoff = (2 ** attempt) + random.uniform(0, 1)
                    logger.info(f"Retrying in {backoff:.2f} seconds...")
                    time.sleep(backoff)
                else:
                    return ChatMessage(
                        role="assistant", 
                        content="I encountered an unexpected error. Please try again."
                    )
    
    def _prepare_messages(self, prompt_or_messages):
        """Ensure proper message format for OpenRouter API."""
        # Handle different input types
        if isinstance(prompt_or_messages, str):
            # Single string prompt
            return [{"role": "user", "content": prompt_or_messages}]
        elif isinstance(prompt_or_messages, list):
            # List of messages
            formatted_messages = []
            for msg in prompt_or_messages:
                if isinstance(msg, dict):
                    # Process content field which might be a string or a list
                    content = msg.get("content", "")
                    if isinstance(content, list):
                        # Extract text from content items
                        text_content = []
                        for item in content:
                            if isinstance(item, dict) and item.get("type") == "text":
                                text_content.append(item.get("text", ""))
                        content = " ".join(text_content)
                    
                    formatted_messages.append({
                        "role": msg.get("role", "user"),
                        "content": str(content)  # Ensure content is string
                    })
                elif hasattr(msg, 'role') and hasattr(msg, 'content'):
                    # Handle ChatMessage objects
                    formatted_messages.append({
                        "role": msg.role,
                        "content": str(msg.content)  # Ensure content is string
                    })
            
            return formatted_messages or [{"role": "user", "content": "Hello"}]
        else:
            # Default fallback
            return [{"role": "user", "content": str(prompt_or_messages)}]
    
    def generate(self, prompt, stop_sequences=None, max_tokens=None, **kwargs):
        """Compatibility method for the smolagents CodeAgent."""
        response = self.__call__(prompt)
        
        # Format response as CodeAgent expects for code blocks
        if hasattr(response, 'content'):
            content = response.content
        else:
            content = str(response)
        
        # Check if this appears to be a request for code or a chess-related question
        prompt_str = str(prompt).lower()
        
        # Special handling for chess moves
        if "chess" in prompt_str:
            # If it's a chess response and contains a move, ensure it's properly formatted
            if not content.strip().startswith("```"):
                # For chess, we keep the answer simple - just the move or the explanation
                return ChatMessage(role="assistant", content=content)
        
        # For code requests or other complex responses
        if any(code_term in prompt_str for code_term in ["code", "function", "implementation", "script", "program"]):
            # If not already formatted as code, wrap it in a code block
            if "```" not in content:
                formatted = f"Thoughts: Processing your request\nCode:\n```python\n{content}\n```"
                return ChatMessage(role="assistant", content=formatted)
        
        # For other responses, ensure they're properly formatted for CodeAgent
        if not content.strip().startswith("```") and not content.strip().startswith("Thoughts:"):
            # Wrap simple responses in a format CodeAgent can understand
            formatted = f"Thoughts: {content}\n\nNo code needed for this response."
            return ChatMessage(role="assistant", content=formatted)
            
        return ChatMessage(role="assistant", content=content)

class FileHandler:
    """Handles file operations with minimal dependencies."""
    
    @staticmethod
    def get_file_info(file_path: str) -> str:
        """Get detailed information about a file."""
        if not file_path or not Path(file_path).exists():
            return f"Error: The file {file_path} does not exist."
        
        try:
            # Get basic file info
            path = Path(file_path)
            file_size = path.stat().st_size
            file_size_mb = file_size / (1024 * 1024)
            extension = path.suffix.lower()
            
            result = f"File: {path.name}\n"
            result += f"Extension: {extension}\n"
            result += f"Size: {file_size_mb:.2f} MB\n"
            
            # Add type-specific details when possible
            if extension in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
                try:
                    from PIL import Image
                    with Image.open(path) as img:
                        result += f"Image dimensions: {img.width}x{img.height}\n"
                        result += f"Image mode: {img.mode}\n"
                        result += f"Image format: {img.format}\n"
                except ImportError:
                    # PIL not available
                    result += "Image file detected (detailed info unavailable without PIL/Pillow)\n"
                except Exception as e:
                    result += f"Error analyzing image: {str(e)}\n"
            
            elif extension in ['.csv', '.json', '.txt', '.md', '.py', '.js']:
                # For text files, read the first few lines
                try:
                    with open(path, 'r', encoding='utf-8', errors='replace') as f:
                        content = f.read(1000)
                    result += f"Text content preview: {content[:300]}...\n"
                except Exception as e:
                    result += f"Error reading file content: {str(e)}\n"
            
            return result
        
        except Exception as e:
            return f"Error analyzing file: {str(e)}"
    
    @staticmethod
    def extract_code_from_file(file_path: str) -> str:
        """Extract code from a file with proper formatting."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            
            extension = Path(file_path).suffix.lower()
            language = {
                '.py': 'python',
                '.js': 'javascript',
                '.html': 'html',
                '.css': 'css',
                '.json': 'json'
            }.get(extension, 'text')
            
            return f"```{language}\n{content}\n```"
        except Exception as e:
            return f"Error reading file: {str(e)}"
    
    @staticmethod
    def handle_image(file_path: str) -> str:
        """Process image files with basic information."""
        try:
            # Try to use PIL if available
            try:
                from PIL import Image
                with Image.open(file_path) as img:
                    return f"Image analysis: {img.width}x{img.height} pixels, format: {img.format}, mode: {img.mode}"
            except ImportError:
                # Fall back to basic file info
                file_size = Path(file_path).stat().st_size
                return f"Image file detected (size: {file_size / 1024:.1f} KB). PIL not available for detailed analysis."
        except Exception as e:
            return f"Error processing image: {str(e)}"

class SmolAgent:
    """
    A robust agent using OpenRouter for reliable model access.
    """
    
    def __init__(self, openrouter_api_key: Optional[str] = None, model_id: str = "anthropic/claude-3-haiku"):
        """
        Initialize the SmolAgent.
        
        Args:
            openrouter_api_key: OpenRouter API key
            model_id: The model ID to use (default: "anthropic/claude-3-haiku")
        """
        self.openrouter_api_key = openrouter_api_key or os.environ.get("OPENROUTER_API_KEY")
        
        # Initialize model using OpenRouter
        self.model = OpenRouterModel(
            api_key=self.openrouter_api_key,
            model_id=model_id
        )
        
        # Create tool registry with available tools
        self.tool_registry = self._create_tool_registry()
        
        # Initialize smolagents if available
        try:
            from smolagents import CodeAgent, PythonInterpreterTool, FinalAnswerTool
            
            # Create properly configured Python interpreter with explicit authorized imports
            self.authorized_imports = [
                "os", "json", "re", "math", "time", "pathlib", "random",
                "collections", "itertools", "functools", "string", "datetime",
                "base64", "io", "PIL", "requests"
            ]
            
            python_tool = PythonInterpreterTool(
                authorized_imports=self.authorized_imports
            )
            
            # Define available tools
            self.tools = [
                python_tool,
                FinalAnswerTool()
            ]
            
            # Generate tool documentation for agent prompt
            tool_docs = self._generate_tool_documentation()
            
            # Initialize the agent with proper configuration
            self.agent = CodeAgent(
                tools=self.tools,
                model=self.model,
                verbosity_level=1,
                max_steps=5,
                stream_outputs=False,
                additional_authorized_imports=self.authorized_imports,
                system_prompt=f"You have access to the following tools:\n{tool_docs}\n\nWhen using tools, verify they exist before attempting to use them."
            )
            self.use_agent = True
            logger.info("Initialized with smolagents CodeAgent and explicit tool configuration")
        except ImportError:
            self.agent = None
            self.use_agent = False
            logger.info("smolagents not available, falling back to direct model use")

    def _create_tool_registry(self):
        """
        Create a registry of available tools with descriptions.
        
        Returns:
            Dictionary mapping tool names to descriptions
        """
        return {
            "python": "Execute Python code with access to a restricted set of libraries",
            "final_answer": "Submit your final answer when task is complete",
            "file_reader": "Read the contents of a file at a specified path",
            "validate_tool": "Check if a tool exists and is available for use"
        }
    
    def _generate_tool_documentation(self):
        """
        Generate formatted documentation for available tools.
        
        Returns:
            Formatted string with tool documentation
        """
        docs = []
        
        # Add authorized imports documentation
        docs.append("PYTHON TOOL:")
        docs.append("  - Execute Python code with the following authorized imports:")
        for imp in sorted(self.authorized_imports):
            docs.append(f"    * {imp}")
        
        # Add other tool documentation
        docs.append("\nOTHER TOOLS:")
        for name, desc in self.tool_registry.items():
            if name != "python":
                docs.append(f"  - {name}: {desc}")
        
        return "\n".join(docs)
    
    def validate_tool_usage(self, tool_name, code=None):
        """
        Validate if a tool can be used before attempting it.
        
        Args:
            tool_name: Name of the tool to validate
            code: Optional code to check for unauthorized imports
            
        Returns:
            Tuple of (valid, message)
        """
        # Check if tool exists
        if tool_name not in self.tool_registry:
            return False, f"Tool '{tool_name}' does not exist. Available tools: {', '.join(self.tool_registry.keys())}"
        
        # For Python tool, check imports
        if tool_name == "python" and code:
            import re
            import_pattern = r'import\s+([a-zA-Z0-9_.]+)'
            imports = re.findall(import_pattern, code)
            
            for imp in imports:
                if imp not in self.authorized_imports:
                    return False, f"Import '{imp}' not authorized. Use only: {', '.join(sorted(self.authorized_imports))}"
        
        return True, "Tool usage valid"
    
    def execute_with_fallback(self, prompt, tool_name=None, attempt=0):
        """
        Execute a task with fallback mechanisms if initial attempt fails.
        
        Args:
            prompt: The prompt to process
            tool_name: Optional tool to try first
            attempt: Current attempt number (for tracking retries)
            
        Returns:
            Result of execution
        """
        try:
            # Try main approach with specified tool
            if tool_name and self.use_agent:
                # Validate tool before use
                valid, message = self.validate_tool_usage(tool_name)
                if not valid:
                    logger.warning(f"Tool validation failed: {message}")
                    # Fall back to agent without specific tool directive
                    return self.agent.run(prompt)
                else:
                    # Add tool directive to prompt
                    tool_prompt = f"Use the {tool_name} tool to answer: {prompt}"
                    return self.agent.run(tool_prompt)
            
            # Default approach: use agent if available
            if self.use_agent:
                return self.agent.run(prompt)
            else:
                # Fall back to direct model use
                messages = [{"role": "user", "content": prompt}]
                return self.model(messages)
                
        except Exception as e:
            logger.warning(f"Error in execution (attempt {attempt+1}): {str(e)}")
            
            # If still have retries left, try again with simplified approach
            if attempt < 2:
                # For retry 1: Try with simpler prompt
                if attempt == 0:
                    simplified_prompt = f"Please answer this question simply: {prompt}"
                # For retry 2: Try with most basic approach
                else:
                    simplified_prompt = f"Answer briefly: {prompt}"
                
                # Sleep with exponential backoff before retry
                time.sleep(2 ** attempt)
                return self.execute_with_fallback(simplified_prompt, None, attempt + 1)
            
            # If all retries failed, return error message
            return "I encountered an error processing your request. Please try a simpler query."

    def __call__(self, question: str, file_path: Optional[str] = None, task_id: str = None) -> str:
        """
        Process a question and return an answer.
        
        Args:
            question: The question to answer
            file_path: Optional path to a file that may be required
            task_id: Optional task ID for tracking
            
        Returns:
            The answer to the question
        """
        # Prepare prompt with additional context
        prompt = question
        
        if file_path and os.path.exists(file_path):
            file_info = FileHandler.get_file_info(file_path)
            prompt += f"\n\nFile information:\n{file_info}"
            
            # Handle special file types
            extension = Path(file_path).suffix.lower()
            if extension in ['.py', '.js', '.html', '.css', '.json']:
                code_content = FileHandler.extract_code_from_file(file_path)
                prompt += f"\n\nFile content:\n{code_content}"
            elif extension in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
                image_info = FileHandler.handle_image(file_path)
                prompt += f"\n\n{image_info}"
        
        # Determine most appropriate tool based on question type
        tool_name = self._select_appropriate_tool(question)
        logger.info(f"Selected tool: {tool_name}")
        
        # Process with robust error handling using our fallback mechanism
        start_time = time.time()
        try:
            # Use the execute_with_fallback method for robust processing
            raw_answer = self.execute_with_fallback(prompt, tool_name)
            
            elapsed_time = time.time() - start_time
            logger.info(f"Processing completed in {elapsed_time:.2f} seconds")
            
            return self._postprocess_answer(raw_answer, question)
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(f"Fatal error processing question after {elapsed_time:.2f} seconds: {str(e)}")
            return "I encountered a serious error while processing your request. Please try again with a simpler query."
    
    def _select_appropriate_tool(self, question: str) -> Optional[str]:
        """
        Select the most appropriate tool based on question content.
        
        Args:
            question: The user's question
            
        Returns:
            Name of selected tool or None if no specific tool is appropriate
        """
        # For code-related questions, use python tool
        if any(term in question.lower() for term in [
            "code", "function", "write a", "implement", "program", 
            "script", "algorithm", "compute", "calculate"
        ]):
            return "python"
            
        # For questions that seek a definitive answer, use final_answer
        if any(term in question.lower() for term in [
            "what is", "who is", "when did", "where is", "how many",
            "why does", "explain", "define", "describe"
        ]):
            return "final_answer"
            
        # Default case - no specific tool selected
        return None
    
    def _postprocess_answer(self, answer: str, question: str) -> str:
        """Clean up and format the answer."""
        # Handle different answer types
        if not isinstance(answer, str):
            answer = str(answer)
        
        # For chess questions, extract just the algebraic notation
        if "chess" in question.lower() and "best move" in question.lower():
            # Look for chess moves in algebraic notation
            chess_move_pattern = r'\b([a-hA-H][1-8]|[KQRBNP][a-h][1-8]|O-O|O-O-O)\b'
            moves = re.findall(chess_move_pattern, answer)
            if moves:
                # Return the last found move as it's likely the conclusion
                return moves[-1]
        
        # Extract the answer from code blocks if present
        code_block_pattern = r"```.*?\n(.*?)```"
        code_blocks = re.findall(code_block_pattern, answer, re.DOTALL)
        if code_blocks and any(term in question.lower() for term in ["code", "function", "implementation"]):
            # If asking for code and there's a code block, return just the code
            return code_blocks[-1].strip()
        
        # For yes/no questions, try to extract just the yes or no
        if "yes or no" in question.lower():
            yes_no_pattern = r'\b(yes|no)\b'
            matches = re.findall(yes_no_pattern, answer.lower())
            if matches:
                return matches[-1].capitalize()
        
        # Remove CodeAgent formatting if present
        if answer.startswith("Thoughts:"):
            # Remove "Thoughts:" and any leading/trailing whitespace
            cleaned = re.sub(r'^Thoughts:\s*', '', answer, flags=re.MULTILINE)
            # If there's a line that says "No code needed" or similar, remove it
            cleaned = re.sub(r'\n+No code needed.*$', '', cleaned, flags=re.MULTILINE)
            return cleaned.strip()
        
        return answer.strip() 