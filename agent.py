import os
import json
import re
import base64
import requests
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import io
from PIL import Image
import chess
import chess.svg
import pandas as pd
from dotenv import load_dotenv

from smolagents import CodeAgent, InferenceClientModel, Tool, tool

# Load environment variables from .env file
load_dotenv()

# Constants
FILES_DIR = "files"
CACHE_DIR = "cache"
DEFAULT_API_URL = "https://agents-course-unit4-scoring.hf.space"

# Ensure directories exist
os.makedirs(FILES_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)

# For testing without a valid HF token - simple model mock
class MockModel:
    """Mock model for testing without a Hugging Face API token"""
    
    def generate(self, prompt):
        # Simple rules to return fixed answers for different question types
        prompt_lower = prompt.lower()
        
        if "2 + 2" in prompt_lower:
            return "The answer is 4."
        elif "chess" in prompt_lower:
            return "After analyzing the chess position, the best move is e4."
        elif "image" in prompt_lower:
            return "The image shows a landscape with mountains and trees."
        else:
            return "This is a mock answer for testing purposes. In production, this would use the real LLM."
            
    def __call__(self, prompt):
        return self.generate(prompt)

# Define specialized tools for the agent
@tool
def analyze_image(image_path: str) -> str:
    """
    Analyze an image and provide a detailed description of what's in it.
    
    Args:
        image_path: Path to the image file
    
    Returns:
        A detailed description of what's in the image
    """
    try:
        # Open the image to verify it exists and is valid
        img = Image.open(image_path)
        width, height = img.size
        format_type = img.format
        mode = img.mode
        
        return (
            f"Image analysis of {image_path}:\n"
            f"- Dimensions: {width}x{height} pixels\n"
            f"- Format: {format_type}\n"
            f"- Mode: {mode}\n"
            f"- The image is now ready for your analysis. Describe what you see in detail."
        )
    except Exception as e:
        return f"Error analyzing image: {str(e)}"

@tool
def analyze_chess_position(image_path: str) -> str:
    """
    Analyze a chess position from an image and provide a detailed FEN notation and position assessment.
    
    Args:
        image_path: Path to the image of the chess position
    
    Returns:
        A detailed analysis of the chess position
    """
    try:
        # Open the image to verify it exists
        Image.open(image_path)
        
        return (
            f"Chess position image at {image_path}:\n"
            f"Please analyze this chess board image carefully. Focus on:\n"
            f"1. The positions of all pieces on the board\n"
            f"2. Whose turn it is to move (black or white)\n"
            f"3. The possible legal moves for the current player\n"
            f"4. Any tactical opportunities, threats, or winning sequences\n"
            f"5. If asked for algebraic notation, provide moves in the format like 'e4', 'Nf3', 'Bxh7+', etc."
        )
    except Exception as e:
        return f"Error analyzing chess image: {str(e)}"

@tool
def analyze_data_file(file_path: str) -> str:
    """
    Analyze a data file (CSV, JSON, TXT) and provide a summary of its contents.
    
    Args:
        file_path: Path to the data file
    
    Returns:
        A summary of the file's contents
    """
    try:
        file_ext = file_path.split('.')[-1].lower()
        
        if file_ext == 'csv':
            df = pd.read_csv(file_path)
            return f"CSV file analysis of {file_path}:\n- Shape: {df.shape}\n- Columns: {list(df.columns)}\n- First few rows:\n{df.head(3).to_string()}"
        
        elif file_ext == 'json':
            with open(file_path, 'r') as f:
                data = json.load(f)
            if isinstance(data, list):
                return f"JSON file analysis of {file_path}:\n- Contains a list with {len(data)} items\n- First item: {json.dumps(data[0], indent=2) if data else 'None'}"
            else:
                return f"JSON file analysis of {file_path}:\n- Contains an object with keys: {list(data.keys())}"
        
        elif file_ext in ['txt', 'md']:
            with open(file_path, 'r') as f:
                content = f.read(1000)  # Read first 1000 chars
            return f"Text file analysis of {file_path}:\n- First 1000 characters:\n{content}..."
        
        else:
            return f"Unsupported file type: {file_ext}. Please implement a handler for this file type."
            
    except Exception as e:
        return f"Error analyzing file: {str(e)}"

@tool
def execute_code(code: str) -> str:
    """
    Execute a code snippet and return the result.
    
    IMPORTANT: Only use for simple calculations, validations, or data transformations.
    Never use for code that could be harmful or access resources without permission.
    
    Args:
        code: Python code to execute
    
    Returns:
        Result of code execution
    """
    try:
        # Create a restricted local execution environment
        local_vars = {}
        
        # Execute the code in the restricted environment
        exec(code, {"__builtins__": {
            "abs": abs, "all": all, "any": any, "bin": bin, 
            "bool": bool, "bytearray": bytearray, "bytes": bytes, 
            "chr": chr, "complex": complex, "dict": dict, 
            "divmod": divmod, "enumerate": enumerate, "filter": filter, 
            "float": float, "format": format, "frozenset": frozenset, 
            "hash": hash, "hex": hex, "int": int, 
            "isinstance": isinstance, "issubclass": issubclass, "iter": iter, 
            "len": len, "list": list, "map": map, "max": max, 
            "min": min, "next": next, "oct": oct, "ord": ord, 
            "pow": pow, "print": print, "range": range, 
            "repr": repr, "reversed": reversed, "round": round, 
            "set": set, "slice": slice, "sorted": sorted, 
            "str": str, "sum": sum, "tuple": tuple, 
            "type": type, "zip": zip
        }}, local_vars)
        
        # Capture any output in local_vars
        if '_result' in local_vars:
            return str(local_vars['_result'])
        else:
            # Look for any assigned variables and return them
            return str(local_vars)
            
    except Exception as e:
        return f"Error executing code: {str(e)}"

@tool
def search_documentation(query: str) -> str:
    """
    Search for information related to a specific query in documentation.
    
    Args:
        query: The search query
    
    Returns:
        Relevant information from documentation
    """
    # This is a placeholder - in a real implementation, you might have
    # a more sophisticated search process
    common_topics = {
        "chess": "Chess is a board game played between two players on an 8x8 grid of squares. "
                 "Pieces include King, Queen, Rook, Bishop, Knight, and Pawn. "
                 "Moves are written in algebraic notation like e4, Nf3, or O-O for castling.",
                 
        "math": "Mathematical operations include: addition (+), subtraction (-), "
                "multiplication (*), division (/), exponentiation (**), modulo (%), etc. "
                "Python includes the 'math' module for advanced functions.",
                
        "code": "Python is a high-level programming language. Key concepts include variables, "
                "functions, conditionals (if/else), loops (for/while), and data structures "
                "like lists, dictionaries, sets, and tuples.",
    }
    
    # Check if the query matches any common topics
    for topic, info in common_topics.items():
        if topic.lower() in query.lower():
            return f"Documentation for '{topic}':\n{info}"
    
    return "No specific documentation found for that query. Please try a more specific search term like 'chess', 'math', or 'code'."

class SmolAgent:
    """
    An advanced agent built with smolagents for answering complex questions.
    """
    
    def __init__(self, hf_token: Optional[str] = None, api_url: str = DEFAULT_API_URL, use_mock: bool = False):
        """
        Initialize the SmolAgent.
        
        Args:
            hf_token: Hugging Face API token for model access
            api_url: API URL for fetching questions and files
            use_mock: Use mock model for testing without a valid token
        """
        # Try to get token from env var if not provided
        self.hf_token = hf_token or os.environ.get("HF_TOKEN")
        self.use_mock = use_mock
        
        if not self.hf_token and not self.use_mock:
            raise ValueError("Hugging Face API token is required. Either pass it directly, set HF_TOKEN environment variable, or use use_mock=True for testing.")
        
        self.api_url = api_url
        
        # Initialize model
        if self.use_mock:
            print("Using mock model for testing")
            self.model = MockModel()
        else:
            self.model = InferenceClientModel(
                model_id="meta-llama/Meta-Llama-3-70B-Instruct",
                token=self.hf_token
            )
        
        # Define tools
        self.tools = [
            analyze_image,
            analyze_chess_position,
            analyze_data_file,
            execute_code,
            search_documentation
        ]
        
        # Initialize agent with tools
        if not self.use_mock:
            self.agent = CodeAgent(
                tools=self.tools,
                model=self.model,
                verbosity_level=1,
                max_steps=10,  # Allow more steps for complex questions
                stream_outputs=False,
                additional_authorized_imports=[
                    "numpy", "pandas", "re", "math", "chess", 
                    "PIL", "io", "json", "base64"
                ]
            )
        
        # Initialize the cache
        self.cache = self._load_cache()
    
    def _load_cache(self) -> Dict[str, Any]:
        """Load the cache from disk."""
        cache_path = Path(CACHE_DIR) / "answers_cache.json"
        if cache_path.exists():
            try:
                with open(cache_path, "r") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading cache: {e}")
                return {}
        return {}
    
    def _save_cache(self) -> None:
        """Save the cache to disk."""
        cache_path = Path(CACHE_DIR) / "answers_cache.json"
        try:
            with open(cache_path, "w") as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            print(f"Error saving cache: {e}")
    
    def download_file(self, task_id: str, file_name: str) -> Optional[str]:
        """
        Download a file associated with a question.
        
        Args:
            task_id: The ID of the task/question
            file_name: The name of the file to download
            
        Returns:
            Path to the downloaded file or None if download failed
        """
        file_path = Path(FILES_DIR) / file_name
        
        # Check if file already exists
        if file_path.exists():
            print(f"File already exists: {file_path}")
            return str(file_path)
        
        # Try to download the file
        file_url = f"{self.api_url}/file/{task_id}"
        print(f"Downloading file: {file_name} from {file_url}")
        
        try:
            file_response = requests.get(file_url, timeout=30)
            file_response.raise_for_status()
            
            # Save the file
            with open(file_path, "wb") as f:
                f.write(file_response.content)
                
            print(f"✅ Successfully downloaded: {file_path}")
            return str(file_path)
            
        except Exception as e:
            print(f"❌ Error downloading file {file_name}: {str(e)}")
            return None
    
    def detect_question_type(self, question: str, file_name: Optional[str] = None) -> str:
        """
        Detect the type of question based on content and file type.
        
        Args:
            question: The question text
            file_name: Optional file name associated with the question
            
        Returns:
            The question type as a string
        """
        question_lower = question.lower()
        
        # First check for chess-related questions
        if "chess" in question_lower or "algebraic notation" in question_lower:
            return "chess"
            
        # Check for math/calculation questions
        elif any(term in question_lower for term in ["math", "calculate", "compute", "solve", "equation"]):
            return "math"
            
        # Check for coding questions
        elif any(term in question_lower for term in ["code", "program", "function", "algorithm"]):
            return "coding"
            
        # Check based on file extension if present
        elif file_name:
            ext = file_name.split('.')[-1].lower()
            if ext in ['png', 'jpg', 'jpeg', 'gif']:
                if "chess" in question_lower:
                    return "chess"
                return "image"
            elif ext in ['csv', 'json', 'txt', 'md']:
                return "data"
            elif ext in ['py', 'js', 'html', 'css']:
                return "coding"
                
        # Default to general if no specific type is detected
        return "general"
    
    def generate_question_hash(self, task_id: str, question: str) -> str:
        """
        Generate a unique hash for a question to use as cache key.
        
        Args:
            task_id: The ID of the question
            question: The question text
            
        Returns:
            A unique hash for the question
        """
        # Use task_id and question to generate a unique hash
        hash_input = f"{task_id}:{question}"
        return hashlib.md5(hash_input.encode()).hexdigest()
    
    def preprocess_question(self, question: str, question_type: str, file_path: Optional[str] = None) -> str:
        """
        Preprocess the question to provide better context to the agent.
        
        Args:
            question: The original question
            question_type: The detected question type
            file_path: Optional path to an attached file
            
        Returns:
            Processed question with additional context
        """
        processed_question = question
        
        if file_path:
            if question_type == "chess":
                processed_question = (
                    f"{question}\n\n"
                    f"This is a chess-related question. You should analyze the chess position in the image at {file_path} "
                    f"using the analyze_chess_position tool. After analysis, determine the best move using algebraic "
                    f"notation (e.g., 'e4', 'Nf3', etc.). Be precise and concise with your final answer."
                )
            elif question_type == "image":
                processed_question = (
                    f"{question}\n\n"
                    f"This question requires image analysis. You should analyze the image at {file_path} "
                    f"using the analyze_image tool to extract relevant information to answer the question."
                )
            elif question_type == "data":
                processed_question = (
                    f"{question}\n\n"
                    f"This question requires data analysis. You should analyze the data file at {file_path} "
                    f"using the analyze_data_file tool to extract relevant information to answer the question."
                )
            else:
                file_ext = file_path.split('.')[-1].lower()
                if file_ext in ['png', 'jpg', 'jpeg', 'gif']:
                    processed_question += f"\n\nThere is an image available at {file_path} that you can analyze using the analyze_image tool."
                elif file_ext in ['csv', 'json', 'txt', 'md']:
                    processed_question += f"\n\nThere is a data file available at {file_path} that you can analyze using the analyze_data_file tool."
        
        return processed_question
    
    def postprocess_answer(self, answer: str, question_type: str, question: str) -> str:
        """
        Clean up and format the answer based on the question type.
        
        Args:
            answer: The raw answer from the agent
            question_type: The detected question type
            question: The original question
            
        Returns:
            Processed answer
        """
        # Extract the answer if it's in a code block
        code_block_pattern = r"```.*?\n(.*?)```"
        code_blocks = re.findall(code_block_pattern, answer, re.DOTALL)
        if code_blocks:
            # Use the last code block as it's likely the final answer
            answer = code_blocks[-1].strip()
        
        # For chess questions, extract just the algebraic notation if present
        if question_type == "chess":
            # Look for chess moves in algebraic notation
            chess_move_pattern = r'\b([a-h][1-8]|[KQRBN][a-h][1-8]|[KQRBN]x[a-h][1-8]|O-O-O|O-O)\b'
            moves = re.findall(chess_move_pattern, answer)
            if moves:
                # Return the last found move as it's likely the conclusion
                return moves[-1]
            
            # Look for phrases like "best move is X" or "move: X"
            move_phrases = re.findall(r'(?:best move is|move:|move is|should play)\s+([a-zA-Z0-9][a-zA-Z0-9\+\#\=\-x]{1,7})', answer, re.IGNORECASE)
            if move_phrases:
                return move_phrases[-1]
        
        # For math questions, try to extract just the numeric answer
        elif question_type == "math":
            # Check if asked for specific format
            if "simplify" in question.lower():
                # Look for "simplified form is X" patterns
                simplified_pattern = r'(?:simplified form|simplify to|simplifies to|answer is)\s*(?:is|=|:)?\s*(.+?)(?:\.|$|\n)'
                matches = re.findall(simplified_pattern, answer, re.IGNORECASE)
                if matches:
                    return matches[-1].strip()
            
            # Look for "answer is X" or "result is X" patterns
            answer_pattern = r'(?:answer|result|solution)\s*(?:is|=|:)\s*([-+]?\d*\.?\d+)'
            matches = re.findall(answer_pattern, answer, re.IGNORECASE)
            if matches:
                return matches[-1]
            
            # Check for equation patterns
            equation_pattern = r'(\d+(?:\.\d+)?)\s*$'
            matches = re.findall(equation_pattern, answer)
            if matches:
                return matches[-1]
        
        # For yes/no questions, try to extract just the yes or no
        elif "yes or no" in question.lower():
            yes_no_pattern = r'\b(yes|no)\b'
            matches = re.findall(yes_no_pattern, answer.lower())
            if matches:
                return matches[-1].capitalize()
        
        # Return the full answer if no specific extraction is needed or possible
        return answer.strip()
    
    def __call__(self, question: str, task_id: str = None, file_name: str = None) -> str:
        """
        Process a question and return an answer.
        
        Args:
            question: The question to answer
            task_id: Optional task ID for caching and file downloads
            file_name: Optional file name associated with the question
            
        Returns:
            The answer to the question
        """
        # If task_id is provided, check cache first
        if task_id:
            question_hash = self.generate_question_hash(task_id, question)
            if question_hash in self.cache:
                print(f"Cache hit for task: {task_id}")
                return self.cache[question_hash]
        
        file_path = None
        if file_name and task_id:
            # Download the file if needed
            file_path = self.download_file(task_id, file_name)
        
        # Detect question type
        question_type = self.detect_question_type(question, file_name)
        print(f"Detected question type: {question_type}")
        
        # Preprocess the question
        processed_question = self.preprocess_question(question, question_type, file_path)
        
        try:
            # Run the agent
            if self.use_mock:
                # Use mock model directly
                raw_answer = self.model(processed_question)
            else:
                # Use the Code Agent
                raw_answer = self.agent.run(processed_question)
            
            # Postprocess the answer
            final_answer = self.postprocess_answer(str(raw_answer), question_type, question)
            
            # Cache the result if task_id is provided
            if task_id:
                question_hash = self.generate_question_hash(task_id, question)
                self.cache[question_hash] = final_answer
                self._save_cache()
            
            return final_answer
        except Exception as e:
            error_msg = f"Error running agent: {str(e)}"
            print(error_msg)
            return f"I encountered an error while trying to answer this question. Error: {str(e)}" 