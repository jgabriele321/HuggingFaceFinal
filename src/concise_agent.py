#!/usr/bin/env python3
"""
Concise SmolAgent Implementation

This agent focuses on providing extremely concise, exact-match answers
by applying extensive post-processing to model outputs.
"""

import os
import re
import json
import logging
import time
import random
from typing import Optional, List, Dict, Any, Union
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ConciseAgent")

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    env_path = Path('.env')
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
    else:
        specific_path = Path('/Users/giovannigabriele/Documents/Code/HuggingFaceAgent/Final_Assignment_Template/.env')
        if specific_path.exists():
            load_dotenv(dotenv_path=specific_path)
except ImportError:
    logger.warning("python-dotenv not installed. Environment variables must be set manually.")

# Import the base model implementation
try:
    # Use OpenRouter by default
    implementation = os.environ.get("SMOL_IMPLEMENTATION", "openrouter")
    
    if implementation == "openrouter":
        from openrouter_agent import OpenRouterModel as BaseModel
        model_key = os.environ.get("OPENROUTER_API_KEY")
        model_id = os.environ.get("OPENROUTER_MODEL", "anthropic/claude-3-haiku")
        logger.info(f"Using OpenRouter implementation with model: {model_id}")
    else:
        from openai_agent import OpenAIModel as BaseModel
        model_key = os.environ.get("OPENAI_API_KEY")
        model_id = os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo")
        logger.info(f"Using OpenAI implementation with model: {model_id}")
except ImportError:
    logger.error("Failed to import base model. Make sure openrouter_agent.py or openai_agent.py exists.")
    raise

class ConciseModel:
    """
    A wrapper around the base model that applies post-processing to get concise answers.
    """
    
    def __init__(self, api_key: Optional[str] = None, model_id: Optional[str] = None):
        """Initialize the concise model with the base model."""
        self.base_model = BaseModel(api_key=api_key, model_id=model_id)
        
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate a response and post-process it for conciseness."""
        # Add explicit instructions to the prompt
        enhanced_prompt = self._enhance_prompt(prompt)
        
        # Get the base response
        raw_response = self.base_model.generate(enhanced_prompt, **kwargs)
        
        # Extract content from the response
        if hasattr(raw_response, 'content'):
            content = raw_response.content
        else:
            content = str(raw_response)
            
        # Post-process to get a concise answer
        concise_answer = self._post_process_answer(content, prompt)
        
        return concise_answer
        
    def _enhance_prompt(self, prompt: str) -> str:
        """Add explicit instructions to the prompt to encourage concise answers."""
        instruction = """
Important instructions: Provide ONLY the essential answer with no explanation, reasoning, or context.
- For numerical questions, just provide the number (e.g., "42" not "The answer is 42")
- For lists, provide comma-separated items without explanations
- For identifiers or codes, provide just the exact code/identifier
- Do not include phrases like "the answer is" or "based on the information"
- If a specific format is requested (alphabetical, etc.), follow it exactly
"""
        # Check if the prompt appears to be a system message or regular question
        if "system:" in prompt.lower() or "user:" in prompt.lower():
            # This is likely a chat format prompt, add our instruction as a system message
            return f"system: {instruction}\n{prompt}"
        else:
            # This is a regular prompt, prepend our instruction
            return f"{instruction}\n\nQuestion: {prompt}"
    
    def _post_process_answer(self, answer: str, original_prompt: str) -> str:
        """
        Apply extensive post-processing to get a concise, exact-match answer.
        """
        # First, check if there's a code block and extract its content
        code_pattern = r"```(?:.*?)\n(.*?)```"
        code_matches = re.findall(code_pattern, answer, re.DOTALL)
        if code_matches and "code" in original_prompt.lower():
            # For code requests, return just the code (without the markdown markers)
            return code_matches[0].strip()
        
        # Remove typical prefixes that models add
        prefixes_to_remove = [
            r"^The answer is:?\s*",
            r"^Answer:?\s*",
            r"^The result is:?\s*",
            r"^Based on .*?, ",
            r"^According to .*?, ",
            r"^From the .*?, ",
            r"^After analyzing .*?, ",
            r"^I found that ",
            r"^It appears that ",
            r"^The .* shows that ",
            r"^The .* indicates that ",
        ]
        
        cleaned_answer = answer
        for prefix in prefixes_to_remove:
            cleaned_answer = re.sub(prefix, "", cleaned_answer, flags=re.IGNORECASE | re.DOTALL)
        
        # Handle numeric answers - extract just the numbers if that's what was asked
        if self._is_numeric_question(original_prompt):
            # Look for numbers with optional units or surrounding text
            numbers = re.findall(r"(\d+(?:\.\d+)?)", cleaned_answer)
            if numbers:
                # Check if multiple numbers exist (might be a range or list)
                if len(numbers) > 1 and "," in cleaned_answer:
                    # This appears to be a comma-separated list of numbers
                    return ", ".join(numbers)
                # Otherwise return the first number found
                return numbers[0]
        
        # Handle list formatting requests
        if "list" in original_prompt.lower() and ("alphabetical" in original_prompt.lower() or 
                                                "alphabetized" in original_prompt.lower()):
            # This appears to be asking for a list in alphabetical order
            items = [item.strip() for item in re.split(r',|\n', cleaned_answer) if item.strip()]
            return ", ".join(sorted(items))
        
        # Remove any remaining explanation text after the direct answer
        # Look for common pattern where the answer is given, then explanation follows
        parts = re.split(r'\.\s+', cleaned_answer, 1)
        if len(parts) > 1 and len(parts[0].split()) < 10:
            # If the first sentence is short, it's likely just the answer
            cleaned_answer = parts[0].strip()
        
        # Remove any remaining period at the end (common in language model outputs)
        cleaned_answer = cleaned_answer.rstrip('.')
        
        # Final cleanup - remove extra whitespace and quotes
        cleaned_answer = cleaned_answer.strip()
        cleaned_answer = re.sub(r'^["\']|["\']$', '', cleaned_answer)
        
        return cleaned_answer
    
    def _is_numeric_question(self, prompt: str) -> bool:
        """Check if the question is likely asking for a numeric answer."""
        numeric_indicators = [
            r"how many", r"count", r"number of", r"amount", r"total",
            r"sum", r"average", r"mean", r"median", r"percentage",
            r"ratio", r"rate", r"frequency", r"quantity"
        ]
        
        prompt_lower = prompt.lower()
        for indicator in numeric_indicators:
            if re.search(r'\b' + indicator + r'\b', prompt_lower):
                return True
        
        return False

class SmolAgent:
    """
    A concise SmolAgent that provides exact-match answers for benchmark evaluation.
    """
    
    def __init__(self, 
                 api_key: Optional[str] = None, 
                 model_id: Optional[str] = None,
                 hf_token: Optional[str] = None,  # For compatibility
                 use_mock: bool = False,          # For compatibility
                 model_name: Optional[str] = None # For compatibility
                ):
        """Initialize the agent with optional API key and model ID."""
        # Initialize the model with specified or default parameters
        self.model = ConciseModel(api_key=api_key, model_id=model_id)
        
        # Store compatibility parameters
        self.hf_token = hf_token
        self.use_mock = use_mock
        
    def __call__(self, question: str, file_path: Optional[str] = None, file_name: Optional[str] = None, task_id: str = None) -> str:
        """
        Process a question and return a concise, exact-match answer.
        
        Args:
            question: The question to answer
            file_path: Optional path to a file that may be required
            file_name: Backward compatibility parameter (will be mapped to file_path)
            task_id: Optional task ID for tracking
            
        Returns:
            A concise, exact-match answer
        """
        # For backward compatibility - map file_name to file_path if provided
        if file_name is not None and file_path is None:
            file_path = file_name
        
        # Prepare the prompt
        prompt = question
        
        # Add file content to the prompt if provided
        if file_path and os.path.exists(file_path):
            prompt += f"\n\nThe question refers to a file. Here's the file information:"
            
            try:
                # Read the file content
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    file_content = f.read(2000)  # Read first 2000 chars to avoid overwhelming the model
                    
                prompt += f"\n\nFile path: {file_path}"
                prompt += f"\n\nFile content (partial):\n{file_content}"
                
                # Add a note if the file was truncated
                if len(file_content) >= 2000:
                    prompt += "\n\n[File content truncated due to size]"
            except Exception as e:
                logger.warning(f"Error reading file {file_path}: {str(e)}")
                prompt += f"\n\nCould not read file content: {str(e)}"
        
        # Process with retries
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Get the response
                response = self.model.generate(prompt)
                
                # Apply post-processing specific to question type
                answer = self.postprocess_answer(response, question)
                
                return answer
            except Exception as e:
                logger.error(f"Error processing question (attempt {attempt+1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    # Exponential backoff
                    backoff = (2 ** attempt) + random.uniform(0, 1)
                    time.sleep(backoff)
                else:
                    return "ERROR: Unable to generate answer after multiple attempts."
    
    def postprocess_answer(self, answer: str, question_type: str = None, question: str = None) -> str:
        """
        Apply specialized post-processing based on question type.
        This is the public method used by the caller.
        
        Args:
            answer: The raw answer from the model
            question_type: The type of question (unused but kept for compatibility)
            question: The original question text
            
        Returns:
            The post-processed answer
        """
        # For backward compatibility, handle different parameters
        if question is None:
            question = question_type if question_type is not None else ""
        
        # Basic post-processing
        answer = answer.strip()
        
        # Check for specific answer types and format accordingly
        
        # Check for yes/no questions
        if self._is_yes_no_question(question):
            yes_pattern = r'\b(yes|yeah|yep|correct|right|true|affirmative)\b'
            no_pattern = r'\b(no|nope|not|false|negative|incorrect)\b'
            
            if re.search(yes_pattern, answer.lower()):
                return "Yes"
            elif re.search(no_pattern, answer.lower()):
                return "No"
        
        # Check for list questions that need formatting
        list_indicators = ["list", "name all", "enumerate"]
        if any(indicator in question.lower() for indicator in list_indicators):
            # This is likely a list question
            if "," in answer:
                # Handle comma-separated items
                items = [item.strip() for item in answer.split(",")]
                # Check if alphabetical order is required
                if "alphabetical" in question.lower() or "alphabetized" in question.lower():
                    items = sorted(items)
                return ", ".join(items)
        
        # Return the answer as is (already processed by the model class)
        return answer
    
    def _is_yes_no_question(self, question: str) -> bool:
        """Check if the question is likely a yes/no question."""
        # Common patterns for yes/no questions
        yes_no_patterns = [
            r"^(is|are|does|do|has|have|can|could|should|would|will)",
            r"\?$",
            r"true or false",
            r"yes or no"
        ]
        
        question_lower = question.lower()
        for pattern in yes_no_patterns:
            if re.search(pattern, question_lower):
                return True
                
        return False 