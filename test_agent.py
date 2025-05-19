import logging
import argparse
import os
from src.enhanced_agent import EnhancedAgent
from src.final_answer_extractor import extract_final_answer
from smolagents import HfApiModel

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_api_keys():
    """Check if required API keys are available."""
    hf_token = os.environ.get("HF_TOKEN")
    
    if not hf_token:
        logger.warning("No Hugging Face token found. Using free model which may be unreliable.")
        return False
    return True

def main():
    parser = argparse.ArgumentParser(description='Test EnhancedAgent')
    parser.add_argument('--query', type=str, required=False, 
                        default="In the video https://www.youtube.com/watch?v=L1vXCYZAYYM, what is the highest number of bird species to be on camera simultaneously?",
                        help='The query to test')
    parser.add_argument('--model', type=str, required=False,
                        default="meta-llama/Llama-3.3-70B-Instruct",  # Using Llama by default
                        help='Model to use for inference')
    parser.add_argument('--timeout', type=int, required=False,
                        default=120,  # 120 second timeout for larger models
                        help='Timeout in seconds for model inference')
    args = parser.parse_args()
    
    try:
        # Check API keys
        has_api_keys = check_api_keys()
        
        # Initialize the agent with Llama model
        logger.info(f"Initializing EnhancedAgent with model: {args.model}")
        
        # Use HfApiModel for Hugging Face API access
        model = HfApiModel(
            model_id=args.model,
            token=os.getenv("HF_TOKEN")  # Will use token if available, otherwise free tier
        )
        
        agent = EnhancedAgent(
            model=model,
            max_steps=8,
            planning_interval=2,
            timeout=args.timeout
        )
        
        # Run the query
        logger.info(f"Running query: {args.query}")
        result = agent(args.query)
        
        # Process the final answer
        logger.info("Processing final answer...")
        final_answer = extract_final_answer(args.query, result)
        
        print("\nResults:")
        print("-" * 50)
        print(f"Raw result:\n{result}")
        print("-" * 50)
        print(f"Final answer: {final_answer}")
        print("-" * 50)
        
    except Exception as e:
        logger.error(f"Error during execution: {str(e)}", exc_info=True)
        print(f"Error: {str(e)}")
        if not has_api_keys:
            print("\nNote: No HF_TOKEN found. Using free tier which may have rate limits.")
            print("Example: export HF_TOKEN='your-token-here'")

if __name__ == "__main__":
    main() 