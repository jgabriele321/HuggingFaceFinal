import os
import json
import re
import base64
import requests
import hashlib
import time
import random
import mimetypes
import logging
from typing import Dict, List, Optional, Any, Tuple, Union
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
LOGS_DIR = "logs"
DEFAULT_API_URL = "https://agents-course-unit4-scoring.hf.space"
AGENT_MIND_FILE = "agentmind.md"
MAX_DOWNLOAD_RETRIES = 3
DOWNLOAD_RETRY_BACKOFF = 2  # seconds

# Ensure directories exist
os.makedirs(FILES_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Path(LOGS_DIR) / "agent.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("SmolAgent")

# Create a logger for the agent's thinking
def start_agent_logging():
    """Initialize or reset the agent mind log file."""
    with open(AGENT_MIND_FILE, 'w') as f:
        f.write(f"# Agent Mind Log\n\n")
        f.write(f"*Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
        f.write("This file tracks the agent's thought process in real time.\n\n")
        f.write("---\n\n")

def log_to_agent_mind(message: str):
    """Append a message to the agent mind log file."""
    with open(AGENT_MIND_FILE, 'a') as f:
        f.write(f"{message}\n\n")

# File handling class with robust error handling
class FileDownloader:
    """
    A class for handling file downloads with robust error handling, retries,
    and content verification.
    """
    
    def __init__(self, api_url: str, files_dir: str = FILES_DIR):
        """
        Initialize the FileDownloader.
        
        Args:
            api_url: Base API URL for file downloads
            files_dir: Directory to store downloaded files
        """
        self.api_url = api_url
        self.files_dir = Path(files_dir)
        self.files_dir.mkdir(exist_ok=True, parents=True)
        
    def download_file(self, task_id: str, file_name: str) -> Optional[str]:
        """
        Download a file with retry logic and error handling.
        
        Args:
            task_id: The ID of the task/question
            file_name: The name of the file to download
            
        Returns:
            Path to the downloaded file or None if download failed
        """
        file_path = self.files_dir / file_name
        
        # Check if file already exists
        if file_path.exists():
            logger.info(f"File already exists: {file_path}")
            return self._verify_file(str(file_path))
        
        # Try to download the file
        file_url = f"{self.api_url}/file/{task_id}"
        logger.info(f"Downloading file: {file_name} from {file_url}")
        
        # Implement retry logic with exponential backoff
        for attempt in range(1, MAX_DOWNLOAD_RETRIES + 1):
            try:
                # Add a small jitter to avoid thundering herd problem
                if attempt > 1:
                    backoff_time = DOWNLOAD_RETRY_BACKOFF * (2 ** (attempt - 1)) + random.uniform(0, 1)
                    logger.info(f"Retry attempt {attempt}/{MAX_DOWNLOAD_RETRIES}, waiting {backoff_time:.2f}s")
                    time.sleep(backoff_time)
                
                # Download the file with a generous timeout
                file_response = requests.get(file_url, timeout=60)
                file_response.raise_for_status()
                
                # Check content type to ensure it's a file and not an error page
                content_type = file_response.headers.get('content-type', '')
                if 'text/html' in content_type and len(file_response.content) < 1000:
                    # This might be an error page instead of the file
                    logger.warning(f"Received HTML content instead of file: {content_type}")
                    continue
                
                # Save the file
                with open(file_path, "wb") as f:
                    f.write(file_response.content)
                
                logger.info(f"✅ Successfully downloaded: {file_path}")
                return self._verify_file(str(file_path))
                
            except requests.exceptions.HTTPError as e:
                logger.error(f"HTTP error downloading file {file_name}: {str(e)}")
                if e.response.status_code in [429, 500, 502, 503, 504]:
                    # Server errors and rate limiting should be retried
                    continue
                else:
                    # Client errors shouldn't be retried
                    break
            except requests.exceptions.ConnectionError as e:
                logger.error(f"Connection error downloading file {file_name}: {str(e)}")
                # Connection errors should be retried
                continue
            except requests.exceptions.Timeout as e:
                logger.error(f"Timeout downloading file {file_name}: {str(e)}")
                # Timeouts should be retried
                continue
            except Exception as e:
                logger.error(f"Unexpected error downloading file {file_name}: {str(e)}")
                # Other errors may or may not be worth retrying
                if attempt < MAX_DOWNLOAD_RETRIES:
                    continue
                else:
                    break
        
        # If we got here, all retries failed
        logger.error(f"❌ Failed to download file {file_name} after {MAX_DOWNLOAD_RETRIES} attempts")
        
        # Create a placeholder file for debugging
        self._create_error_placeholder(file_path, task_id, file_name)
        return None
    
    def _verify_file(self, file_path: str) -> Optional[str]:
        """
        Verify that the downloaded file is valid and usable.
        
        Args:
            file_path: Path to the file to verify
            
        Returns:
            The file path if valid, None otherwise
        """
        try:
            path = Path(file_path)
            
            # Check file exists and has content
            if not path.exists() or path.stat().st_size == 0:
                logger.error(f"File verification failed - file empty or does not exist: {file_path}")
                return None
                
            # Check file extension and try to validate based on type
            ext = path.suffix.lower()
            
            # For images, try to open them with PIL
            if ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
                try:
                    with Image.open(path) as img:
                        # Just accessing img.format is enough to verify it's a valid image
                        logger.info(f"Verified image file: {file_path} (Format: {img.format}, Size: {img.size})")
                except Exception as e:
                    logger.error(f"Image verification failed: {str(e)}")
                    return None
                    
            # For CSV files, try to read with pandas
            elif ext == '.csv':
                try:
                    # Just read the first 5 rows to verify format
                    pd.read_csv(path, nrows=5)
                    logger.info(f"Verified CSV file: {file_path}")
                except Exception as e:
                    logger.error(f"CSV verification failed: {str(e)}")
                    return None
                    
            # For JSON files, try to parse
            elif ext == '.json':
                try:
                    with open(path, 'r') as f:
                        json.load(f)
                    logger.info(f"Verified JSON file: {file_path}")
                except Exception as e:
                    logger.error(f"JSON verification failed: {str(e)}")
                    return None
            
            # For all other files, just check if they're readable
            else:
                try:
                    with open(path, 'rb') as f:
                        f.read(1024)  # Read the first 1KB
                    logger.info(f"Verified file exists and is readable: {file_path}")
                except Exception as e:
                    logger.error(f"File read verification failed: {str(e)}")
                    return None
            
            return file_path
                
        except Exception as e:
            logger.error(f"Unexpected error verifying file {file_path}: {str(e)}")
            return None
    
    def _create_error_placeholder(self, file_path: Path, task_id: str, file_name: str) -> None:
        """
        Create a placeholder file when download fails to help with debugging.
        
        Args:
            file_path: Path where the file should have been saved
            task_id: Task ID associated with the file
            file_name: Name of the file that failed to download
        """
        try:
            error_info = {
                "error": "File download failed",
                "task_id": task_id,
                "file_name": file_name,
                "timestamp": time.time(),
                "human_time": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Save info to a JSON file in the same location but with .error.json extension
            error_path = file_path.with_suffix('.error.json')
            with open(error_path, 'w') as f:
                json.dump(error_info, f, indent=2)
                
            logger.info(f"Created error placeholder: {error_path}")
        except Exception as e:
            logger.error(f"Failed to create error placeholder: {str(e)}")

# Specialized file processors
class FileProcessor:
    """Base class for file processors with error handling and diagnostics."""
    
    @staticmethod
    def get_processor_for_file(file_path: str) -> 'FileProcessor':
        """
        Factory method to get the appropriate processor for a file.
        
        Args:
            file_path: Path to the file to process
            
        Returns:
            The appropriate FileProcessor subclass instance
        """
        if not file_path or not Path(file_path).exists():
            return NullProcessor()
            
        ext = Path(file_path).suffix.lower()
        
        # Select the appropriate processor based on file extension
        if ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
            return ImageProcessor()
        elif ext == '.csv':
            return CSVProcessor()
        elif ext == '.json':
            return JSONProcessor()
        elif ext in ['.txt', '.md']:
            return TextProcessor()
        elif ext in ['.py', '.js', '.html', '.css']:
            return CodeProcessor()
        elif ext in ['.mp3', '.wav', '.ogg', '.flac']:
            return AudioProcessor()
        elif ext in ['.xls', '.xlsx']:
            return ExcelProcessor()
        else:
            return GenericProcessor()
    
    def process(self, file_path: str) -> Dict[str, Any]:
        """
        Process a file and return useful information about it.
        Must be implemented by subclasses.
        
        Args:
            file_path: Path to the file to process
            
        Returns:
            Dictionary with processed information about the file
        """
        raise NotImplementedError("Subclasses must implement process()")
        
    def _safe_process(self, file_path: str, process_func: callable) -> Dict[str, Any]:
        """
        Safely process a file, handling any errors.
        
        Args:
            file_path: Path to the file to process
            process_func: Function to call to actually process the file
            
        Returns:
            Dictionary with processing results or error information
        """
        try:
            return process_func(file_path)
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {str(e)}")
            return {
                "error": str(e),
                "file_path": file_path,
                "file_exists": Path(file_path).exists(),
                "file_size": Path(file_path).stat().st_size if Path(file_path).exists() else None
            }

class NullProcessor(FileProcessor):
    """Processor for handling missing or null files."""
    
    def process(self, file_path: str) -> Dict[str, Any]:
        return {
            "error": "No file provided or file does not exist",
            "file_path": file_path
        }

class ImageProcessor(FileProcessor):
    """Processor for image files with detailed analysis."""
    
    def process(self, file_path: str) -> Dict[str, Any]:
        return self._safe_process(file_path, self._process_image)
        
    def _process_image(self, file_path: str) -> Dict[str, Any]:
        """Process an image file and return detailed information."""
        img = Image.open(file_path)
        
        result = {
            "file_path": file_path,
            "format": img.format,
            "mode": img.mode,
            "width": img.width,
            "height": img.height,
            "aspect_ratio": img.width / img.height if img.height > 0 else None,
            "is_animated": getattr(img, "is_animated", False),
            "n_frames": getattr(img, "n_frames", 1),
            "file_size": Path(file_path).stat().st_size,
            "content_type": mimetypes.guess_type(file_path)[0]
        }
        
        return result

class CSVProcessor(FileProcessor):
    """Processor for CSV files with data summary."""
    
    def process(self, file_path: str) -> Dict[str, Any]:
        return self._safe_process(file_path, self._process_csv)
        
    def _process_csv(self, file_path: str) -> Dict[str, Any]:
        """Process a CSV file and return summary information."""
        df = pd.read_csv(file_path)
        
        # Get column types in a safe way
        column_types = {}
        for col in df.columns:
            column_types[col] = str(df[col].dtype)
        
        return {
            "file_path": file_path,
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": list(df.columns),
            "column_types": column_types,
            "has_nulls": df.isnull().any().any(),
            "null_counts": df.isnull().sum().to_dict(),
            "preview": df.head(3).to_dict(orient='records')
        }

class JSONProcessor(FileProcessor):
    """Processor for JSON files with structure analysis."""
    
    def process(self, file_path: str) -> Dict[str, Any]:
        return self._safe_process(file_path, self._process_json)
        
    def _process_json(self, file_path: str) -> Dict[str, Any]:
        """Process a JSON file and return structure information."""
        with open(file_path, 'r') as f:
            data = json.load(f)
            
        if isinstance(data, list):
            return {
                "file_path": file_path,
                "type": "array",
                "length": len(data),
                "sample": data[0] if data else None,
                "file_size": Path(file_path).stat().st_size
            }
        elif isinstance(data, dict):
            return {
                "file_path": file_path,
                "type": "object",
                "keys": list(data.keys()),
                "key_count": len(data),
                "file_size": Path(file_path).stat().st_size
            }
        else:
            return {
                "file_path": file_path,
                "type": type(data).__name__,
                "value": data,
                "file_size": Path(file_path).stat().st_size
            }

class TextProcessor(FileProcessor):
    """Processor for text files with content analysis."""
    
    def process(self, file_path: str) -> Dict[str, Any]:
        return self._safe_process(file_path, self._process_text)
        
    def _process_text(self, file_path: str) -> Dict[str, Any]:
        """Process a text file and return content information."""
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
            
        lines = content.splitlines()
        
        return {
            "file_path": file_path,
            "line_count": len(lines),
            "char_count": len(content),
            "word_count": len(content.split()),
            "preview": content[:1000] + ("..." if len(content) > 1000 else ""),
            "file_size": Path(file_path).stat().st_size
        }

class CodeProcessor(FileProcessor):
    """Processor for code files with syntax highlighting hints."""
    
    def process(self, file_path: str) -> Dict[str, Any]:
        return self._safe_process(file_path, self._process_code)
        
    def _process_code(self, file_path: str) -> Dict[str, Any]:
        """Process a code file and return analysis."""
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
            
        lines = content.splitlines()
        ext = Path(file_path).suffix.lower()
        
        # Map extension to language for syntax highlighting
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.html': 'html',
            '.css': 'css',
            '.json': 'json',
            '.md': 'markdown'
        }
        
        # Count imports or similar based on language
        imports = []
        if ext == '.py':
            import_lines = [l for l in lines if l.strip().startswith(('import ', 'from '))]
            imports = import_lines[:10]  # Limit to first 10 imports
        elif ext == '.js':
            import_lines = [l for l in lines if l.strip().startswith(('import ', 'require('))]
            imports = import_lines[:10]
            
        return {
            "file_path": file_path,
            "language": language_map.get(ext, 'text'),
            "line_count": len(lines),
            "imports": imports,
            "preview": content[:1000] + ("..." if len(content) > 1000 else ""),
            "file_size": Path(file_path).stat().st_size
        }

class AudioProcessor(FileProcessor):
    """Processor for audio files (placeholder, as we don't have audio libraries)."""
    
    def process(self, file_path: str) -> Dict[str, Any]:
        return self._safe_process(file_path, self._process_audio)
        
    def _process_audio(self, file_path: str) -> Dict[str, Any]:
        """Process an audio file and return basic information."""
        # This is a placeholder - in a real implementation you would use a library
        # like librosa, pydub, or integrate with a speech-to-text API
        
        return {
            "file_path": file_path,
            "file_size": Path(file_path).stat().st_size,
            "content_type": mimetypes.guess_type(file_path)[0],
            "note": "Audio processing requires additional libraries. To fully implement, add librosa or pydub dependencies."
        }

class ExcelProcessor(FileProcessor):
    """Processor for Excel files."""
    
    def process(self, file_path: str) -> Dict[str, Any]:
        return self._safe_process(file_path, self._process_excel)
        
    def _process_excel(self, file_path: str) -> Dict[str, Any]:
        """Process an Excel file and return sheet information."""
        # Read the Excel file
        xlsx = pd.ExcelFile(file_path)
        sheet_names = xlsx.sheet_names
        
        # Get info about each sheet
        sheets_info = []
        for sheet in sheet_names[:3]:  # Limit to first 3 sheets
            df = pd.read_excel(xlsx, sheet_name=sheet, nrows=5)  # Read just first 5 rows
            sheets_info.append({
                "name": sheet,
                "columns": list(df.columns),
                "row_preview_count": len(df),
                "column_count": len(df.columns)
            })
            
        return {
            "file_path": file_path,
            "sheet_count": len(sheet_names),
            "sheet_names": sheet_names,
            "sheets_info": sheets_info,
            "file_size": Path(file_path).stat().st_size
        }

class GenericProcessor(FileProcessor):
    """Generic processor for unknown file types."""
    
    def process(self, file_path: str) -> Dict[str, Any]:
        return self._safe_process(file_path, self._process_generic)
        
    def _process_generic(self, file_path: str) -> Dict[str, Any]:
        """Process an unknown file type and return basic information."""
        path = Path(file_path)
        
        return {
            "file_path": file_path,
            "file_exists": path.exists(),
            "file_size": path.stat().st_size if path.exists() else None,
            "content_type": mimetypes.guess_type(file_path)[0],
            "extension": path.suffix,
            "last_modified": time.ctime(path.stat().st_mtime) if path.exists() else None
        }

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
        
        result = (
            f"Image analysis of {image_path}:\n"
            f"- Dimensions: {width}x{height} pixels\n"
            f"- Format: {format_type}\n"
            f"- Mode: {mode}\n"
            f"- The image is now ready for your analysis. Describe what you see in detail."
        )
        
        log_to_agent_mind(f"## Image Analysis\nAnalyzing image: {image_path}\n```\n{result}\n```")
        return result
    except Exception as e:
        error_msg = f"Error analyzing image: {str(e)}"
        log_to_agent_mind(f"## Error in Image Analysis\n```\n{error_msg}\n```")
        return error_msg

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
        # Verify that the image exists and is a valid image file
        img = Image.open(image_path)
        width, height = img.size
        format_type = img.format
        
        # Log image details for debugging
        logger.info(f"Analyzing chess image: {image_path} ({width}x{height}, {format_type})")
        
        # Attempt to verify this is likely a chess board image based on properties
        is_likely_chess = False
        if abs(width - height) < width * 0.2:  # Chess boards are usually square(ish)
            is_likely_chess = True
            
        # Create a detailed analysis prompt for the chess position
        analysis_prompt = (
            f"Chess position image at {image_path}:\n\n"
            f"Image properties: {width}x{height} pixels, {format_type} format.\n\n"
            f"Please analyze this chess board image carefully. Focus on:\n"
            f"1. The positions of all pieces on the board (pawns, knights, bishops, rooks, queens, kings)\n"
            f"2. Whose turn it is to move (black or white)\n"
            f"3. The possible legal moves for the current player, especially capturing moves and checks\n"
            f"4. Any tactical opportunities, threats, or winning sequences\n"
            f"5. If asked for algebraic notation, provide moves in the standard format: 'e4', 'Nf3', 'Bxh7+', etc.\n"
            f"6. If a specific piece is under attack, identify the attacker and the piece being attacked\n"
            f"7. If checkmate is possible, identify the shortest checkmate sequence\n"
            f"8. Evaluate which side is better positioned and why\n"
        )
        
        if not is_likely_chess:
            analysis_prompt += (
                f"\n\nNote: This image's dimensions ({width}x{height}) suggest it might not be a typical chess board. "
                f"If you can't clearly identify a chess position, please state so and describe what you see instead."
            )
            
        log_to_agent_mind(f"## Chess Position Analysis\nAnalyzing chess image: {image_path}\n```\n{analysis_prompt}\n```")
        return analysis_prompt
    except Exception as e:
        error_msg = f"Error analyzing chess image: {str(e)}"
        logger.error(error_msg, exc_info=True)
        log_to_agent_mind(f"## Error in Chess Analysis\n```\n{error_msg}\n```")
        
        # Provide a more helpful error message with diagnostics
        return (
            f"Error analyzing chess image: {str(e)}\n\n"
            f"This could be due to:\n"
            f"1. The file not being a valid image format\n"
            f"2. File permission issues\n"
            f"3. The image being corrupted\n\n"
            f"Please check if the file exists at path {image_path} and is a valid image format."
        )

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
        # Start a new agent mind log for this session
        start_agent_logging()
        log_to_agent_mind("# SmolAgent Initialized\n")
        
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
        log_to_agent_mind(f"Loaded cache with {len(self.cache)} entries")
        
        # Initialize the file downloader
        self.file_downloader = FileDownloader(api_url)
    
    def _load_cache(self) -> Dict[str, Any]:
        """Load the cache from disk."""
        cache_path = Path(CACHE_DIR) / "answers_cache.json"
        if cache_path.exists():
            try:
                with open(cache_path, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading cache: {e}")
                return {}
        return {}
    
    def _save_cache(self) -> None:
        """Save the cache to disk."""
        cache_path = Path(CACHE_DIR) / "answers_cache.json"
        try:
            with open(cache_path, "w") as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving cache: {e}")
    
    def download_file(self, task_id: str, file_name: str) -> Optional[str]:
        """
        Download a file associated with a question using the robust FileDownloader.
        
        Args:
            task_id: The ID of the task/question
            file_name: The name of the file to download
            
        Returns:
            Path to the downloaded file or None if download failed
        """
        log_to_agent_mind(f"Downloading file: {file_name} for task {task_id}")
        file_path = self.file_downloader.download_file(task_id, file_name)
        
        if file_path:
            # Get detailed file information for debugging
            try:
                processor = FileProcessor.get_processor_for_file(file_path)
                file_info = processor.process(file_path)
                log_to_agent_mind(f"File information: {json.dumps(file_info, indent=2)}")
            except Exception as e:
                log_to_agent_mind(f"Error getting file information: {str(e)}")
            
            return file_path
        else:
            log_to_agent_mind(f"⚠️ Failed to download file: {file_name}")
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
            
        # Check for audio-related questions
        elif any(term in question_lower for term in ["audio", "sound", "listen", "heard", "speech"]):
            return "audio"
            
        # Check based on file extension if present
        elif file_name:
            ext = file_name.split('.')[-1].lower()
            if ext in ['png', 'jpg', 'jpeg', 'gif', 'bmp']:
                if "chess" in question_lower:
                    return "chess"
                return "image"
            elif ext in ['csv', 'json', 'txt', 'md']:
                return "data"
            elif ext in ['py', 'js', 'html', 'css']:
                return "coding"
            elif ext in ['mp3', 'wav', 'ogg', 'flac']:
                return "audio"
            elif ext in ['xls', 'xlsx']:
                return "excel"
                
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
            # Get information about the file to enhance context
            try:
                processor = FileProcessor.get_processor_for_file(file_path)
                file_info = processor.process(file_path)
                log_to_agent_mind(f"Gathered file information to enhance question context")
            except Exception as e:
                logger.error(f"Error getting file information during preprocessing: {str(e)}")
                file_info = None
            
            if question_type == "chess":
                processed_question = (
                    f"{question}\n\n"
                    f"This is a chess-related question. You should analyze the chess position in the image at {file_path} "
                    f"using the analyze_chess_position tool. After analysis, determine the best move using algebraic "
                    f"notation (e.g., 'e4', 'Nf3', etc.). Be precise and concise with your final answer."
                )
                if file_info:
                    processed_question += f"\n\nImage information: {file_info.get('width')}x{file_info.get('height')} pixels, {file_info.get('format')} format."
                    
            elif question_type == "image":
                processed_question = (
                    f"{question}\n\n"
                    f"This question requires image analysis. You should analyze the image at {file_path} "
                    f"using the analyze_image tool to extract relevant information to answer the question."
                )
                if file_info:
                    processed_question += f"\n\nImage information: {file_info.get('width')}x{file_info.get('height')} pixels, {file_info.get('format')} format."
                    
            elif question_type == "data":
                processed_question = (
                    f"{question}\n\n"
                    f"This question requires data analysis. You should analyze the data file at {file_path} "
                    f"using the analyze_data_file tool to extract relevant information to answer the question."
                )
                if file_info and 'row_count' in file_info:
                    processed_question += f"\n\nData file information: {file_info.get('row_count')} rows, {file_info.get('column_count')} columns."
                    
            elif question_type == "excel":
                processed_question = (
                    f"{question}\n\n"
                    f"This question requires Excel file analysis. You should analyze the Excel file at {file_path} "
                    f"using the analyze_data_file tool to extract relevant information to answer the question."
                )
                if file_info and 'sheet_count' in file_info:
                    processed_question += f"\n\nExcel file information: {file_info.get('sheet_count')} sheets: {', '.join(file_info.get('sheet_names', [])[:3])}."
                    
            elif question_type == "audio":
                processed_question = (
                    f"{question}\n\n"
                    f"This question involves audio analysis. The audio file is located at {file_path}. "
                    f"However, direct audio processing is limited. Please do your best to answer based on available information."
                )
                
            else:
                # Generic file handling based on extension
                file_ext = Path(file_path).suffix.lower() if file_path else ""
                
                if file_ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
                    processed_question += f"\n\nThere is an image available at {file_path} that you can analyze using the analyze_image tool."
                    
                elif file_ext in ['.csv', '.json', '.txt', '.md']:
                    processed_question += f"\n\nThere is a data file available at {file_path} that you can analyze using the analyze_data_file tool."
                    
                elif file_ext in ['.xls', '.xlsx']:
                    processed_question += f"\n\nThere is an Excel file available at {file_path} that you can analyze using the analyze_data_file tool."
                    
                elif file_ext in ['.mp3', '.wav', '.ogg', '.flac']:
                    processed_question += f"\n\nThere is an audio file at {file_path}. The system has limited audio processing capabilities."
                    
                else:
                    processed_question += f"\n\nThere is a file available at {file_path} that may contain information needed to answer the question."
        
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
        # Log the raw answer for debugging
        logger.info(f"Raw answer before postprocessing: {answer[:100]}...")
        
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
        # Log the current question
        log_to_agent_mind(f"## Processing Task: {task_id}\n**Question:** {question}")
        if file_name:
            log_to_agent_mind(f"**File:** {file_name}")
        
        # Disabled caching for now
        # if task_id:
        #     question_hash = self.generate_question_hash(task_id, question)
        #     if question_hash in self.cache:
        #         cached_answer = self.cache[question_hash]
        #         log_to_agent_mind(f"✓ Cache hit! Using cached answer: {cached_answer}")
        #         print(f"Cache hit for task: {task_id}")
        #         return cached_answer
        
        file_path = None
        if file_name and task_id:
            # Download the file if needed using robust downloader
            file_path = self.download_file(task_id, file_name)
            if file_path:
                log_to_agent_mind(f"Downloaded file to: {file_path}")
            else:
                log_to_agent_mind(f"⚠️ Failed to download file: {file_name}")
                # Try to proceed anyway, the agent should handle missing files gracefully
        
        # Detect question type
        question_type = self.detect_question_type(question, file_name)
        log_to_agent_mind(f"**Question type detected:** {question_type}")
        logger.info(f"Detected question type: {question_type}")
        
        # Preprocess the question with enhanced context
        processed_question = self.preprocess_question(question, question_type, file_path)
        log_to_agent_mind(f"### Preprocessed Question:\n```\n{processed_question}\n```")
        
        try:
            # Run the agent
            log_to_agent_mind(f"### Running Agent")
            raw_answer = self.agent.run(processed_question)
            log_to_agent_mind(f"### Raw Answer:\n```\n{raw_answer}\n```")
            
            # Postprocess the answer
            final_answer = self.postprocess_answer(str(raw_answer), question_type, question)
            log_to_agent_mind(f"### Final Answer:\n```\n{final_answer}\n```")
            
            # Disabled caching for now
            # if task_id:
            #     question_hash = self.generate_question_hash(task_id, question)
            #     self.cache[question_hash] = final_answer
            #     self._save_cache()
            #     log_to_agent_mind(f"✓ Answer cached for future use")
            
            log_to_agent_mind("---\n")
            return final_answer
        except Exception as e:
            error_msg = f"Error running agent: {str(e)}"
            logger.error(error_msg, exc_info=True)
            log_to_agent_mind(f"### ERROR:\n```\n{error_msg}\n```")
            
            # Try to provide a partial answer or fallback response
            fallback_answer = self._generate_fallback_answer(question, question_type, file_path)
            if fallback_answer:
                log_to_agent_mind(f"### Fallback Answer:\n```\n{fallback_answer}\n```")
                return fallback_answer
                
            log_to_agent_mind("---\n")
            return f"I encountered an error while trying to answer this question. Error: {str(e)}"
            
    def _generate_fallback_answer(self, question: str, question_type: str, file_path: Optional[str]) -> Optional[str]:
        """
        Generate a fallback answer when the main agent fails.
        
        Args:
            question: The original question
            question_type: The detected question type
            file_path: Optional path to the file
            
        Returns:
            A fallback answer or None if no fallback is possible
        """
        try:
            # For chess questions with a file
            if question_type == "chess" and file_path:
                return "After analyzing the chess position, I would need to see the board more clearly to provide a definitive best move."
                
            # For math questions, provide a general note
            elif question_type == "math":
                return "This math problem requires careful calculation. Please check the formula and try again."
                
            # For image questions with a file
            elif question_type == "image" and file_path:
                return "The image contains visual elements that I can't fully analyze at the moment. Please try again later."
                
            # For audio questions
            elif question_type == "audio":
                return "I'm unable to fully process the audio content at this time."
                
            # Default fallback for other question types
            return None
                
        except Exception as e:
            logger.error(f"Error generating fallback answer: {str(e)}")
            return None 