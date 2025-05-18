#!/usr/bin/env python3
"""
Agent Adapter Module

This module provides a compatibility layer to ensure the new agent implementations
(OpenRouter and OpenAI) can be used with the original app.py interface.
"""

import os
from typing import Optional, Dict, Any, Union
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Try to load from .env file in the current directory
    env_path = Path('.env')
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
    else:
        # Try to load from the full path (for the specific case mentioned)
        specific_path = Path('/Users/giovannigabriele/Documents/Code/HuggingFaceAgent/Final_Assignment_Template/.env')
        if specific_path.exists():
            load_dotenv(dotenv_path=specific_path)
except ImportError:
    print("Warning: python-dotenv not installed. Environment variables must be set manually.")

# Import the implementation that's currently active
try:
    from agent import SmolAgent as BaseSmolAgent
except ImportError:
    # If agent.py doesn't exist, try to import from specific implementations
    try:
        from openrouter_agent import SmolAgent as BaseSmolAgent
        CURRENT_IMPLEMENTATION = "openrouter"
    except ImportError:
        try:
            from openai_agent import SmolAgent as BaseSmolAgent
            CURRENT_IMPLEMENTATION = "openai"
        except ImportError:
            raise ImportError("No SmolAgent implementation found. Please run update_agent.py first.")

class SmolAgent:
    """
    Adapter class that provides a compatibility layer for the app.py interface.
    This adapter accepts the original parameters (hf_token, etc.) but uses
    the new implementations under the hood.
    """
    
    def __init__(self, 
                 hf_token: Optional[str] = None, 
                 use_mock: bool = False,
                 model_name: Optional[str] = None,
                 **kwargs):
        """
        Initialize the SmolAgent adapter.
        
        Args:
            hf_token: The Hugging Face token (not used, kept for compatibility)
            use_mock: Whether to use a mock model (not used, kept for compatibility)
            model_name: The model name (will be mapped to appropriate API model)
            **kwargs: Additional arguments passed to the real implementation
        """
        # Map model names from original implementation to new implementations
        model_mapping = {
            # OpenRouter models
            "openrouter": {
                "gpt-3.5-turbo": "openai/gpt-3.5-turbo",
                "gpt-4": "openai/gpt-4",
                "mistral-7b": "mistralai/Mistral-7B-Instruct-v0.2", 
                "llama-3": "meta-llama/Meta-Llama-3-8B-Instruct",
                "claude-3-haiku": "anthropic/claude-3-haiku",
                "claude-3-sonnet": "anthropic/claude-3-sonnet",
                "gemma-7b": "google/gemma-7b-it",
                None: "anthropic/claude-3-haiku",  # Default model
            },
            # OpenAI models
            "openai": {
                "gpt-3.5-turbo": "gpt-3.5-turbo",
                "gpt-4": "gpt-4",
                "mistral-7b": "gpt-3.5-turbo",  # Fallback
                "llama-3": "gpt-3.5-turbo",  # Fallback 
                "claude-3-haiku": "gpt-3.5-turbo",  # Fallback
                "claude-3-sonnet": "gpt-3.5-turbo",  # Fallback
                "gemma-7b": "gpt-3.5-turbo",  # Fallback
                None: "gpt-3.5-turbo",  # Default model
            }
        }
        
        # Determine which implementation is being used
        implementation = os.environ.get("SMOL_IMPLEMENTATION", "openrouter")
        
        # Map the model name
        if model_name:
            mapped_model = model_mapping[implementation].get(model_name, model_mapping[implementation][None])
        else:
            mapped_model = model_mapping[implementation][None]
        
        # Print environment variables for debugging
        openrouter_key = os.environ.get("OPENROUTER_API_KEY")
        openai_key = os.environ.get("OPENAI_API_KEY")
        print(f"OpenRouter API Key available: {bool(openrouter_key)}")
        print(f"OpenAI API Key available: {bool(openai_key)}")
        
        # Initialize the appropriate agent with the correct parameters
        if implementation == "openrouter":
            # OpenRouter implementation
            self.agent = BaseSmolAgent(
                openrouter_api_key=os.environ.get("OPENROUTER_API_KEY"),
                model_id=mapped_model
            )
        else:
            # OpenAI implementation
            self.agent = BaseSmolAgent(
                openai_api_key=os.environ.get("OPENAI_API_KEY"),
                model_id=mapped_model
            )
        
        # Store original parameters for compatibility
        self.use_mock = use_mock
        self.model_name = model_name
        self.hf_token = hf_token
    
    def __call__(self, question: str, file_path: Optional[str] = None, file_name: Optional[str] = None, task_id: str = None) -> str:
        """
        Pass the call to the actual implementation.
        
        Args:
            question: The question to answer
            file_path: Optional path to a file that may be required
            file_name: Backward compatibility parameter (will be mapped to file_path)
            task_id: Optional task ID for tracking
            
        Returns:
            The answer to the question
        """
        # For backward compatibility - map file_name to file_path if provided
        if file_name is not None and file_path is None:
            file_path = file_name
            
        return self.agent(question, file_path, task_id)
    
    def postprocess_answer(self, answer: str, question_type: str, question: str) -> str:
        """
        For compatibility with the original SmolAgent interface.
        Falls back to the _postprocess_answer method in the actual implementation.
        """
        if hasattr(self.agent, 'postprocess_answer'):
            return self.agent.postprocess_answer(answer, question_type, question)
        elif hasattr(self.agent, '_postprocess_answer'):
            return self.agent._postprocess_answer(answer, question)
        return answer 