---
title: Hugging Face Agents Course - Final Assignment
emoji: 🕵️‍♂️
colorFrom: indigo
colorTo: indigo
sdk: gradio
sdk_version: 5.25.2
app_file: app.py
pinned: false
hf_oauth: true
# optional, default duration is 8 hours/480 minutes. Max duration is 30 days/43200 minutes.
hf_oauth_expiration_minutes: 480
---

# Hugging Face Agents Course - Final Assignment

This project implements an intelligent agent using the smolagents framework for the Hugging Face Agents Course final assignment. The agent is designed to answer a variety of questions, including those requiring analysis of images, chess positions, data files, and more.

## Repository Structure

The repository is organized into the following directories:

- `src/`: Core agent implementations
  - `agent.py`: The current active agent implementation
  - `openrouter_agent.py`: OpenRouter API-based implementation
  - `openai_agent.py`: OpenAI API-based implementation
  - `concise_agent.py`: Implementation focused on producing concise, exact answers
  - `agent_adapter.py`: Compatibility layer for the original interface

- `tests/`: Testing utilities
  - `test_implementations.py`: Tests for different agent implementations
  - `test_model.py`: Tests model availability and configurations
  - `test_hf_client.py`: Tests Hugging Face client connectivity

- `scripts/`: Helper scripts
  - `update_agent.py`: Script to switch between implementations
  - `fix_app.py`: Utility to patch app.py if needed
  - `install.sh`: Installation script
  - `save_to_github.sh`: GitHub backup utility
  - `direct_env_checker.py`: Environment variable checker
  - `clean_root.sh`: Script to clean up redundant files

- `docs/`: Documentation
  - `agentmind.md`: Detailed agent design and reasoning
  - `model_troubleshooting.md`: Common model issues and solutions
  - `reorganization_plan.md`: Repository organization planning
  - `reorganization_summary.md`: Summary of reorganization changes

- `config/`: Configuration files
  - `.env`: Environment variables with API keys (not in version control)
  - `.env.template`: Template for setting up environment variables
  - `README.md`: Instructions for environment configuration

- `backups/`: Backup files
  - Contains backup versions of modified files

## Latest Improvements

- **Model Reliability Enhancements**:
  - 🔄 Robust model loading with multiple fallbacks (Llama 3, Mistral, Claude, Gemma)
  - 🔁 Automatic retry mechanism for model failures
  - 🚨 Detailed error reporting and logging
  
- **Web Integration**:
  - 🌐 Web search capability for factual questions
  - 🎬 YouTube video transcript extraction and analysis
  - 📚 Wikipedia integration for entity-related questions
  
- **File Processing**:
  - 📊 Enhanced file type detection and processing
  - 🔍 Specialized handlers for different file formats
  - ✅ File integrity verification during download

## Setup Instructions

1. Clone this repository:
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables in the config directory:
   ```bash
   # Copy the template
   cp config/.env.template config/.env
   
   # Edit the .env file with your API keys
   nano config/.env
   ```
   
   Required environment variables:
   ```
   # Hugging Face API token
   HF_TOKEN=your_huggingface_token_here
   
   # API URL for questions and submission
   API_URL=https://agents-course-unit4-scoring.hf.space
   
   # OpenRouter API key (for Claude and other models)
   OPENROUTER_API_KEY=your_openrouter_api_key
   ```

4. Choose your agent implementation:
   ```bash
   # Switch to OpenRouter implementation (recommended)
   python scripts/update_agent.py --implementation openrouter
   
   # Or use OpenAI implementation
   python scripts/update_agent.py --implementation openai
   ```

5. Run the application:
   ```bash
   python app.py
   ```

## Running Tests

Run all tests with the convenience script:
```bash
./run_tests.sh
```

Or run specific tests:
```bash
# Test implementations
python tests/test_implementations.py

# Test model availability
python tests/test_model.py
```

## Agent Features

The agent uses a modular architecture with the following components:

- **SmolAgent**: Main agent class that orchestrates the entire process
- **Specialized Tools**:
  - `analyze_image`: For general image analysis
  - `analyze_chess_position`: For chess-specific image analysis
  - `analyze_data_file`: For CSV, JSON, and text files
  - `web_search`: For retrieving factual information from the web
  - `analyze_youtube_video`: For extracting and analyzing video content
  - `execute_code`: For running code snippets safely
  - `search_documentation`: For retrieving relevant information
- **Question Processing**:
  - Question type detection
  - Pre-processing with context enhancement
  - Post-processing to format answers according to requirements
- **File Handling**:
  - Automatic download of question-related files
  - Organized storage in the `files` directory
  - Robust error handling with retry logic
- **Caching**:
  - Results are cached to avoid recomputing answers
  - Cache is maintained between runs in the `cache` directory

## How It Works

1. The app fetches questions from the API endpoint
2. For each question, it detects the question type and downloads any associated files
3. For factual questions, it may use web search to supplement information
4. It then processes the question with the appropriate tools
5. If model errors occur, it uses a fallback strategy with multiple retries
6. The answer is formatted according to the question type and cached
7. All answers are submitted back to the API for scoring

## Error Handling and Reliability

The agent implements comprehensive error handling:

- Multiple model fallbacks if primary models fail
- Automatic retries for transient errors
- Specialized handling for different question types
- Graceful degradation when services are unavailable
- Detailed logging for debugging and analysis

## Contributing

Feel free to contribute to this project by submitting pull requests or opening issues.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

Check out the configuration reference at https://huggingface.co/docs/hub/spaces-config-reference

# SmolAgent Implementations

This repository contains two robust SmolAgent implementations that bypass Hugging Face model issues by using OpenRouter and OpenAI APIs instead.

## Features

### Common Features (Both Implementations)
- Robust error handling with retry logic
- Proper formatting for the CodeAgent parser
- Type-safe message handling
- Built-in file analysis without problematic dependencies
- Auto-detection of response formats (code vs. text)

### OpenRouter Implementation
- Uses reliable models like Claude 3 Haiku
- Configurable model selection
- Compatible with the existing SmolAgent interface

### OpenAI Implementation
- Uses GPT-3.5-Turbo for cost-effectiveness
- Maintains compatibility with the smolagents framework
- Properly processes file information

## Installation

1. Clone the repository
2. Install the requirements:

```bash
pip install requests smolagents
```

3. Set up your API keys:

```bash
# For OpenRouter
export OPENROUTER_API_KEY=your_openrouter_api_key

# For OpenAI
export OPENAI_API_KEY=your_openai_api_key
```

You can also create a `.env` file in the project root:

```
OPENROUTER_API_KEY=your_openrouter_api_key
OPENAI_API_KEY=your_openai_api_key
```

## Usage

### Running the Test Script

Test both implementations:

```bash
python test_implementations.py
```

Test only one implementation:

```bash
# For OpenRouter
python test_implementations.py --openrouter

# For OpenAI
python test_implementations.py --openai
```

### Using in Your Code

#### OpenRouter Implementation

```python
from src.openrouter_agent import SmolAgent

# Initialize the agent
agent = SmolAgent()  # Uses environment variable OPENROUTER_API_KEY

# Or with explicit API key and model
agent = SmolAgent(
    openrouter_api_key="your_api_key", 
    model_id="anthropic/claude-3-haiku"
)

# Ask a question
response = agent("What is the capital of France?")
print(response)

# Code generation
code = agent("Write a function to calculate the factorial of a number in Python")
print(code)

# With file analysis
response = agent("Analyze this Python file", file_path="example.py")
print(response)
```

#### OpenAI Implementation

```python
from src.openai_agent import SmolAgent

# Initialize the agent
agent = SmolAgent()  # Uses environment variable OPENAI_API_KEY

# Or with explicit API key and model
agent = SmolAgent(
    openai_api_key="your_api_key", 
    model_id="gpt-3.5-turbo"
)

# Ask a question
response = agent("What is the capital of France?")
print(response)

# Code generation
code = agent("Write a function to calculate the factorial of a number in Python")
print(code)

# With file analysis
response = agent("Analyze this Python file", file_path="example.py")
print(response)
```

## Troubleshooting

### API Key Issues

- Ensure your API keys are valid and have not expired
- Check that the environment variables are properly set
- Verify network connectivity to the API endpoints

### Model Errors

- Try switching to a different model if you encounter model-specific issues
- Ensure your API key has access to the requested model
- Monitor your API usage and quotas

### Integration Problems

- Make sure you have the latest version of `smolagents` installed
- Check that the dependencies are correctly installed
- Verify that your Python version is 3.8 or higher

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Final Answer Processor

The project includes a comprehensive final answer processor that ensures the SmolAgent's responses match exactly what automated evaluation systems expect. This component is critical for achieving high evaluation scores, as it transforms verbose, explanatory answers into concise, exact-match responses.

### Key Features

- **Format Detection**: Intelligently identifies the expected answer format based on question analysis
- **Advanced Pattern Extraction**: Uses sophisticated regex patterns to extract precise answers from verbose text
- **Format-Specific Validation**: Tailors processing to handle various answer types:
  - Numeric answers (extracts just the number without units or text)
  - Lists (standardizes formatting, handles alphabetical ordering)
  - Yes/No questions (normalizes to "Yes" or "No")
  - Chess moves (extracts standard algebraic notation)
  - Code snippets (removes markdown formatting)
  - File analyses (extracts key data points)
  - Reversed text (handles detecting and processing backwards text)

- **Truncation Prevention**: Ensures answers are never cut off mid-response
- **Length Validation**: Implements checks to prevent answers from being too verbose
- **LLM-Assisted Processing**: Optionally uses an LLM to extract answers when pattern matching isn't sufficient

### Usage

```python
from src.final_answer_processor import process_final_answer

# The original question
question = "How many albums did the artist release in 2010?"

# A verbose answer from the agent
verbose_answer = "After analyzing the artist's discography, I found that they released 3 studio albums in 2010."

# Process into a concise, exact-match answer
final_answer = process_final_answer(question, verbose_answer)
# Result: "3"
```

### Running Tests

To run the comprehensive test suite for the answer processor:

```bash
./run_answer_processor_tests.sh
```