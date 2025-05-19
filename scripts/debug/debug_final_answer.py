#!/usr/bin/env python3
"""
Debug script for final_answer_processor
Provides detailed tracing for answer transformation process
"""

import os
import sys
import logging
import json
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

# Configure verbose debug logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('debug_final_answer.log', mode='w')
    ]
)

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

# Create specific logger for this script
logger = logging.getLogger("debug_script")
logger.setLevel(logging.DEBUG)

try:
    # Import the final answer processor
    from src.final_answer_processor import process_final_answer, FinalAnswerProcessor
    logger.info("Successfully imported final_answer_processor")
    
    # Create a processor instance with more verbose debugging
    processor = FinalAnswerProcessor()
    logger.debug("Created FinalAnswerProcessor instance")
    
    # Monkey patch the processor's logger to be more verbose
    answer_logger = logging.getLogger("final_answer_processor")
    answer_logger.setLevel(logging.DEBUG)
    
    # Add a file handler specific for this debugging session
    detailed_handler = logging.FileHandler('logs/detailed_processor.log', mode='w')
    detailed_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    answer_logger.addHandler(detailed_handler)
    
except Exception as e:
    logger.error(f"Error importing modules: {e}")
    sys.exit(1)

def test_with_examples():
    """Run tests on examples that represent different question types"""
    logger.info("=== Starting Example Tests ===")
    
    examples = [
        {
            "question": "How many studio albums did Mercedes Sosa release between 2000 and 2009?",
            "verbose_answer": "Based on my analysis, Mercedes Sosa published 4 studio albums between 2000 and 2009."
        },
        {
            "question": "What is the NASA award number that supported the work?",
            "verbose_answer": "The NASA award number that supported the work was NAS5-26555."
        },
        {
            "question": "List all vegetables found in the recipe, alphabetically.",
            "verbose_answer": "The recipe contains the following vegetables: tomatoes, onions, bell peppers, garlic, and carrots."
        },
        {
            "question": "Who nominated the only Featured Article on English Wikipedia about a dinosaur that was promoted in November 2006?",
            "verbose_answer": "After researching, I found that the only Featured Article on English Wikipedia about a dinosaur that was promoted in November 2006 was nominated by User:Firsfron."
        },
        {
            "question": "In the video https://www.youtube.com/watch?v=L1vXCYZAYYM, what is the highest number of bird species shown simultaneously?",
            "verbose_answer": "After watching the video, the highest number of bird species shown simultaneously appears to be 6, which occurs at the 1:32 mark where you can see a variety of songbirds at a feeder including cardinals, chickadees, and finches."
        }
    ]
    
    # Process each example
    for i, example in enumerate(examples):
        logger.info(f"=== Example {i+1} ===")
        logger.info(f"Question: {example['question']}")
        logger.info(f"Verbose answer: {example['verbose_answer']}")
        
        # Process the answer
        try:
            answer = processor.process_answer(example['question'], example['verbose_answer'])
            logger.info(f"Final answer: '{answer}'")
            
            # Analyze the transformation
            if answer != example['verbose_answer']:
                pct_reduced = 100 - (len(answer) / len(example['verbose_answer']) * 100)
                logger.info(f"Answer reduced by {pct_reduced:.1f}% from {len(example['verbose_answer'])} to {len(answer)} characters")
            else:
                logger.info("No transformation occurred")
                
        except Exception as e:
            logger.error(f"Error processing example {i+1}: {e}")
            
        logger.info("-" * 50)

def test_from_logs():
    """Parse recent log files to find problematic examples"""
    logger.info("=== Testing from Logs ===")
    
    # Check if we have recent agent logs
    agent_log_path = 'logs/agent.log'
    if not os.path.exists(agent_log_path):
        logger.warning(f"Agent log file {agent_log_path} not found, skipping test_from_logs")
        return
    
    # Parse the log for examples
    log_examples = []
    try:
        with open(agent_log_path, 'r') as f:
            lines = f.readlines()
            
        # Look for pattern indicating a raw answer before postprocessing
        for i, line in enumerate(lines):
            if "Raw answer before postprocessing:" in line:
                # Extract the raw answer
                raw_answer = line.split("Raw answer before postprocessing:", 1)[1].strip()
                
                # Look for a question earlier in the log (within 10 lines)
                question = None
                for j in range(max(0, i-10), i):
                    if "Question:" in lines[j]:
                        question = lines[j].split("Question:", 1)[1].strip()
                        # Remove truncation if present
                        if question.endswith("..."):
                            question = question[:-3]
                        break
                
                if question:
                    log_examples.append({"question": question, "verbose_answer": raw_answer})
    
        # Test with log examples (use up to 5)
        for i, example in enumerate(log_examples[:5]):
            logger.info(f"=== Log Example {i+1} ===")
            logger.info(f"Question: {example['question']}")
            logger.info(f"Verbose answer: {example['verbose_answer']}")
            
            # Process the answer
            try:
                answer = processor.process_answer(example['question'], example['verbose_answer'])
                logger.info(f"Final answer: '{answer}'")
                
                # Analyze the transformation
                if answer != example['verbose_answer']:
                    pct_reduced = 100 - (len(answer) / len(example['verbose_answer']) * 100)
                    logger.info(f"Answer reduced by {pct_reduced:.1f}% from {len(example['verbose_answer'])} to {len(answer)} characters")
                else:
                    logger.info("No transformation occurred")
                    
            except Exception as e:
                logger.error(f"Error processing log example {i+1}: {e}")
                
            logger.info("-" * 50)
                
    except Exception as e:
        logger.error(f"Error processing log files: {e}")

def debug_pattern_matching(question, verbose_answer):
    """Debug the pattern matching process specifically"""
    logger.info("=== Debugging Pattern Matching ===")
    logger.info(f"Question: {question}")
    logger.info(f"Verbose answer: {verbose_answer}")
    
    # Extract directly with patterns
    try:
        # Directly call the extract method
        pattern_result = processor._extract_answer_with_patterns(question, verbose_answer)
        logger.info(f"Pattern extraction result: '{pattern_result}'")
        
        # Try numeric extraction specifically
        if hasattr(processor, '_extract_numeric_answer'):
            numeric_result = processor._extract_numeric_answer(verbose_answer, question)
            logger.info(f"Numeric extraction result: '{numeric_result}'")
            
        # Try entity extraction
        if hasattr(processor, '_detect_entity_type'):
            entity_types = processor._detect_entity_type(question)
            logger.info(f"Detected entity types: {entity_types}")
            
            if hasattr(processor, '_select_entity_by_context'):
                entity = processor._select_entity_by_context(verbose_answer, entity_types)
                logger.info(f"Entity extraction result: '{entity}'")
        
    except Exception as e:
        logger.error(f"Error in pattern matching debug: {e}")
    
    logger.info("-" * 50)

def main():
    logger.info("=== Starting Final Answer Processor Debug ===")
    
    # Run examples
    test_with_examples()
    
    # Test from logs
    test_from_logs()
    
    # Debug specific problematic cases
    debug_pattern_matching(
        "In the video https://www.youtube.com/watch?v=L1vXCYZAYYM, what is the highest number of bird species shown simultaneously?",
        "After watching the video, the highest number of bird species shown simultaneously appears to be 6, which occurs at the 1:32 mark where you can see a variety of songbirds at a feeder including cardinals, chickadees, and finches."
    )
    
    debug_pattern_matching(
        "Who nominated the only Featured Article on English Wikipedia about a dinosaur that was promoted in November 2006?",
        "After researching, I found that the only Featured Article on English Wikipedia about a dinosaur that was promoted in November 2006 was nominated by User:Firsfron."
    )
    
    logger.info("=== Final Answer Processor Debug Complete ===")

if __name__ == "__main__":
    main() 