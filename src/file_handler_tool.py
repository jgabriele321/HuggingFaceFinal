#!/usr/bin/env python3
"""
Enhanced File Handler Tool for the SmolAgent

This module provides a tool for handling different types of files including:
- Images (.png, .jpg, .jpeg)
- Audio (.mp3, .wav)
- Code (.py)
- Data (.json, .xlsx, .csv)
"""

import os
import json
import logging
import ast
from pathlib import Path
from typing import Optional, Dict, Any, Union, List
import requests
from PIL import Image
import pandas as pd
import mutagen  # For audio file metadata
from mutagen.mp3 import MP3
from mutagen.wave import WAVE

logger = logging.getLogger(__name__)

class FileHandlerTool:
    """Tool for handling different types of files."""
    
    def __init__(self, files_dir: str = "files"):
        """Initialize the file handler tool."""
        self.files_dir = files_dir
        self.supported_extensions = {
            'image': ['.png', '.jpg', '.jpeg'],
            'audio': ['.mp3', '.wav'],
            'code': ['.py'],
            'data': ['.json', '.xlsx', '.csv']
        }
        
    def get_file_type(self, filename: str) -> Optional[str]:
        """Determine the type of file based on extension."""
        ext = Path(filename).suffix.lower()
        for file_type, extensions in self.supported_extensions.items():
            if ext in extensions:
                return file_type
        return None
        
    def get_file_path(self, task_id: str, filename: str) -> str:
        """Get the full path to a file."""
        return os.path.join(self.files_dir, filename)
        
    def read_file(self, task_id: str, filename: str) -> Dict[str, Any]:
        """Read a file and return its contents based on type."""
        try:
            file_path = self.get_file_path(task_id, filename)
            if not os.path.exists(file_path):
                # Try to download from API if file doesn't exist
                self.download_file(task_id, filename)
            
            file_type = self.get_file_type(filename)
            if not file_type:
                raise ValueError(f"Unsupported file type: {filename}")
                
            handlers = {
                'image': self._handle_image,
                'audio': self._handle_audio,
                'code': self._handle_code,
                'data': self._handle_data
            }
            
            handler = handlers.get(file_type)
            if handler:
                return handler(file_path)
            else:
                raise ValueError(f"No handler for file type: {file_type}")
            
        except Exception as e:
            logger.error(f"Error reading file {filename}: {str(e)}")
            return {"error": str(e)}
            
    def download_file(self, task_id: str, filename: str) -> bool:
        """Download a file from the API endpoint."""
        try:
            api_url = f"/files/{task_id}"  # Update with actual API endpoint
            response = requests.get(api_url)
            if response.status_code == 200:
                file_path = self.get_file_path(task_id, filename)
                with open(file_path, 'wb') as f:
                    f.write(response.content)
                return True
            return False
        except Exception as e:
            logger.error(f"Error downloading file {filename}: {str(e)}")
            return False
            
    def _handle_image(self, file_path: str) -> Dict[str, Any]:
        """Handle image files."""
        try:
            img = Image.open(file_path)
            return {
                "type": "image",
                "size": img.size,
                "mode": img.mode,
                "format": img.format,
                "path": file_path
            }
        except Exception as e:
            return {"error": f"Error processing image: {str(e)}"}
            
    def _handle_audio(self, file_path: str) -> Dict[str, Any]:
        """Handle audio files with metadata."""
        try:
            # Get audio metadata based on file type
            if file_path.lower().endswith('.mp3'):
                audio = MP3(file_path)
                info = {
                    "type": "audio",
                    "format": "mp3",
                    "duration": audio.info.length,  # Duration in seconds
                    "bitrate": audio.info.bitrate,
                    "sample_rate": audio.info.sample_rate,
                    "channels": audio.info.channels,
                    "path": file_path
                }
            elif file_path.lower().endswith('.wav'):
                audio = WAVE(file_path)
                info = {
                    "type": "audio",
                    "format": "wav",
                    "duration": audio.info.length,
                    "sample_rate": audio.info.sample_rate,
                    "channels": audio.info.channels,
                    "path": file_path
                }
            
            # Add any available tags/metadata
            if hasattr(audio, 'tags') and audio.tags:
                info["metadata"] = dict(audio.tags)
            
            return info
            
        except Exception as e:
            return {"error": f"Error processing audio: {str(e)}"}
            
    def _handle_code(self, file_path: str) -> Dict[str, Any]:
        """Handle Python code files with analysis."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Parse the AST to analyze the code
            tree = ast.parse(content)
            
            # Analyze code structure
            functions = []
            classes = []
            imports = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions.append({
                        "name": node.name,
                        "args": [arg.arg for arg in node.args.args],
                        "line": node.lineno
                    })
                elif isinstance(node, ast.ClassDef):
                    classes.append({
                        "name": node.name,
                        "bases": [base.id for base in node.bases if isinstance(base, ast.Name)],
                        "line": node.lineno
                    })
                elif isinstance(node, ast.Import):
                    imports.extend(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom):
                    imports.extend(f"{node.module}.{alias.name}" for alias in node.names)
            
            return {
                "type": "code",
                "language": "python",
                "content": content,
                "size": len(content),
                "analysis": {
                    "functions": functions,
                    "classes": classes,
                    "imports": imports,
                    "total_lines": len(content.splitlines())
                },
                "path": file_path
            }
        except Exception as e:
            return {"error": f"Error processing Python code: {str(e)}"}
            
    def _handle_data(self, file_path: str) -> Dict[str, Any]:
        """Handle data files (JSON, Excel, CSV)."""
        try:
            ext = Path(file_path).suffix.lower()
            
            if ext == '.json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {
                    "type": "data",
                    "format": "json",
                    "data": data,
                    "path": file_path
                }
            elif ext in ['.xlsx', '.csv']:
                df = pd.read_excel(file_path) if ext == '.xlsx' else pd.read_csv(file_path)
                return {
                    "type": "data",
                    "format": ext[1:],
                    "rows": len(df),
                    "columns": list(df.columns),
                    "data": df.to_dict(orient='records'),
                    "path": file_path
                }
            else:
                raise ValueError(f"Unsupported data file type: {ext}")
                
        except Exception as e:
            return {"error": f"Error processing data file: {str(e)}"}

def get_file_handler_tool() -> Dict[str, Any]:
    """Create and return the file handler tool configuration."""
    handler = FileHandlerTool()
    
    return {
        "name": "file_handler",
        "description": "Handle different types of files including images, audio files, Python code, and data files",
        "parameters": {
            "task_id": {
                "type": "string",
                "description": "The task ID associated with the file"
            },
            "filename": {
                "type": "string",
                "description": "The name of the file to process"
            }
        },
        "function": handler.read_file
    } 