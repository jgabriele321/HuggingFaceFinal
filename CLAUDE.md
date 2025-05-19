# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Command Reference

### Running the Application

```bash
# Run the main application
python app.py

# Run the enhanced agent demo
python demo.py

# Run the capital finder demo
python demo_capital.py
```

### Testing

```bash
# Run all tests
./run_tests.sh

# Run final answer processor tests
./run_answer_processor_tests.sh

# Run specific test files
python test_enhanced_agent.py
python test_answer_extractor.py
python test_capital.py
python tests/test_final_answer_processor.py
```

### Environment Setup

```bash
# Install required dependencies
pip install -r requirements.txt

# Configure environment (copy template and edit)
cp config/.env.template config/.env
nano config/.env

# Required environment variables:
# HF_TOKEN=your_huggingface_token_here
# API_URL=https://agents-course-unit4-scoring.hf.space
# OPENROUTER_API_KEY=your_openrouter_api_key
```

### Agent Selection

```bash
# Switch to specific agent implementation
python scripts/update_agent.py --implementation openrouter  # For OpenRouter implementation
python scripts/update_agent.py --implementation openai      # For OpenAI implementation
```

## Project Structure

This repository implements an intelligent agent using the smolagents framework for the Hugging Face Agents Course. The agent is designed to answer various questions including those requiring analysis of images, chess positions, data files, and web search.

### Key Components

1. **Agent Implementations**:
   - `src/agent.py`: Main agent implementation (auto-generated)
   - `src/openrouter_agent.py`: Implementation using OpenRouter API
   - `src/openai_agent.py`: Implementation using OpenAI API
   - `src/enhanced_agent.py`: Implementation using ReAct framework
   - `src/agent_adapter.py`: Compatibility layer for original interface

2. **Tools**:
   - `src/duckduckgo_search_tool.py`: Web search functionality
   - `src/webpage_tool.py`: Web content extraction
   - `src/youtube_tool.py`: YouTube video analysis
   - `src/python_interpreter_tool.py`: Code execution capabilities
   - `src/tool_validator.py`: Validation for tool usage

3. **Answer Processing**:
   - `src/final_answer_processor.py`: Transforms verbose model responses into concise answers
   - `src/final_answer_extractor.py`: Enhanced answer extraction for specific formats

4. **Infrastructure**:
   - `app.py`: Main application with Gradio UI
   - `config/logging_config.py`: Enhanced logging configuration
   - `scripts/`: Helper scripts for various tasks

## Architecture Overview

The system uses a modular architecture with the following workflow:

1. Questions are received via API or user input
2. The agent processes each question and selects appropriate tools
3. Tools perform web searches, analyze files, extract video content, etc.
4. Raw model responses are post-processed by the final answer processor
5. Concise, formatted answers are returned and can be submitted for evaluation

The agent uses a robust error handling system with multiple fallback mechanisms:
- Model failures trigger automatic retries with exponential backoff
- Tool errors are handled gracefully with appropriate recovery steps
- API connection issues trigger fallbacks to alternative models

## Development Notes

1. When modifying tool code, respect the pattern of defining a tool class and providing a getter function that instantiates it (e.g., `get_youtube_tool()`).

2. When adding new functionality:
   - Update the relevant agent class (typically in `enhanced_agent.py`)
   - Register new tools in the `_initialize_tools()` method
   - Add appropriate tool validation in `tool_validator.py`

3. The logging system:
   - All modules use Python's logging framework
   - Logs are stored in the `logs/` directory
   - Each component has its own log file for easier debugging

4. Answer processing:
   - The `final_answer_processor.py` module handles transforming verbose answers
   - It uses pattern matching and LLM-based extraction
   - Extend the pattern detection for new question types as needed

5. The system supports multiple agent implementations through the adapter pattern - all implementations share a common interface that can be used interchangeably in the app.