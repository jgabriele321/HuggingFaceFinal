#!/usr/bin/env python
"""
Model Availability Tester for SmolAgent

This script tests the availability of various models that can be used with the SmolAgent,
helping diagnose and fix model configuration issues.
"""

import os
import sys
import json
import logging
import argparse
import requests
from dotenv import load_dotenv

# Add the parent directory to Python path to allow imports from src
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger("ModelTester")

# Load environment variables
load_dotenv()

def test_huggingface_token():
    """Test if the Hugging Face token is valid."""
    hf_token = os.environ.get("HF_TOKEN")
    
    if not hf_token:
        logger.error("❌ HF_TOKEN environment variable is not set")
        return False
    
    try:
        # Test the token with a simple API call
        headers = {"Authorization": f"Bearer {hf_token}"}
        response = requests.get(
            "https://huggingface.co/api/whoami",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            user_info = response.json()
            logger.info(f"✅ HF_TOKEN is valid. Authenticated as: {user_info.get('name', 'Unknown')}")
            return True
        else:
            logger.error(f"❌ HF_TOKEN validation failed. Status code: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
    except Exception as e:
        logger.error(f"❌ Error testing HF_TOKEN: {e}")
        return False

def test_model_availability(model_id, provider=None):
    """Test if a specific model is available."""
    try:
        from huggingface_hub import InferenceClient, model_info
        
        logger.info(f"Testing model: {model_id}" + (f" (Provider: {provider})" if provider else ""))
        
        # First check model info
        try:
            if not provider:  # Only check model_info for Hub models
                info = model_info(model_id)
                logger.info(f"✅ Model info retrieved successfully: {info.modelId}")
                logger.info(f"   Pipeline tags: {info.pipeline_tags}")
        except Exception as e:
            logger.warning(f"⚠️ Could not retrieve model info: {e}")
        
        # Try to initialize the client
        if provider:
            # For external providers like OpenAI
            api_key = os.environ.get(f"{provider.upper()}_API_KEY")
            if not api_key:
                logger.error(f"❌ {provider.upper()}_API_KEY environment variable is not set")
                return False
            
            if provider == "openai":
                try:
                    import openai
                    client = openai.OpenAI(api_key=api_key)
                    response = client.chat.completions.create(
                        model=model_id,
                        messages=[{"role": "user", "content": "Hello"}],
                        max_tokens=10
                    )
                    logger.info(f"✅ Successfully tested {provider} model: {model_id}")
                    return True
                except Exception as e:
                    logger.error(f"❌ Error testing {provider} model: {e}")
                    return False
            
            elif provider == "anthropic":
                try:
                    import anthropic
                    client = anthropic.Anthropic(api_key=api_key)
                    response = client.messages.create(
                        model=model_id,
                        max_tokens=10,
                        messages=[{"role": "user", "content": "Hello"}]
                    )
                    logger.info(f"✅ Successfully tested {provider} model: {model_id}")
                    return True
                except Exception as e:
                    logger.error(f"❌ Error testing {provider} model: {e}")
                    return False
            
            else:
                logger.error(f"❌ Unsupported provider: {provider}")
                return False
        else:
            # For Hugging Face models
            hf_token = os.environ.get("HF_TOKEN")
            client = InferenceClient(model=model_id, token=hf_token)
            
            # Test text generation
            try:
                response = client.text_generation(
                    "Hello, how are you?",
                    max_new_tokens=10,
                    temperature=0.7
                )
                logger.info(f"✅ Successfully generated text with model: {model_id}")
                logger.info(f"   Response: {response}")
                return True
            except Exception as e:
                logger.warning(f"⚠️ Text generation failed: {e}")
                
                # Try chat completion
                try:
                    response = client.chat_completion(
                        messages=[{"role": "user", "content": "Hello"}],
                        max_tokens=10
                    )
                    logger.info(f"✅ Successfully used chat completion with model: {model_id}")
                    return True
                except Exception as e:
                    logger.error(f"❌ Chat completion also failed: {e}")
                    return False
    except ImportError as e:
        logger.error(f"❌ Missing required packages: {e}")
        logger.error("Run 'pip install -r requirements.txt' to install dependencies")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error testing model {model_id}: {e}")
        return False

def test_smolagents_integration():
    """Test if smolagents can be imported and used."""
    try:
        from smolagents import CodeAgent, InferenceClientModel
        
        logger.info("✅ Successfully imported smolagents")
        
        # Check smolagents version
        import importlib.metadata
        version = importlib.metadata.version("smolagents")
        logger.info(f"   smolagents version: {version}")
        
        if version < "0.13.1":
            logger.warning(f"⚠️ smolagents version {version} is older than recommended (0.13.1+)")
            logger.warning("   Consider upgrading with: pip install --upgrade smolagents>=0.13.1")
        
        return True
    except ImportError as e:
        logger.error(f"❌ Error importing smolagents: {e}")
        logger.error("   Install with: pip install smolagents>=0.13.1")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error testing smolagents: {e}")
        return False

def test_agent_initialization():
    """Test initializing the SmolAgent."""
    try:
        from agent import SmolAgent
        
        logger.info("Testing SmolAgent initialization...")
        
        # Test with mock mode first
        try:
            mock_agent = SmolAgent(use_mock=True)
            logger.info("✅ Successfully initialized SmolAgent in mock mode")
            
            # Test a simple question
            result = mock_agent("What is 2 + 2?")
            logger.info(f"   Mock agent response: {result}")
        except Exception as e:
            logger.error(f"❌ Error initializing mock agent: {e}")
        
        # Test with real token if available
        hf_token = os.environ.get("HF_TOKEN")
        if hf_token:
            try:
                real_agent = SmolAgent(hf_token=hf_token)
                logger.info("✅ Successfully initialized SmolAgent with HF token")
                return True
            except Exception as e:
                logger.error(f"❌ Error initializing agent with HF token: {e}")
                return False
        else:
            logger.warning("⚠️ Skipping real agent test as HF_TOKEN is not set")
            return False
    except ImportError:
        logger.error("❌ Could not import SmolAgent from agent.py")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error testing agent initialization: {e}")
        return False

def main():
    """Main function to run the tests."""
    parser = argparse.ArgumentParser(description="Test model availability for SmolAgent")
    parser.add_argument("--test-all", action="store_true", help="Test all available models")
    parser.add_argument("--model", help="Test a specific model ID")
    parser.add_argument("--provider", help="Provider for the model (e.g., openai, anthropic)")
    args = parser.parse_args()
    
    logger.info("Starting model availability tests...")
    
    # Test Hugging Face token
    token_valid = test_huggingface_token()
    
    # Test smolagents integration
    smolagents_valid = test_smolagents_integration()
    
    if args.model:
        # Test a specific model
        model_valid = test_model_availability(args.model, args.provider)
    elif args.test_all:
        # Test all predefined models
        models_to_test = [
            {"model_id": "meta-llama/Meta-Llama-3-8B-Instruct", "provider": None},
            {"model_id": "mistralai/Mistral-7B-Instruct-v0.2", "provider": None},
            {"model_id": "google/gemma-7b-it", "provider": None},
            {"model_id": "microsoft/phi-2", "provider": None},
            {"model_id": "google/flan-t5-large", "provider": None}
        ]
        
        # Test OpenAI if API key is available
        if os.environ.get("OPENAI_API_KEY"):
            models_to_test.append({"model_id": "gpt-3.5-turbo", "provider": "openai"})
        
        # Test Anthropic if API key is available
        if os.environ.get("ANTHROPIC_API_KEY"):
            models_to_test.append({"model_id": "claude-instant-1", "provider": "anthropic"})
        
        results = []
        for model in models_to_test:
            result = test_model_availability(model["model_id"], model["provider"])
            results.append({
                "model_id": model["model_id"],
                "provider": model["provider"],
                "available": result
            })
        
        # Print summary
        logger.info("\n--- Model Availability Summary ---")
        available_models = [m for m in results if m["available"]]
        
        if available_models:
            logger.info("Available models:")
            for model in available_models:
                provider = f" ({model['provider']})" if model["provider"] else ""
                logger.info(f"✅ {model['model_id']}{provider}")
            
            # Recommend the best available model
            if any(m["model_id"] == "gpt-3.5-turbo" and m["available"] for m in results):
                recommended = "gpt-3.5-turbo (openai)"
            elif any(m["model_id"] == "meta-llama/Meta-Llama-3-8B-Instruct" and m["available"] for m in results):
                recommended = "meta-llama/Meta-Llama-3-8B-Instruct"
            else:
                # Get the first available model
                model = available_models[0]
                provider = f" ({model['provider']})" if model["provider"] else ""
                recommended = f"{model['model_id']}{provider}"
            
            logger.info(f"\nRecommended model: {recommended}")
        else:
            logger.error("❌ No models are available!")
    else:
        # Default: test the SmolAgent initialization
        agent_valid = test_agent_initialization()
    
    logger.info("Test completed.")

if __name__ == "__main__":
    main() 