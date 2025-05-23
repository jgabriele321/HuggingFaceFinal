#!/usr/bin/env python3
"""
Multi-Agent System for SmolAgent with specialized domain agents.

This implements a simplified multi-agent architecture that works with current smolagents:
- Enhanced single agent with specialized tools
- Smart tool routing and enhanced system prompts
- Planning capabilities with domain expertise
"""

import os
import logging
from typing import List, Dict, Any, Optional
from smolagents import CodeAgent, HfApiModel, LiteLLMModel, DuckDuckGoSearchTool

# Configure logging
logger = logging.getLogger("MultiAgentSystem")

class MultiAgentSystem:
    """Enhanced agent system with specialized tool integration."""
    
    def __init__(self, model_id: str = None, planning_interval: int = 3):
        """
        Initialize the enhanced agent system.
        
        Args:
            model_id: Model to use (defaults to OpenRouter Gemini)
            planning_interval: Steps between planning phases
        """
        self.model_id = model_id or "google/gemini-2.0-flash-exp:free"
        self.planning_interval = planning_interval
        
        # Initialize model
        self.model = self._initialize_model()
        
        # Initialize enhanced agent
        self.manager_agent = None
        self._setup_enhanced_agent()
        
        logger.info("✅ Enhanced agent system initialized successfully")
    
    def _initialize_model(self):
        """Initialize the LLM model for the agent."""
        try:
            # Try LiteLLM for OpenRouter first
            if "google/" in self.model_id and os.getenv("OPENROUTER_API_KEY"):
                return LiteLLMModel(
                    model_id=self.model_id,
                    api_key=os.getenv("OPENROUTER_API_KEY"),
                    api_base="https://openrouter.ai/api/v1"
                )
            else:
                # Fallback to HuggingFace
                from smolagents import InferenceClientModel
                return InferenceClientModel(self.model_id)
                
        except Exception as e:
            logger.warning(f"Failed to initialize primary model, using fallback: {str(e)}")
            try:
                from smolagents import InferenceClientModel
                return InferenceClientModel("meta-llama/Llama-3.3-70B-Instruct")
            except:
                from smolagents import HfApiModel
                return HfApiModel("meta-llama/Llama-3.3-70B-Instruct")
    
    def _setup_enhanced_agent(self):
        """Setup enhanced agent with all specialized tools."""
        
        # Collect all available tools
        tools = self._initialize_all_tools()
        
        # Enhanced system prompt
        system_prompt = self._create_enhanced_system_prompt()
        
        # Create enhanced agent
        self.manager_agent = CodeAgent(
            tools=tools,
            model=self.model,
            planning_interval=self.planning_interval,
            additional_authorized_imports=[
                "chess", "pandas", "numpy", "time", "json", "re", 
                "datetime", "collections", "itertools", "math", "requests"
            ],
            system_prompt=system_prompt,
            max_steps=15,
            verbose=True
        )
        
        logger.info(f"✅ Enhanced agent created with {len(tools)} tools")
    
    def _initialize_all_tools(self) -> List:
        """Initialize all available tools with error handling."""
        tools = []
        tool_status = {}
        
        # 1. Core web search
        try:
            tools.append(DuckDuckGoSearchTool())
            tool_status["web_search"] = "✅ Active"
        except Exception as e:
            logger.error(f"Failed to initialize web search: {str(e)}")
            tool_status["web_search"] = "❌ Failed"
        
        # 2. Enhanced Wikipedia tool
        try:
            from src.enhanced_wikipedia_tool import get_enhanced_wikipedia_tool
            tools.append(get_enhanced_wikipedia_tool())
            tool_status["enhanced_wikipedia"] = "✅ Active"
        except Exception as e:
            logger.error(f"Failed to initialize enhanced Wikipedia: {str(e)}")
            tool_status["enhanced_wikipedia"] = "❌ Failed"
        
        # 3. Webpage tool
        try:
            from src.webpage_tool import get_webpage_tool
            tools.append(get_webpage_tool())
            tool_status["webpage"] = "✅ Active"
        except Exception as e:
            logger.error(f"Failed to initialize webpage tool: {str(e)}")
            tool_status["webpage"] = "❌ Failed"
        
        # 4. Vision analysis tool
        try:
            from src.vision_analysis_tool import get_vision_analysis_tool
            tools.append(get_vision_analysis_tool())
            tool_status["vision_analysis"] = "✅ Active"
        except Exception as e:
            logger.warning(f"Vision analysis not available: {str(e)}")
            tool_status["vision_analysis"] = "⚠️ Limited (OpenAI API needed)"
        
        # 5. Audio transcription tool
        try:
            from src.audio_transcription_tool import get_audio_transcription_tool
            tools.append(get_audio_transcription_tool())
            tool_status["audio_transcription"] = "✅ Active"
        except Exception as e:
            logger.warning(f"Audio transcription not available: {str(e)}")
            tool_status["audio_transcription"] = "⚠️ Limited (OpenAI API needed)"
        
        # 6. Chess analysis tool
        try:
            from src.chess_analysis_tool import get_chess_analysis_tool
            tools.append(get_chess_analysis_tool())
            tool_status["chess_analysis"] = "✅ Active"
        except Exception as e:
            logger.warning(f"Chess analysis not available: {str(e)}")
            tool_status["chess_analysis"] = "⚠️ Limited"
        
        # 7. File handler tool
        try:
            from src.file_handler_tool import get_file_handler_tool
            file_config = get_file_handler_tool()
            
            # Create wrapper for file handler
            from smolagents import Tool
            
            class FileHandlerWrapper(Tool):
                name = "file_handler"
                description = "Handles file processing for various file types (images, audio, text, excel)"
                inputs = {
                    "task_id": {"type": "string", "description": "Task ID"},
                    "filename": {"type": "string", "description": "Filename to process"}
                }
                output_type = "string"
                
                def __init__(self, file_function):
                    super().__init__()
                    self._function = file_function
                    
                def forward(self, task_id: str, filename: str):
                    try:
                        result = self._function(task_id=task_id, filename=filename)
                        return str(result)
                    except Exception as e:
                        return f"Error processing file: {str(e)}"
            
            tools.append(FileHandlerWrapper(file_config["function"]))
            tool_status["file_handler"] = "✅ Active"
        except Exception as e:
            logger.error(f"Failed to initialize file handler: {str(e)}")
            tool_status["file_handler"] = "❌ Failed"
        
        # 8. Python interpreter
        try:
            from src.python_interpreter_tool import PythonInterpreterTool
            tools.append(PythonInterpreterTool())
            tool_status["python_interpreter"] = "✅ Active"
        except Exception as e:
            logger.error(f"Failed to initialize Python interpreter: {str(e)}")
            tool_status["python_interpreter"] = "❌ Failed"
        
        # Log tool status
        logger.info("🔧 Tool Initialization Status:")
        for tool_name, status in tool_status.items():
            logger.info(f"  • {tool_name}: {status}")
        
        self.tool_status = tool_status
        return tools
    
    def _create_enhanced_system_prompt(self) -> str:
        """Create enhanced system prompt with domain expertise."""
        
        # Use a basic system prompt since CODE_SYSTEM_PROMPT may not be available
        base_prompt = """You are an expert assistant who can solve any task using code blobs. You will be given a task to solve as best you can.
To do so, you have been given access to a list of tools: these tools are basically Python functions which you can call with code.
To solve the task, you must plan forward to proceed in a series of steps, in a cycle of 'Thought:', 'Code:', and 'Observation:' sequences.

At each step, in the 'Thought:' sequence, you should first explain your reasoning towards solving the task and the tools that you want to use.
Then in the 'Code:' sequence, you should write the code in simple Python. The code sequence must end with '<end_code>' sequence.
During each intermediate step, you can use 'print()' to save whatever important information you will then need.
These print outputs will then appear in the 'Observation:' field, which will be available as input for the next step.
In the end you have to return a final answer using the `final_answer` tool.

Here are the rules you should always follow to solve your task:
1. Always provide a 'Thought:' sequence, and a 'Code:\n```py' sequence ending with '```<end_code>' sequence, else you will fail.
2. Use only variables that you have defined!
3. Always use the right arguments for the tools. DO NOT pass the arguments as a dict, but use the arguments directly.
4. Take care to not chain too many sequential tool calls in the same code block, especially when the output format is unpredictable.
5. Call a tool only when needed, and never re-do a tool call that you previously did with the exact same parameters.
6. Don't name any new variable with the same name as a tool.
7. Never create any notional variables in our code, as having these in your logs might derail you from the true variables.
8. You can use imports in your code, but only from the following list of modules: {{authorized_imports}}
9. The state persists between code executions: so if in one step you've created variables or imported modules, these will all persist.
10. Don't give up! You're in charge of solving the task, not providing directions to solve it.

On top of performing computations in the Python code snippets that you create, you only have access to these tools:

{{tool_descriptions}}"""
        
        enhanced_prompt = base_prompt + """

🎯 ENHANCED DOMAIN EXPERTISE & STRATEGIC REASONING:

CORE STRATEGY - SMART DATA ACCESS:
1. For album/discography questions: Use enhanced_wikipedia_search with section_filter="Discography" and try category pages first
2. For research questions: Start with enhanced_wikipedia_search, then web_search for verification
3. For file analysis: Use file_handler first, then vision_analyzer for images, audio_transcriber for audio
4. For chess positions: Use vision_analyzer for board images, then chess_position_analyzer for analysis

🧠 WIKIPEDIA OPTIMIZATION (CRITICAL FOR PERFORMANCE):
• ALWAYS try enhanced_wikipedia_search with specific parameters:
  - For "Mercedes Sosa albums": enhanced_wikipedia_search(query="Mercedes Sosa", data_type="albums")
  - For discographies: enhanced_wikipedia_search(query="Artist Name", section_filter="Discography", data_type="albums")
  - For biographical data: enhanced_wikipedia_search(query="Person Name", section_filter="Biography")
• The enhanced Wikipedia tool uses REST API and category pages - much faster than general web search
• Example: "How many albums did X release?" → enhanced_wikipedia_search(query="X", data_type="albums") gets direct answer

📊 TOOL SELECTION INTELLIGENCE:
• enhanced_wikipedia_search: Wikipedia research, discographies, biographical data, factual information
• web_search: Current events, recent information, verification, additional sources  
• vision_analyzer: Image analysis, chess boards, charts, document OCR
• audio_transcriber: Audio file transcription, speech-to-text
• chess_position_analyzer: Chess position analysis, best moves, game evaluation
• file_handler: File processing, data extraction from various formats
• visit_webpage: Specific webpage content extraction

⚡ PERFORMANCE OPTIMIZATION:
• For questions about artist albums between years: Use enhanced_wikipedia_search with year_range parameter
• For chess board images: vision_analyzer → chess_position_analyzer pipeline
• For multimedia questions: Route to appropriate specialized tool first
• Always use print() statements to show your reasoning and intermediate results

🎭 PLANNING & REFLECTION:
During planning intervals, consider:
- Have I used the most efficient tool for this domain?
- Should I try enhanced_wikipedia_search before general web search?
- Do I need to process any files or multimedia content?
- Is there a more direct path to the answer?

Remember: Enhanced Wikipedia tool solves 80% of truncation issues by using targeted API calls instead of downloading full pages.
"""
        
        return enhanced_prompt
    
    def run(self, query: str, **kwargs) -> str:
        """
        Run the enhanced agent system on a query.
        
        Args:
            query: The question or task to process
            **kwargs: Additional arguments
            
        Returns:
            Final result from the agent
        """
        if not self.manager_agent:
            return "❌ Error: Enhanced agent not initialized"
        
        logger.info(f"🚀 Processing query: {query[:100]}...")
        
        try:
            result = self.manager_agent.run(query, **kwargs)
            logger.info("✅ Query processing completed")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error processing query: {str(e)}")
            return f"❌ Error processing query: {str(e)}"
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get status of the enhanced agent system."""
        status = {
            "model_id": self.model_id,
            "planning_interval": self.planning_interval,
            "agent_status": "✅ Active" if self.manager_agent else "❌ Failed",
            "tools": getattr(self, 'tool_status', {})
        }
        
        return status

def create_multi_agent_system(model_id: str = None, planning_interval: int = 3) -> MultiAgentSystem:
    """
    Create and return a configured enhanced agent system.
    
    Args:
        model_id: Model identifier to use
        planning_interval: Steps between planning phases
        
    Returns:
        Configured MultiAgentSystem instance
    """
    return MultiAgentSystem(model_id=model_id, planning_interval=planning_interval)

# Convenience function for backwards compatibility
def get_enhanced_agent(model_id: str = None):
    """Get an enhanced agent system (backwards compatibility)."""
    system = create_multi_agent_system(model_id=model_id)
    return system.manager_agent if system.manager_agent else None 