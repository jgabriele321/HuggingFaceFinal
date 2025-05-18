# Model Troubleshooting Guide

This guide provides solutions for common model configuration issues with the SmolAgent.

## Quick Fix for "Unable to access model" Error

If you're encountering the "404 Client Error: Not Found" error when initializing the agent, follow these steps:

1. **Run the diagnostics script**:
   ```bash
   python test_model.py
   ```
   This will check your Hugging Face token validity and test model availability.

2. **Set your API keys correctly**:
   Make sure your `.env` file contains valid API keys:
   ```
   HF_TOKEN=your_huggingface_token_here
   OPENAI_API_KEY=your_openai_api_key_here (optional)
   ANTHROPIC_API_KEY=your_anthropic_api_key_here (optional)
   ```

3. **Update dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Common Issues and Solutions

### 1. Model Not Found (404 Error)

**Problem**: The specified model ID is not available or accessible.

**Solution**:
- The agent now includes multiple fallback models and will automatically try different ones.
- If all models fail, check if your Hugging Face token has proper permissions.
- Run `python test_model.py --test-all` to see which models are available to you.

### 2. Token Validation Issues

**Problem**: Your Hugging Face token lacks necessary permissions.

**Solution**:
- Verify your token is valid by running `python test_model.py`
- Make sure your token has "read" scope by checking at https://huggingface.co/settings/tokens
- Generate a new token if needed

### 3. Missing Dependencies

**Problem**: Required packages are missing or have incompatible versions.

**Solution**:
- The dependency checker will automatically install missing dependencies
- If automatic installation fails, manually run:
  ```bash
  pip install -r requirements.txt
  ```
- For specific OpenAI or Anthropic integration issues:
  ```bash
  pip install openai anthropic -U
  ```

### 4. Specific Model Recommendations

If you continue experiencing issues, these model configurations are known to work well:

1. **Most reliable (requires OpenAI API key)**:
   ```python
   model = InferenceClientModel(
       model_id="gpt-3.5-turbo",
       provider="openai",
       token=openai_api_key
   )
   ```

2. **Free tier (Hugging Face only)**:
   ```python
   model = InferenceClientModel(
       model_id="microsoft/phi-2",
       token=hf_token
   )
   ```

3. **Offline fallback**:
   Use the mock model by setting `use_mock=True` when initializing SmolAgent:
   ```python
   agent = SmolAgent(use_mock=True)
   ```

## Advanced Troubleshooting

If you need more detailed diagnostics:

1. Check the logs in the `logs/agent.log` file
2. Run `python test_model.py --model MODEL_ID --provider PROVIDER` to test a specific model
3. If you're using a custom model, ensure it's compatible with the InferenceClient

For persistent issues, try clearing the cache directory:
```bash
rm -rf cache/*
```

## Support

If you continue experiencing issues after trying these solutions, please reach out with:
1. The full error message from `logs/agent.log`
2. Output from `python test_model.py --test-all`
3. Your Python version and environment details 