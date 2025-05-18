# Environment Configuration

This directory contains configuration files for the SmolAgent project.

## Important Files

- `.env`: Contains environment variables (not committed to version control)
- `.env.template`: Template showing required environment variables

## Setup Instructions

1. Copy `.env.template` to `.env`:
   ```bash
   cp .env.template .env
   ```

2. Edit `.env` and add your API keys:
   ```
   # Hugging Face API token
   HF_TOKEN=your_huggingface_token_here
   
   # OpenRouter API key (for Claude and other models)
   OPENROUTER_API_KEY=your_openrouter_api_key_here
   
   # OpenAI API key (optional, for GPT models)
   OPENAI_API_KEY=your_openai_api_key_here
   
   # API URL for questions and submission
   API_URL=https://agents-course-unit4-scoring.hf.space
   ```

3. Choose your agent implementation:
   ```bash
   # Use OpenRouter implementation (recommended)
   export SMOL_IMPLEMENTATION=openrouter
   
   # Or use OpenAI implementation
   export SMOL_IMPLEMENTATION=openai
   ```

## Testing Your Configuration

You can test if your environment variables are properly loaded with:

```bash
python scripts/direct_env_checker.py
```

## Switching Implementations

To switch between OpenRouter and OpenAI implementations:

```bash
# Using the utility script
python scripts/update_agent.py --implementation openrouter
# or
python scripts/update_agent.py --implementation openai
```

This will copy the selected implementation to `src/agent.py`. 