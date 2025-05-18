#!/usr/bin/env python3
"""
Final Answer Processor

This module provides a final post-processing step to convert verbose LLM answers into 
extremely concise responses that match exactly what evaluation systems expect.
"""

import os
import re
import json
import logging
from typing import Dict, Any, Optional, Union, List
import time
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('logs', 'answer_processor.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('final_answer_processor')

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

class FinalAnswerProcessor:
    """
    A processor that transforms verbose model answers into extremely concise, 
    exact-match responses suitable for automated evaluation systems.
    """
    
    def __init__(self, openai_api_key: Optional[str] = None, openrouter_api_key: Optional[str] = None):
        """
        Initialize the processor with API keys.
        
        Args:
            openai_api_key: OpenAI API key
            openrouter_api_key: OpenRouter API key
        """
        # Use provided keys or try to get from environment
        self.openai_api_key = openai_api_key or os.environ.get("OPENAI_API_KEY")
        self.openrouter_api_key = openrouter_api_key or os.environ.get("OPENROUTER_API_KEY")
        
        # Determine which API to use based on available keys
        if self.openrouter_api_key:
            self.api_type = "openrouter"
            self.api_key = self.openrouter_api_key
            # Import appropriate module
            try:
                from openrouter import OpenRouter
                self.api = OpenRouter(api_key=self.api_key)
            except ImportError:
                # Fallback to bare requests if package not available
                self.api = None
        elif self.openai_api_key:
            self.api_type = "openai"
            self.api_key = self.openai_api_key
            # Import appropriate module
            try:
                from openai import OpenAI
                self.api = OpenAI(api_key=self.api_key)
            except ImportError:
                # Fallback to bare requests if package not available
                self.api = None
        else:
            logger.warning("No API keys available for answer processing")
            self.api_type = None
            self.api_key = None
            self.api = None
    
    def _detect_answer_format(self, question: str) -> Dict[str, Any]:
        """
        Analyze the question to detect required answer format.
        
        Args:
            question: The original question
            
        Returns:
            Dictionary with format requirements
        """
        format_info = {
            "numeric_answer": False,
            "list_answer": False,
            "alphabetical": False,
            "comma_separated": False,
            "exact_match": False,
            "code_answer": False,
            "yes_no_answer": False
        }
        
        # Check for numeric indicators
        numeric_patterns = [
            r'\bhow many\b', r'\bcount\b', r'\bnumber of\b', r'\bamount\b', 
            r'\btotal\b', r'\bsum\b', r'\baverage\b', r'\bmean\b'
        ]
        for pattern in numeric_patterns:
            if re.search(pattern, question.lower()):
                format_info["numeric_answer"] = True
                break
        
        # Check for list indicators
        list_patterns = [
            r'\blist\b', r'\benumerate\b', r'\ball of the\b', r'\ball the\b',
            r'\bname all\b', r'\bidentify all\b'
        ]
        for pattern in list_patterns:
            if re.search(pattern, question.lower()):
                format_info["list_answer"] = True
                break
        
        # Check for alphabetical ordering requirement
        if format_info["list_answer"] and re.search(r'\balphabet', question.lower()):
            format_info["alphabetical"] = True
        
        # Check for comma-separated requirement
        if format_info["list_answer"] and re.search(r'\bcomma[ -]separated\b', question.lower()):
            format_info["comma_separated"] = True
        
        # Check for exact match requirements
        exact_match_patterns = [
            r'\bexact\b', r'\bprecisely\b', r'\bspecifically\b', 
            r'\bonly\b', r'\bjust\b', r'\bverbatim\b'
        ]
        for pattern in exact_match_patterns:
            if re.search(pattern, question.lower()):
                format_info["exact_match"] = True
                break
        
        # Check for code answers
        if re.search(r'\bcode\b|\bfunction\b|\bimplementation\b|\bprogram\b', question.lower()):
            format_info["code_answer"] = True
        
        # Check for yes/no questions
        if re.search(r'\byes or no\b|\byes/no\b|\btrue or false\b', question.lower()):
            format_info["yes_no_answer"] = True
        
        return format_info
    
    def _format_answer_with_llm(self, question: str, verbose_answer: str) -> str:
        """
        Use an LLM to format the answer according to the precise requirements.
        
        Args:
            question: The original question
            verbose_answer: The verbose answer to format
            
        Returns:
            Formatted concise answer
        """
        # System prompt to enforce strict formatting
        system_prompt = """
        You are a strict answer formatter that converts verbose answers into minimal, exact responses.

        Your ONLY job is to extract the precise, minimal answer from longer text. Never explain, justify, or add context.

        The ideal answer is:
        - One word, number, or short phrase
        - No articles (the, a, an)
        - No punctuation except when specifically requested
        - No units unless explicitly requested
        - No explanations, context, or hedging

        For lists:
        - Format exactly as requested (comma-separated, alphabetical, etc.)
        - Include only the items, not descriptions of the items

        You will be penalized severely for any:
        - Explanations or reasoning
        - Phrases like "the answer is" or "based on"
        - Additional context
        - Uncertainties or hedging
        - Politeness markers
        """
        
        # User prompt with question and verbose answer
        user_prompt = f"""
        Convert this verbose answer into the shortest possible exact response for an automated evaluation system. 
        The answer must be fewer than 10 words, ideally just 1-3 words or a number.

        Question: {question}
        Verbose answer: {verbose_answer}

        Format precisely as demanded in the question (alphabetical order, comma-separated, etc.).
        Provide ONLY the minimal answer with no explanation or introduction.
        """
        
        # Try to use API library if available
        if self.api is not None:
            try:
                if self.api_type == "openrouter":
                    # OpenRouter API call
                    response = self.api.chat.completions.create(
                        model="anthropic/claude-3-haiku",  # Using Claude for better instruction following
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ]
                    )
                    return response.choices[0].message.content.strip()
                elif self.api_type == "openai":
                    # OpenAI API call
                    response = self.api.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ]
                    )
                    return response.choices[0].message.content.strip()
            except Exception as e:
                logger.error(f"Error using API library: {e}")
                # Fall back to pattern-based extraction
        
        # If API isn't available or failed, fall back to pattern-based extraction
        return self._extract_answer_with_patterns(question, verbose_answer)
    
    def _extract_answer_with_patterns(self, question: str, verbose_answer: str) -> str:
        """
        Extract answers using regex patterns when API calls aren't possible.
        
        Args:
            question: The original question
            verbose_answer: The verbose answer to format
            
        Returns:
            Extracted concise answer
        """
        # Clean up answer
        cleaned_answer = verbose_answer.strip()
        
        # Remove common prefixes
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
            r"^This indicates that ",
        ]
        
        for prefix in prefixes_to_remove:
            cleaned_answer = re.sub(prefix, "", cleaned_answer, flags=re.IGNORECASE | re.DOTALL)
        
        # Format detection
        format_info = self._detect_answer_format(question)
        
        # Handle specific format types
        if format_info["numeric_answer"]:
            # Extract numbers
            numbers = re.findall(r"(\d+(?:\.\d+)?)", cleaned_answer)
            if numbers:
                return numbers[0]
        
        if format_info["yes_no_answer"]:
            # Extract yes/no
            if re.search(r'\b(yes|yeah|yep|correct|right|true|affirmative)\b', cleaned_answer.lower()):
                return "Yes"
            elif re.search(r'\b(no|nope|not|false|negative|incorrect)\b', cleaned_answer.lower()):
                return "No"
        
        if format_info["list_answer"]:
            # Special case for "the following [items]:" pattern
            list_match = re.search(r'(?:contains|contains the following|includes|has)(?:\s+the)?\s+(?:\w+)?:\s*(.*?)(?:\.|$)', cleaned_answer, re.IGNORECASE | re.DOTALL)
            
            if list_match:
                # Extract items directly from the matched text
                list_text = list_match.group(1).strip()
                
                # Split by commas and "and"
                items = re.split(r',\s*(?:and\s+)?|\s+and\s+', list_text)
                
                # Clean and filter items
                cleaned_items = []
                for item in items:
                    # Remove articles, labels, and punctuation
                    clean_item = re.sub(r'^(?:the|a|an)\s+', '', item, flags=re.IGNORECASE)
                    clean_item = re.sub(r'\s*\(.*?\)', '', clean_item)  # Remove parenthetical info
                    clean_item = clean_item.strip('.,;:"\'')
                    
                    # Skip empty items or category labels
                    if clean_item and not re.search(r':\s*$', clean_item):
                        cleaned_items.append(clean_item)
                
                # Sort if required
                if format_info["alphabetical"] and cleaned_items:
                    cleaned_items = sorted(cleaned_items)
                
                if cleaned_items:
                    return ", ".join(cleaned_items)
            
            # Fallback to more generic extraction if needed
            comma_lists = re.findall(r'([^,.]+(?:,\s*[^,.]+)+)', cleaned_answer)
            if comma_lists:
                best_list = max(comma_lists, key=len)  # Take the longest comma-separated list
                items = [item.strip() for item in re.split(r',\s*', best_list) if item.strip()]
                
                # Clean items
                cleaned_items = []
                for item in items:
                    # Remove any category labels (words followed by colon)
                    if ":" in item:
                        item = item.split(":", 1)[1].strip()
                    
                    # Remove articles
                    clean_item = re.sub(r'^(?:the|a|an)\s+', '', item, flags=re.IGNORECASE)
                    clean_item = clean_item.strip('.,;:"\'')
                    
                    if clean_item:
                        cleaned_items.append(clean_item)
                
                # Sort if required
                if format_info["alphabetical"] and cleaned_items:
                    cleaned_items = sorted(cleaned_items)
                
                if cleaned_items:
                    return ", ".join(cleaned_items)
        
        if format_info["code_answer"]:
            # Extract code blocks
            code_pattern = r'```(?:.*?)\n(.*?)```'
            code_matches = re.findall(code_pattern, cleaned_answer, re.DOTALL)
            if code_matches:
                return code_matches[0].strip()
        
        # For any other types, try to extract the first sentence if it's short
        sentences = re.split(r'(?<=[.!?])\s+', cleaned_answer, 1)
        if len(sentences) > 0 and len(sentences[0].split()) <= 10:
            # Clean up the sentence (remove trailing period, etc.)
            return sentences[0].rstrip('.!? "\'')
        
        # If all else fails, return the first 50 characters with an ellipsis
        if len(cleaned_answer) > 50:
            return cleaned_answer[:50].rstrip() + "..."
        
        return cleaned_answer
    
    def _validate_format(self, answer: str, question: str) -> str:
        """
        Validate and fix formatting issues with the answer.
        
        Args:
            answer: The processed answer
            question: The original question
            
        Returns:
            Validated and corrected answer
        """
        # Detect required format
        format_info = self._detect_answer_format(question)
        
        # Remove trailing punctuation unless specifically required
        if not re.search(r'punctuation|with periods|with commas', question.lower()):
            answer = answer.rstrip('.!?,:;')
        
        # Validate numeric answers
        if format_info["numeric_answer"]:
            # Try to extract just the number if there's text
            numbers = re.findall(r"(\d+(?:\.\d+)?)", answer)
            if numbers:
                answer = numbers[0]
        
        # Validate list answers
        if format_info["list_answer"]:
            # Ensure items are properly formatted
            if format_info["comma_separated"] and "," not in answer:
                # If items are separated by spaces, convert to commas
                items = answer.split()
                answer = ", ".join(items)
            
            # Ensure alphabetical order if required
            if format_info["alphabetical"]:
                items = [item.strip() for item in answer.split(",")]
                answer = ", ".join(sorted(items))
        
        # Remove any "the answer is" prefix that might remain
        answer = re.sub(r'^(the answer is|answer:|result:|result is)\s*', '', answer, flags=re.IGNORECASE)
        
        # Final trim
        return answer.strip()
    
    def process_answer(self, original_question: str, verbose_answer: str) -> str:
        """
        Process a verbose answer into a concise final answer.
        
        Args:
            original_question: The original question
            verbose_answer: The verbose answer from the model
            
        Returns:
            Concise, formatted answer suitable for evaluation
        """
        logger.info(f"Processing answer for question: {original_question[:100]}...")
        
        # Step 1: Format the answer using LLM if available
        try:
            concise_answer = self._format_answer_with_llm(original_question, verbose_answer)
        except Exception as e:
            logger.warning(f"Error in LLM formatting: {e}. Falling back to pattern extraction.")
            concise_answer = self._extract_answer_with_patterns(original_question, verbose_answer)
        
        # Step 2: Validate and correct the format
        final_answer = self._validate_format(concise_answer, original_question)
        
        # Log the transformation
        logger.info(f"Transformed answer: '{verbose_answer[:100]}...' -> '{final_answer}'")
        
        return final_answer

# Instantiate a global processor for easy imports
processor = FinalAnswerProcessor()

def process_final_answer(question: str, verbose_answer: str) -> str:
    """
    Utility function to process a final answer without creating a new processor.
    
    Args:
        question: The original question
        verbose_answer: The verbose answer from the model
        
    Returns:
        Concise, formatted answer suitable for evaluation
    """
    return processor.process_answer(question, verbose_answer)

# Example usage
if __name__ == "__main__":
    # Test with examples
    examples = [
        {
            "question": "How many studio albums did Mercedes Sosa release between 2000 and 2009?",
            "verbose_answer": "Based on my analysis, Mercedes Sosa published 4 studio albums between 2000 and 2009."
        },
        {
            "question": "What is the NASA award number that supported the work?",
            "verbose_answer": "The NASA award number that supported the work was NAS5-26555."
        },
        {
            "question": "List all vegetables found in the recipe, alphabetically.",
            "verbose_answer": "The recipe contains the following vegetables: tomatoes, onions, bell peppers, garlic, and carrots."
        }
    ]
    
    processor = FinalAnswerProcessor()
    
    for example in examples:
        print(f"Question: {example['question']}")
        print(f"Verbose: {example['verbose_answer']}")
        print(f"Concise: {processor.process_answer(example['question'], example['verbose_answer'])}")
        print("---") 