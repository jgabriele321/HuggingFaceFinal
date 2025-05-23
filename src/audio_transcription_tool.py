#!/usr/bin/env python3
"""
Audio Transcription Tool for SmolAgent using OpenAI's Whisper API.

This tool provides audio transcription capabilities for various audio formats
and supports multiple languages with high accuracy.
"""

import os
import logging
import json
from typing import Dict, List, Optional, Any
import requests
from pathlib import Path

from smolagents import Tool

# Configure logging
logger = logging.getLogger("AudioTranscriptionTool")

class AudioTranscriptionTool(Tool):
    """Audio transcription tool using OpenAI's Whisper API."""
    
    name = "audio_transcriber"
    description = """
    Transcribes audio files using OpenAI's Whisper API with high accuracy.
    
    Capabilities:
    - Speech-to-text conversion for multiple languages
    - Automatic language detection
    - Support for various audio formats (MP3, WAV, M4A, FLAC, etc.)
    - Timestamped transcriptions
    - Speaker identification hints
    - Content summarization options
    
    Best for: Interview transcripts, meeting notes, lecture content, 
    podcast analysis, multilingual audio content.
    
    Supported formats: MP3, MP4, MPEG, MPGA, M4A, WAV, WEBM, FLAC
    Max file size: 25MB
    """
    
    inputs = {
        "audio_path": {
            "type": "string", 
            "description": "Path to the audio file to transcribe"
        },
        "language": {
            "type": "string",
            "description": "Optional: Language code (e.g., 'en', 'es', 'fr') or 'auto' for detection",
            "nullable": True
        },
        "output_format": {
            "type": "string",
            "description": "Output format: 'text', 'detailed', 'summary'",
            "nullable": True
        },
        "include_timestamps": {
            "type": "boolean",
            "description": "Whether to include timestamps in the output",
            "nullable": True
        }
    }
    
    output_type = "string"
    
    def __init__(self, **kwargs):
        """Initialize the Audio Transcription Tool."""
        super().__init__(**kwargs)
        
        # Get API key
        self.api_key = os.getenv("WHISPER_API_KEY") or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.warning("No OpenAI API key found. Audio transcription will not work.")
        
        self.api_url = "https://api.openai.com/v1/audio/transcriptions"
        
        # Headers for API requests
        self.headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # Supported audio formats
        self.supported_formats = {
            '.mp3', '.mp4', '.mpeg', '.mpga', '.m4a', 
            '.wav', '.webm', '.flac', '.ogg'
        }
        
        # Language codes mapping
        self.language_codes = {
            'english': 'en', 'spanish': 'es', 'french': 'fr', 
            'german': 'de', 'italian': 'it', 'portuguese': 'pt',
            'russian': 'ru', 'japanese': 'ja', 'chinese': 'zh',
            'korean': 'ko', 'arabic': 'ar', 'hindi': 'hi'
        }
    
    def forward(self, audio_path: str, language: str = "auto", 
                output_format: str = "detailed", include_timestamps: bool = True) -> str:
        """
        Transcribe an audio file using OpenAI's Whisper API.
        
        Args:
            audio_path: Path to the audio file
            language: Language code or 'auto' for detection
            output_format: Format of output ('text', 'detailed', 'summary')
            include_timestamps: Whether to include timestamps
            
        Returns:
            Transcription results as formatted string
        """
        if not self.api_key:
            return "❌ Error: No OpenAI API key configured. Please set WHISPER_API_KEY or OPENAI_API_KEY."
        
        if not audio_path:
            return "❌ Error: No audio path provided"
        
        logger.info(f"🎵 Transcribing audio: {audio_path} | Language: {language} | Format: {output_format}")
        
        try:
            # Validate audio file
            if not self._validate_audio_file(audio_path):
                return f"❌ Error: Invalid or unsupported audio file: {audio_path}"
            
            # Process language parameter
            processed_language = self._process_language(language)
            
            # Transcribe audio
            transcription_result = self._transcribe_audio(audio_path, processed_language, include_timestamps)
            
            if transcription_result:
                return self._format_output(transcription_result, output_format, audio_path, language)
            else:
                return "❌ Error: Failed to transcribe audio"
                
        except Exception as e:
            logger.error(f"❌ Error transcribing audio {audio_path}: {str(e)}")
            return f"❌ Error transcribing audio: {str(e)}"
    
    def _validate_audio_file(self, audio_path: str) -> bool:
        """Validate that the audio file exists and is supported."""
        try:
            path = Path(audio_path)
            
            # Check if file exists
            if not path.exists():
                logger.error(f"Audio file not found: {audio_path}")
                return False
            
            # Check file extension
            if path.suffix.lower() not in self.supported_formats:
                logger.error(f"Unsupported audio format: {path.suffix}")
                return False
            
            # Check file size (OpenAI limit is 25MB)
            file_size = path.stat().st_size
            max_size = 25 * 1024 * 1024  # 25MB in bytes
            
            if file_size > max_size:
                logger.error(f"Audio file too large: {file_size / (1024*1024):.1f}MB (max 25MB)")
                return False
            
            logger.info(f"✅ Audio file validated: {file_size / (1024*1024):.1f}MB, {path.suffix}")
            return True
            
        except Exception as e:
            logger.error(f"Error validating audio file: {str(e)}")
            return False
    
    def _process_language(self, language: str) -> Optional[str]:
        """Process and validate language parameter."""
        if not language or language.lower() == "auto":
            return None  # Let Whisper auto-detect
        
        # Convert full language names to codes
        language_lower = language.lower()
        if language_lower in self.language_codes:
            return self.language_codes[language_lower]
        
        # Return as-is if it looks like a language code
        if len(language) == 2:
            return language.lower()
        
        logger.warning(f"Unknown language: {language}, using auto-detection")
        return None
    
    def _transcribe_audio(self, audio_path: str, language: Optional[str], 
                         include_timestamps: bool) -> Optional[Dict]:
        """Transcribe audio using Whisper API."""
        try:
            # Prepare files for upload
            with open(audio_path, 'rb') as audio_file:
                files = {
                    'file': (os.path.basename(audio_path), audio_file, 'audio/mpeg')
                }
                
                # Prepare data
                data = {
                    'model': 'whisper-1',
                    'response_format': 'verbose_json' if include_timestamps else 'json'
                }
                
                # Add language if specified
                if language:
                    data['language'] = language
                
                # Make API request
                response = requests.post(
                    self.api_url,
                    headers=self.headers,
                    files=files,
                    data=data,
                    timeout=120  # Audio transcription can take a while
                )
                
                response.raise_for_status()
                
                result = response.json()
                logger.info("✅ Audio transcription completed successfully")
                return result
                
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error transcribing audio: {str(e)}")
            return None
    
    def _format_output(self, transcription: Dict, output_format: str, 
                      audio_path: str, language: str) -> str:
        """Format the transcription output."""
        
        output_parts = [
            f"🎵 Audio Transcription: {os.path.basename(audio_path)}",
            f"🌐 Language: {language.title() if language != 'auto' else 'Auto-detected'}",
            f"📝 Format: {output_format.title()}",
            "=" * 60
        ]
        
        # Add detected language if available
        if 'language' in transcription:
            output_parts.append(f"🔍 Detected Language: {transcription['language'].upper()}")
        
        # Add duration if available
        if 'duration' in transcription:
            duration = transcription['duration']
            minutes = int(duration // 60)
            seconds = int(duration % 60)
            output_parts.append(f"⏱️ Duration: {minutes}:{seconds:02d}")
        
        if output_format == "text":
            # Simple text output
            output_parts.append(f"\n📄 TRANSCRIPTION:")
            output_parts.append(transcription.get('text', ''))
            
        elif output_format == "summary":
            # Summary format
            text = transcription.get('text', '')
            output_parts.append(f"\n📄 TRANSCRIPTION:")
            output_parts.append(text)
            
            # Add basic analysis
            if text:
                word_count = len(text.split())
                output_parts.append(f"\n📊 ANALYSIS:")
                output_parts.append(f"• Word count: {word_count}")
                output_parts.append(f"• Character count: {len(text)}")
                
                # Identify potential speakers (simple heuristic)
                if any(indicator in text.lower() for indicator in ['speaker', ':', 'a:', 'b:']):
                    output_parts.append("• Format: Multi-speaker conversation detected")
                else:
                    output_parts.append("• Format: Single speaker or monologue")
            
        else:  # detailed
            # Detailed format with segments if available
            output_parts.append(f"\n📄 FULL TRANSCRIPTION:")
            
            if 'segments' in transcription and transcription['segments']:
                # Timestamped segments
                for i, segment in enumerate(transcription['segments']):
                    start = segment.get('start', 0)
                    end = segment.get('end', 0)
                    text = segment.get('text', '').strip()
                    
                    start_time = f"{int(start//60):02d}:{int(start%60):02d}"
                    end_time = f"{int(end//60):02d}:{int(end%60):02d}"
                    
                    output_parts.append(f"[{start_time}-{end_time}] {text}")
            else:
                # No segments, just text
                output_parts.append(transcription.get('text', ''))
            
            # Add confidence info if available
            if 'confidence' in transcription:
                confidence = transcription['confidence'] * 100
                output_parts.append(f"\n🎯 Confidence: {confidence:.1f}%")
        
        # Add metadata
        output_parts.append(f"\n📍 Source: {audio_path}")
        output_parts.append(f"🔧 Processed with: OpenAI Whisper")
        
        return "\n".join(output_parts)

def get_audio_transcription_tool():
    """Create and return an audio transcription tool instance."""
    return AudioTranscriptionTool() 