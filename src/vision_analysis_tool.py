#!/usr/bin/env python3
"""
Vision Analysis Tool for SmolAgent using OpenAI's Vision API.

This tool provides advanced image analysis capabilities including:
- Chess board position analysis from images
- Chart and graph data extraction  
- General image content description
- OCR for text in images
"""

import os
import logging
import base64
import json
from typing import Dict, List, Optional, Any
from PIL import Image
import requests

from smolagents import Tool

# Configure logging
logger = logging.getLogger("VisionAnalysisTool")

class VisionAnalysisTool(Tool):
    """Vision analysis tool using OpenAI's Vision API."""
    
    name = "vision_analyzer"
    description = """
    Analyzes images using OpenAI's Vision API. Specialized capabilities:
    
    - Chess board analysis: Extract FEN notation from chess board images
    - Chart reading: Extract data from graphs, charts, and tables in images
    - General analysis: Describe image content, identify objects, read text
    - OCR: Extract text from images with high accuracy
    - Technical diagrams: Analyze scientific/technical images
    
    Supports common image formats: PNG, JPG, JPEG, GIF, WebP
    Best for: Chess positions, data visualization, document analysis, content verification
    """
    
    inputs = {
        "image_path": {
            "type": "string", 
            "description": "Path to the image file to analyze"
        },
        "analysis_type": {
            "type": "string",
            "description": "Type of analysis: 'chess', 'chart', 'ocr', 'general', 'detailed'",
            "nullable": True
        },
        "specific_question": {
            "type": "string",
            "description": "Optional: Specific question about the image content",
            "nullable": True
        }
    }
    
    output_type = "string"
    
    def __init__(self, **kwargs):
        """Initialize the Vision Analysis Tool."""
        super().__init__(**kwargs)
        
        # Get API key
        self.api_key = os.getenv("VISION_API_KEY") or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.warning("No OpenAI API key found. Vision analysis will not work.")
        
        self.api_url = "https://api.openai.com/v1/chat/completions"
        
        # Headers for API requests
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # Analysis templates
        self.analysis_prompts = {
            "chess": """
            Analyze this chess board image and provide:
            1. The FEN notation of the current position
            2. Whose turn it is to move (White or Black)
            3. Any notable tactical features or patterns
            4. The material balance
            Be precise with piece positions and notation.
            """,
            
            "chart": """
            Analyze this chart/graph image and extract:
            1. Chart type (bar, line, pie, scatter, etc.)
            2. Title and axis labels
            3. Key data points and values
            4. Trends or patterns observed
            5. Any numerical data you can read accurately
            """,
            
            "ocr": """
            Extract all text visible in this image. Maintain formatting where possible.
            Focus on accuracy and completeness. If there are multiple text sections,
            organize them logically.
            """,
            
            "detailed": """
            Provide a comprehensive analysis of this image including:
            1. Overall description of what's shown
            2. Key objects, people, or elements
            3. Text content (if any)
            4. Colors, composition, and visual style
            5. Any notable details or specific information
            """,
            
            "general": """
            Describe what you see in this image clearly and accurately.
            Focus on the main content and any important details.
            """
        }
    
    def forward(self, image_path: str, analysis_type: str = "general", 
                specific_question: str = None) -> str:
        """
        Analyze an image using OpenAI's Vision API.
        
        Args:
            image_path: Path to the image file
            analysis_type: Type of analysis to perform
            specific_question: Optional specific question about the image
            
        Returns:
            Analysis results as formatted string
        """
        if not self.api_key:
            return "❌ Error: No OpenAI API key configured. Please set VISION_API_KEY or OPENAI_API_KEY."
        
        if not image_path:
            return "❌ Error: No image path provided"
        
        logger.info(f"🔍 Analyzing image: {image_path} | Type: {analysis_type}")
        
        try:
            # Validate and process image
            image_data = self._prepare_image(image_path)
            if not image_data:
                return f"❌ Error: Could not load or process image: {image_path}"
            
            # Create prompt based on analysis type
            prompt = self._create_analysis_prompt(analysis_type, specific_question)
            
            # Make API request
            response = self._call_vision_api(image_data, prompt)
            
            if response:
                return self._format_response(response, analysis_type, image_path)
            else:
                return "❌ Error: Failed to get response from Vision API"
                
        except Exception as e:
            logger.error(f"❌ Error analyzing image {image_path}: {str(e)}")
            return f"❌ Error analyzing image: {str(e)}"
    
    def _prepare_image(self, image_path: str) -> Optional[str]:
        """Prepare image for API request by encoding to base64."""
        try:
            # Check if file exists
            if not os.path.exists(image_path):
                logger.error(f"Image file not found: {image_path}")
                return None
            
            # Open and validate image
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Resize if too large (API limits)
                max_size = (2048, 2048)
                if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)
                    logger.info(f"Resized image to {img.size}")
                
                # Save to temporary file if resized, otherwise use original
                if img.size != Image.open(image_path).size:
                    import tempfile
                    temp_path = tempfile.mktemp(suffix='.jpg')
                    img.save(temp_path, 'JPEG', quality=95)
                    image_path = temp_path
            
            # Encode to base64
            with open(image_path, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')
            
            return image_data
            
        except Exception as e:
            logger.error(f"Error preparing image {image_path}: {str(e)}")
            return None
    
    def _create_analysis_prompt(self, analysis_type: str, specific_question: str = None) -> str:
        """Create analysis prompt based on type and specific question."""
        
        # Use specific question if provided
        if specific_question:
            base_prompt = f"Please answer this specific question about the image: {specific_question}\n\n"
            if analysis_type in self.analysis_prompts:
                base_prompt += f"Additional context: {self.analysis_prompts[analysis_type]}"
            return base_prompt
        
        # Use template for analysis type
        if analysis_type in self.analysis_prompts:
            return self.analysis_prompts[analysis_type]
        else:
            return self.analysis_prompts["general"]
    
    def _call_vision_api(self, image_data: str, prompt: str) -> Optional[str]:
        """Make API call to OpenAI Vision."""
        try:
            payload = {
                "model": "gpt-4o",  # Use the latest vision model
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_data}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 1000,
                "temperature": 0.1  # Low temperature for more consistent results
            }
            
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            
            result = response.json()
            
            if 'choices' in result and len(result['choices']) > 0:
                return result['choices'][0]['message']['content']
            else:
                logger.error("No choices in API response")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error calling Vision API: {str(e)}")
            return None
    
    def _format_response(self, response: str, analysis_type: str, image_path: str) -> str:
        """Format the API response for output."""
        
        output_parts = [
            f"🖼️ Image Analysis: {os.path.basename(image_path)}",
            f"📊 Analysis Type: {analysis_type.title()}",
            "=" * 50
        ]
        
        # Add type-specific formatting
        if analysis_type == "chess":
            output_parts.append("♟️ CHESS POSITION ANALYSIS:")
            # Try to extract FEN if present
            if "FEN:" in response or "fen:" in response.lower():
                lines = response.split('\n')
                for line in lines:
                    if 'fen' in line.lower() and '/' in line:
                        output_parts.append(f"🎯 FEN: {line.split(':', 1)[1].strip()}")
                        break
        
        elif analysis_type == "chart":
            output_parts.append("📈 CHART DATA ANALYSIS:")
            
        elif analysis_type == "ocr":
            output_parts.append("📄 EXTRACTED TEXT:")
            
        else:
            output_parts.append("🔍 ANALYSIS RESULTS:")
        
        # Add the main response
        output_parts.append(response)
        
        # Add metadata
        output_parts.append(f"\n📍 Source: {image_path}")
        
        return "\n".join(output_parts)

def get_vision_analysis_tool():
    """Create and return a vision analysis tool instance."""
    return VisionAnalysisTool() 