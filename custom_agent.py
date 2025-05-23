#!/usr/bin/env python3
"""
Custom Agent Implementation with OpenRouter Gemini Model and Multi-Agent System

This implementation uses the comprehensive multi-agent system with:
- Research Agent: Enhanced Wikipedia + Web search
- Analysis Agent: Vision + Audio + File processing  
- Chess Agent: Chess analysis with vision integration
- Manager Agent: Orchestration with planning capabilities
"""

import os
import logging
from typing import Optional, Any
from dotenv import load_dotenv

# Load environment variables from config/.env
load_dotenv("config/.env")

# Configure logging
logger = logging.getLogger("CustomAgent")

class GeminiAgent:
    """
    Enhanced agent implementation using multi-agent system with OpenRouter Gemini.
    """
    
    def __init__(self, model_id: str = None, planning_interval: int = 3):
        """
        Initialize the Gemini agent with multi-agent system.
        
        Args:
            model_id: Model to use (defaults to OpenRouter Gemini)
            planning_interval: Steps between planning phases
        """
        self.model_id = model_id or "google/gemini-2.0-flash-exp:free"
        self.planning_interval = planning_interval
        
        # Validate API keys
        self._validate_api_keys()
        
        # Initialize multi-agent system
        self.multi_agent_system = self._initialize_multi_agent_system()
        
        # For compatibility with existing interface
        if hasattr(self.multi_agent_system, 'manager_agent'):
            self.agent = self.multi_agent_system.manager_agent
        else:
            # Fallback case - multi_agent_system is actually an EnhancedAgent
            self.agent = self.multi_agent_system
        
        logger.info("✅ Enhanced Gemini Agent initialized successfully")
    
    def _validate_api_keys(self):
        """Validate that required API keys are available."""
        required_keys = ["OPENROUTER_API_KEY"]
        missing_keys = []
        
        for key in required_keys:
            if not os.environ.get(key):
                missing_keys.append(key)
        
        if missing_keys:
            error_msg = f"Missing required API keys: {', '.join(missing_keys)}"
            logger.error(error_msg)
            raise ValueError(f"{error_msg}. Please set them in your config/.env file.")
        
        # Log available optional keys
        optional_keys = {
            "SERPER_API_KEY": "Web search functionality",
            "OPENAI_API_KEY": "Vision and audio analysis", 
            "STOCKFISH_API_KEY": "Advanced chess analysis",
            "WHISPER_API_KEY": "Audio transcription"
        }
        
        for key, description in optional_keys.items():
            if os.environ.get(key):
                logger.info(f"✅ {key} available - {description} enabled")
            else:
                logger.warning(f"⚠️ {key} not set - {description} will be limited")
    
    def _initialize_multi_agent_system(self):
        """Initialize the comprehensive multi-agent system."""
        try:
            from src.multi_agent_system import create_multi_agent_system
            
            system = create_multi_agent_system(
                model_id=self.model_id,
                planning_interval=self.planning_interval
            )
            
            # Log system status
            status = system.get_agent_status()
            logger.info("🚀 Multi-Agent System Status:")
            for agent_name, agent_status in status["agents"].items():
                logger.info(f"  • {agent_name}: {agent_status}")
            
            if "managed_agents_count" in status:
                logger.info(f"  • Total managed agents: {status['managed_agents_count']}")
            
            print("\n" + "=" * 80)
            print(f"🤖 ENHANCED MULTI-AGENT SYSTEM ACTIVE")
            print(f"Model: {self.model_id}")
            print(f"Planning Interval: {self.planning_interval}")
            print(f"Specialized Agents: {len([s for s in status['agents'].values() if '✅' in s])}")
            print("=" * 80 + "\n")
            
            return system
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize multi-agent system: {str(e)}")
            # Fallback to basic agent
            return self._create_fallback_agent()
    
    def _create_fallback_agent(self):
        """Create a fallback agent if multi-agent system fails."""
        try:
            logger.warning("🔄 Creating fallback agent...")
            from src.enhanced_agent import EnhancedAgent
            
            # Get OpenRouter API key
            openrouter_api_key = os.environ.get("OPENROUTER_API_KEY")
            
            # Create basic enhanced agent
            fallback = EnhancedAgent(
                model_id=self.model_id,
                hf_token=openrouter_api_key
            )
            
            logger.info("✅ Fallback agent created")
            return fallback
            
        except Exception as e:
            logger.error(f"❌ Failed to create fallback agent: {str(e)}")
            return None
    
    def run(self, query: str, **kwargs) -> str:
        """
        Run the enhanced agent system on a query.
        
        Args:
            query: The question or task to process
            **kwargs: Additional arguments
            
        Returns:
            The agent's response
        """
        if not self.multi_agent_system:
            return "❌ Error: Agent system not available"
        
        # Log the query processing
        logger.info(f"🔍 Processing query with enhanced system: {query[:100]}...")
        
        print("\n" + "🔍" * 40)
        print(f"QUERY: {query}")
        print("🔍" * 40 + "\n")
        
        try:
            # Handle both multi-agent system and fallback agent
            if hasattr(self.multi_agent_system, 'run'):
                result = self.multi_agent_system.run(query, **kwargs)
            elif hasattr(self.multi_agent_system, '__call__'):
                result = self.multi_agent_system(query, **kwargs)
            else:
                return "❌ Error: Agent system not properly configured"
            
            print("\n" + "✅" * 40)
            print("QUERY COMPLETED SUCCESSFULLY")
            print("✅" * 40 + "\n")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error processing query: {str(e)}")
            
            print("\n" + "❌" * 40)
            print(f"ERROR: {str(e)}")
            print("❌" * 40 + "\n")
            
            return f"❌ Error processing query: {str(e)}"
    
    def __call__(self, query: str, file_path: Optional[str] = None, 
                 file_name: Optional[str] = None, task_id: Optional[str] = None) -> str:
        """
        Process a query with optional file context (compatibility interface).
        
        Args:
            query: The query to process
            file_path: Optional file path for file-based queries
            file_name: Alternative file path (for compatibility)
            task_id: Optional task ID for tracking
            
        Returns:
            The agent's response
        """
        # Enhance query with file context if provided
        enhanced_query = query
        
        if task_id and (file_name or file_path):
            filename = file_name or os.path.basename(file_path) if file_path else None
            if filename:
                enhanced_query = f"""
Query: {query}

File Information:
- Task ID: {task_id}
- Filename: {filename}
- File Path: {file_path or 'Not provided'}

Please process this query considering the file context. Use the content_analyzer to process the file if needed.
"""
        
        return self.run(enhanced_query)
    
    def get_system_status(self) -> dict:
        """Get comprehensive system status information."""
        if not self.multi_agent_system:
            return {"status": "❌ Agent system not available"}
        
        # Get status from the system
        if hasattr(self.multi_agent_system, 'get_agent_status'):
            status = self.multi_agent_system.get_agent_status()
        else:
            # Fallback case - basic status for EnhancedAgent
            status = {
                "model_id": self.model_id,
                "planning_interval": self.planning_interval,
                "agent_status": "✅ Active (Fallback Mode)",
                "tools": {"basic_tools": "✅ Active"}
            }
        
        # Add API key status
        api_status = {}
        api_keys = [
            "OPENROUTER_API_KEY", "SERPER_API_KEY", "OPENAI_API_KEY", 
            "STOCKFISH_API_KEY", "WHISPER_API_KEY"
        ]
        
        for key in api_keys:
            api_status[key] = "✅ Available" if os.environ.get(key) else "❌ Missing"
        
        status["api_keys"] = api_status
        
        return status
    
    def test_capabilities(self) -> str:
        """Test the capabilities of the multi-agent system."""
        test_queries = [
            "What is 2+2?",  # Simple math
            "Search for information about Python programming",  # Web search
            "Tell me about machine learning"  # General knowledge
        ]
        
        results = []
        results.append("🧪 TESTING MULTI-AGENT SYSTEM CAPABILITIES")
        results.append("=" * 50)
        
        for i, query in enumerate(test_queries, 1):
            try:
                result = self.run(query)
                status = "✅ SUCCESS" if result and not result.startswith("❌") else "❌ FAILED"
                results.append(f"\nTest {i}: {query}")
                results.append(f"Status: {status}")
                results.append(f"Response: {result[:100]}..." if len(result) > 100 else f"Response: {result}")
            except Exception as e:
                results.append(f"\nTest {i}: {query}")
                results.append(f"Status: ❌ FAILED")
                results.append(f"Error: {str(e)}")
        
        # Add system status
        status = self.get_system_status()
        results.append("\n" + "=" * 50)
        results.append("SYSTEM STATUS:")
        for key, value in status.items():
            if isinstance(value, dict):
                results.append(f"\n{key.upper()}:")
                for subkey, subvalue in value.items():
                    results.append(f"  • {subkey}: {subvalue}")
            else:
                results.append(f"• {key}: {value}")
        
        return "\n".join(results)

# For backwards compatibility
class EnhancedAgent(GeminiAgent):
    """Backwards compatibility alias."""
    pass

# For direct usage
if __name__ == "__main__":
    # Create agent instance
    agent = GeminiAgent()
    
    # Run capability test
    print(agent.test_capabilities())
    
    # Test with a sample query
    result = agent("What is the capital of France?")
    print(f"\nSample Query Result: {result}") 