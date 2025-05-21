#!/usr/bin/env python3
"""
Enhanced Debugging Interface for Answer Processing

This module provides visualization and tracing capabilities for the answer processing pipeline,
making it easier to diagnose and fix issues with over-filtering of responses.
"""

import os
import re
import json
import logging
import difflib
import datetime
import html
from typing import Dict, Any, List, Optional, Tuple, Union

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('logs', 'debugging_ui.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('debugging_ui')

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

class AnswerProcessingDebugger:
    """
    A debugger that visualizes and traces the answer processing pipeline,
    helping to identify where over-filtering occurs.
    """
    
    def __init__(self):
        """Initialize the debugger with default settings."""
        self.processing_steps = []
        self.enabled = True  # Can be toggled in config
        self.session_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_question = ""
        self.original_answer = ""
        
    def start_debug_session(self, question: str, original_answer: str, question_id: Optional[str] = None):
        """
        Start a new debugging session for a question-answer pair.
        
        Args:
            question: The original question
            original_answer: The original answer before processing
            question_id: Optional identifier for the question
        """
        self.processing_steps = []
        self.current_question = question
        self.original_answer = original_answer
        self.session_id = question_id or datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Record the initial state
        self.record_step(
            "Original Input", 
            original_answer, 
            original_answer,
            metadata={
                "question": question,
                "timestamp": datetime.datetime.now().isoformat()
            }
        )
        
        logger.info(f"Started debug session {self.session_id} for question: {question[:50]}...")
    
    def record_step(self, stage_name: str, input_text: str, output_text: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Record a processing step for later visualization.
        
        Args:
            stage_name: Name of the processing stage
            input_text: Input text to this stage
            output_text: Output text from this stage
            metadata: Additional information about this stage
        """
        if not self.enabled:
            return
        
        self.processing_steps.append({
            'stage': stage_name,
            'input': input_text,
            'output': output_text,
            'metadata': metadata or {},
            'timestamp': datetime.datetime.now().isoformat()
        })
        
        # Log changes
        if input_text != output_text:
            logger.info(f"Step '{stage_name}': Text changed from '{input_text[:30]}...' to '{output_text[:30]}...'")
            
            # If text became much shorter, that's potentially over-filtering
            if len(output_text) < len(input_text) * 0.5:
                logger.warning(f"Potential over-filtering in '{stage_name}': Text reduced by {len(input_text) - len(output_text)} characters")
    
    def generate_html_visualization(self) -> str:
        """
        Generate an HTML visualization of the processing steps.
        
        Returns:
            HTML string showing the processing pipeline
        """
        if not self.processing_steps:
            return "<p>No processing steps recorded.</p>"
        
        html_output = ["<!DOCTYPE html>"]
        html_output.append("<html><head>")
        html_output.append("<title>Answer Processing Debug</title>")
        html_output.append("<style>")
        html_output.append("""
            body { font-family: Arial, sans-serif; margin: 20px; }
            .debug-panel { border: 1px solid #ddd; border-radius: 5px; padding: 10px; margin-bottom: 20px; }
            .step { border: 1px solid #eee; margin: 10px 0; padding: 10px; border-radius: 5px; }
            .step h3 { margin-top: 0; color: #333; }
            .diff { font-family: monospace; white-space: pre-wrap; margin: 10px 0; }
            .added { background-color: #e6ffed; color: #22863a; }
            .removed { background-color: #ffebe9; color: #cb2431; }
            .metadata { background-color: #f6f8fa; padding: 10px; border-radius: 3px; margin-top: 10px; }
            .warning { color: #b33c00; }
            .collapse-btn { cursor: pointer; background: #f5f5f5; border: none; padding: 5px 10px; }
            .content { display: block; overflow: hidden; }
            .hidden { display: none; }
            .summary { font-weight: bold; }
        """)
        html_output.append("</style>")
        html_output.append("</head><body>")
        
        # Question and session info
        html_output.append("<div class='debug-panel'>")
        html_output.append(f"<h2>Debug Session: {self.session_id}</h2>")
        html_output.append(f"<div class='summary'><strong>Question:</strong> {html.escape(self.current_question)}</div>")
        html_output.append("</div>")
        
        # Overall summary
        original_length = len(self.original_answer)
        final_step = self.processing_steps[-1] if self.processing_steps else None
        final_length = len(final_step['output']) if final_step else 0
        
        html_output.append("<div class='debug-panel'>")
        html_output.append("<h3>Processing Summary</h3>")
        html_output.append(f"<p>Original answer length: <strong>{original_length}</strong> characters</p>")
        html_output.append(f"<p>Final answer length: <strong>{final_length}</strong> characters</p>")
        
        # Warning if significant reduction
        if final_length < original_length * 0.5:
            html_output.append(f"<p class='warning'><strong>Warning:</strong> Significant content reduction detected! {original_length - final_length} characters removed ({(1 - final_length / original_length) * 100:.1f}%)</p>")
        
        html_output.append("</div>")
        
        # Processing steps
        html_output.append("<div class='debug-panel'>")
        html_output.append("<h3>Processing Steps</h3>")
        
        for i, step in enumerate(self.processing_steps):
            html_output.append(f"<div class='step' id='step-{i}'>")
            html_output.append(f"<h3>{i+1}. {html.escape(step['stage'])}</h3>")
            
            # Add collapsible sections for each diff
            html_output.append(f"<button onclick=\"toggleContent('diff-{i}')\" class='collapse-btn'>Show/Hide Changes</button>")
            html_output.append(f"<div id='diff-{i}' class='content'>")
            
            # Generate the diff visualization
            diff_html = self._generate_diff_html(step['input'], step['output'])
            html_output.append(f"<div class='diff'>{diff_html}</div>")
            
            html_output.append("</div>") # End diff content
            
            # Metadata section
            if step['metadata']:
                html_output.append(f"<button onclick=\"toggleContent('meta-{i}')\" class='collapse-btn'>Show/Hide Metadata</button>")
                html_output.append(f"<div id='meta-{i}' class='content hidden'>")
                html_output.append("<div class='metadata'>")
                
                for key, value in step['metadata'].items():
                    # Format metadata based on type
                    if isinstance(value, dict):
                        html_output.append(f"<p><strong>{html.escape(key)}:</strong></p>")
                        html_output.append("<ul>")
                        for k, v in value.items():
                            html_output.append(f"<li><strong>{html.escape(k)}:</strong> {html.escape(str(v))}</li>")
                        html_output.append("</ul>")
                    else:
                        html_output.append(f"<p><strong>{html.escape(key)}:</strong> {html.escape(str(value))}</p>")
                
                html_output.append("</div>") # End metadata content
                html_output.append("</div>") # End metadata
            
            html_output.append("</div>") # End step
        
        html_output.append("</div>") # End steps panel
        
        # Add JavaScript for interactivity
        html_output.append("""
        <script>
        function toggleContent(id) {
            var content = document.getElementById(id);
            if (content.classList.contains('hidden')) {
                content.classList.remove('hidden');
            } else {
                content.classList.add('hidden');
            }
        }
        </script>
        """)
        
        html_output.append("</body></html>")
        
        return "\n".join(html_output)
    
    def _generate_diff_html(self, before: str, after: str) -> str:
        """
        Generate HTML showing the differences between before and after text.
        
        Args:
            before: Text before processing
            after: Text after processing
            
        Returns:
            HTML string showing the changes
        """
        if before == after:
            return f"<p><em>No changes made</em></p><pre>{html.escape(before)}</pre>"
        
        # Use difflib to show differences
        d = difflib.Differ()
        diff = list(d.compare(before.splitlines(), after.splitlines()))
        
        diff_html = []
        for line in diff:
            if line.startswith('+ '):
                diff_html.append(f"<span class='added'>{html.escape(line)}</span>")
            elif line.startswith('- '):
                diff_html.append(f"<span class='removed'>{html.escape(line)}</span>")
            elif line.startswith('? '):
                # Highlight intraline changes - skip these lines as they're just markers
                continue
            else:
                diff_html.append(html.escape(line))
        
        return "<br>".join(diff_html)
    
    def save_debug_session(self, directory: str = "debug_sessions"):
        """
        Save the current debug session to disk for later analysis.
        
        Args:
            directory: Directory to save the session data
        """
        if not self.processing_steps:
            logger.warning("No processing steps to save")
            return
        
        # Create directory if it doesn't exist
        os.makedirs(directory, exist_ok=True)
        
        # Create session file
        filename = f"{directory}/{self.session_id}.json"
        with open(filename, 'w') as f:
            json.dump({
                "session_id": self.session_id,
                "question": self.current_question,
                "original_answer": self.original_answer,
                "steps": self.processing_steps,
                "timestamp": datetime.datetime.now().isoformat()
            }, f, indent=2)
        
        # Create HTML visualization
        html_filename = f"{directory}/{self.session_id}.html"
        with open(html_filename, 'w') as f:
            f.write(self.generate_html_visualization())
        
        logger.info(f"Debug session saved to {filename} and {html_filename}")
    
    def analyze_filtering(self) -> Dict[str, Any]:
        """
        Analyze the processing steps to identify potential over-filtering issues.
        
        Returns:
            Dictionary containing analysis results
        """
        if not self.processing_steps:
            return {"status": "No processing steps to analyze"}
        
        # Track size changes through the pipeline
        step_sizes = [(step['stage'], len(step['input']), len(step['output'])) 
                     for step in self.processing_steps]
        
        # Identify steps with significant reduction
        significant_reductions = []
        for i, (stage, input_size, output_size) in enumerate(step_sizes):
            if i > 0:  # Skip first step which is just the original
                reduction = input_size - output_size
                reduction_percent = (reduction / input_size) * 100 if input_size > 0 else 0
                
                if reduction_percent > 30:  # Consider 30% reduction significant
                    significant_reductions.append({
                        "stage": stage,
                        "input_size": input_size,
                        "output_size": output_size,
                        "reduction": reduction,
                        "reduction_percent": reduction_percent,
                        "step_index": i
                    })
        
        # Check for lost key information
        lost_info = []
        
        # Look for common patterns of important information
        original = self.processing_steps[0]['output']
        final = self.processing_steps[-1]['output'] if self.processing_steps else ""
        
        # Check for lost numbers
        original_numbers = set(re.findall(r'\b\d+(?:\.\d+)?\b', original))
        final_numbers = set(re.findall(r'\b\d+(?:\.\d+)?\b', final))
        lost_numbers = original_numbers - final_numbers
        
        # Check for lost entities (proper nouns)
        original_entities = set(re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', original))
        final_entities = set(re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', final))
        lost_entities = original_entities - final_entities
        
        if lost_numbers:
            lost_info.append({
                "type": "numbers",
                "lost_items": list(lost_numbers)
            })
        
        if lost_entities:
            lost_info.append({
                "type": "entities",
                "lost_items": list(lost_entities)
            })
        
        return {
            "original_size": len(original),
            "final_size": len(final),
            "total_reduction": len(original) - len(final),
            "total_reduction_percent": ((len(original) - len(final)) / len(original)) * 100 if len(original) > 0 else 0,
            "significant_reductions": significant_reductions,
            "lost_information": lost_info,
            "recommendation": self._generate_filtering_recommendation(significant_reductions, lost_info)
        }
    
    def _generate_filtering_recommendation(self, reductions, lost_info) -> str:
        """
        Generate a recommendation for fixing filtering issues.
        
        Args:
            reductions: List of significant reductions
            lost_info: List of lost information
            
        Returns:
            Recommendation string
        """
        if not reductions and not lost_info:
            return "No significant filtering issues detected."
        
        recommendation = []
        
        if reductions:
            problematic_stages = [r["stage"] for r in reductions]
            recommendation.append(f"Review these processing stages which may be over-filtering: {', '.join(problematic_stages)}.")
        
        if lost_info:
            for info in lost_info:
                if info["type"] == "numbers" and info["lost_items"]:
                    recommendation.append(f"Important numeric values were lost: {', '.join(info['lost_items'][:5])}.")
                elif info["type"] == "entities" and info["lost_items"]:
                    recommendation.append(f"Important named entities were lost: {', '.join(info['lost_items'][:5])}.")
        
        recommendation.append("Consider implementing more conservative filters or context-aware processing for this question type.")
        
        return " ".join(recommendation)
        
# Helper function to get a singleton instance
_debugger_instance = None

def get_debugger() -> AnswerProcessingDebugger:
    """Get the singleton debugger instance."""
    global _debugger_instance
    if _debugger_instance is None:
        _debugger_instance = AnswerProcessingDebugger()
    return _debugger_instance 