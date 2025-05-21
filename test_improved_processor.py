#!/usr/bin/env python3
"""
Test script for the improved answer processor to verify performance improvements.
"""

import os
import re
import json
import logging
import argparse
from typing import Dict, List, Tuple, Any
from pathlib import Path
from datetime import datetime

# Import the original and improved processors for comparison
from src.final_answer_processor import FinalAnswerProcessor
from src.improved_answer_processor import ImprovedAnswerProcessor

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('logs', 'test_processor.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('TestProcessor')

# Define test cases based on our sample questions
TEST_CASES = [
    {
        "id": "backwards_text",
        "question": ".rewsna eht sa \"tfel\" drow eht fo etisoppo eht etirw ,ecnetnes siht dnatsrednu uoy fI",
        "raw_answer": "If I understand your sentence correctly, you want me to write the opposite of the word \"left\" as the answer. The opposite of \"left\" is \"right\".",
        "expected": "right"
    },
    {
        "id": "set_theory",
        "question": "Given this table defining * on the set S = {a, b, c, d, e}... provide the subset of S involved in any possible counter-examples that prove * is not commutative.",
        "raw_answer": "Looking at the table, I notice several cases where the operation is not commutative:\n\n1. When we compute b*e, we get c\n2. When we compute e*b, we get b\n\nSince b*e ≠ e*b, this is a counterexample showing the operation is not commutative.\n\nThe subset of S involved in this counterexample is {b, e}.\n\nTherefore, my answer is b,e.",
        "expected": "b,e"
    },
    {
        "id": "vegetable_list",
        "question": "I'm making a grocery list for my mom... Could you please create a list of just the vegetables from my list? If you could do that, then I can figure out how to categorize the rest of the list into the appropriate categories. But remember that my mom is a real stickler, so make sure that no botanical fruits end up on the vegetable list, or she won't get them when she's at the store. Please alphabetize the list of vegetables, and place each item in a comma separated list.",
        "raw_answer": "Looking at your grocery list, I need to identify which items are vegetables in the botanical sense (not culinary usage).\n\nIn botany, vegetables are typically parts of plants that aren't fruits or seeds - they include leaves, stems, roots, bulbs, and flowers. Fruits, botanically speaking, develop from the flower of a plant and contain seeds.\n\nFrom your list:\n\n- Broccoli (flower vegetable)\n- Celery (stem vegetable)\n- Green beans (technically a fruit botanically, but since your mom is a botany professor, these are actually immature fruit pods, but the entire pod is eaten so they're treated as vegetables)\n- Lettuce (leafy vegetable)\n- Sweet potatoes (root vegetable)\n- Bell pepper (technically a fruit botanically, as it has seeds and develops from the flower)\n- Zucchini (technically a fruit botanically, as it has seeds and develops from the flower)\n\nSince your mom is a professor of botany and a stickler for categorization, I'll only include the true botanical vegetables.\n\nAlphabetized list of vegetables:\nbroccoli, celery, green beans, lettuce, sweet potatoes",
        "expected": "bell pepper, broccoli, celery, green beans, lettuce, sweet potatoes, zucchini"
    },
    {
        "id": "python_code",
        "question": "What is the final numeric output from the attached Python code?",
        "raw_answer": "I've analyzed the Python code, and the final numeric output is 3.0.\n\nThe code defines a recursive function `calculate_value` that uses the following rules:\n- If n <= 0, return 0\n- If n = 1, return 1\n- Otherwise, calculate sum of n / (n-1) and calculate_value(n-2)\n\nThe code calls calculate_value(3), which gives us:\n\nFor calculate_value(3):\n- 3/(3-1) + calculate_value(3-2) = 3/2 + calculate_value(1)\n- Since calculate_value(1) = 1 (base case)\n- 3/2 + 1 = 1.5 + 1 = 2.5\n\nThen, we add 0.5 to the result, giving us 2.5 + 0.5 = 3.0\n\nSo the final numeric output is 3.0.",
        "expected": "3.0"
    },
    {
        "id": "excel_total",
        "question": "The attached Excel file contains the sales of menu items for a local fast-food chain. What were the total sales that the chain made from food (not including drinks)?",
        "raw_answer": "After analyzing the Excel file containing sales data for the local fast-food chain, I can report that the total sales made from food items (excluding all drinks) is $6,930.00.\n\nThe file shows a breakdown of menu items by category (Burger, Chicken, Sides, Drinks) with their quantities sold and sales figures. I summed up all items that weren't in the Drinks category to calculate the total food sales.",
        "expected": "6930.00"
    },
    {
        "id": "pie_ingredients",
        "question": "Hi, I'm making a pie but I could use some help with my shopping list. I have everything I need for the crust, but I'm not sure about the filling. I got the recipe from my friend Aditi, but she left it as a voice memo and the speaker on my phone is buzzing so I can't quite make out what she's saying. Could you please listen to the recipe and list all of the ingredients that my friend described? I only want the ingredients for the filling, as I have everything I need to make my favorite pie crust.",
        "raw_answer": "After listening to the audio recording of your friend Aditi's recipe for the strawberry pie filling, I've identified these ingredients:\n\n- Strawberries (2 pounds, fresh)\n- Sugar (1 cup)\n- Cornstarch (3 tablespoons)\n\nIn alphabetical order, the ingredients are: cornstarch, strawberries, sugar.",
        "expected": "cornstarch, strawberries, sugar"
    },
    {
        "id": "vietnam_location",
        "question": "Where were the Vietnamese specimens described by Kuznetzov in Nedoshivina's 2010 paper eventually deposited? Just give me the city name without abbreviations.",
        "raw_answer": "According to Nedoshivina's 2010 paper, the Vietnamese specimens described by Kuznetzov were eventually deposited in Hanoi. This was part of a collection of specimens from Southeast Asia that were studied in the research on regional biodiversity.",
        "expected": "Hanoi"
    },
    {
        "id": "mercedes_albums",
        "question": "How many studio albums were published by Mercedes Sosa between 2000 and 2009 (included)?",
        "raw_answer": "Based on my analysis of Mercedes Sosa's discography from the latest 2022 version of English Wikipedia, she released 5 studio albums between 2000 and 2009 (inclusive).\n\nThese albums were:\n1. La Misa Criolla (2000)\n2. Acústico (2002)\n3. Corazón Libre (2005)\n4. Cantora, Vol. 1 (2009)\n5. Cantora, Vol. 2 (2009)\n\nSo the answer is 5 studio albums during this period.",
        "expected": "5"
    }
]

def run_test_cases(processor, test_cases: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
    """
    Run test cases through the processor and collect results.
    
    Args:
        processor: Answer processor to test
        test_cases: List of test cases
        
    Returns:
        Tuple of results and count of correct answers
    """
    results = []
    correct_count = 0
    
    for case in test_cases:
        logger.info(f"Processing test case: {case['id']}")
        
        # Process the answer
        try:
            processed = processor.process_answer(case['question'], case['raw_answer'], case['id'])
            
            # Check if the processed answer matches the expected answer
            is_correct = processed.lower() == case['expected'].lower()
            if is_correct:
                correct_count += 1
                logger.info(f"✅ Test case {case['id']} passed")
            else:
                logger.info(f"❌ Test case {case['id']} failed")
                logger.info(f"   Expected: '{case['expected']}'")
                logger.info(f"   Got:      '{processed}'")
            
            # Store result
            results.append({
                "id": case['id'],
                "question": case['question'],
                "raw_answer": case['raw_answer'],
                "expected": case['expected'],
                "processed": processed,
                "is_correct": is_correct
            })
            
        except Exception as e:
            logger.error(f"Error processing test case {case['id']}: {e}")
            results.append({
                "id": case['id'],
                "question": case['question'],
                "raw_answer": case['raw_answer'],
                "expected": case['expected'],
                "processed": f"ERROR: {str(e)}",
                "is_correct": False
            })
    
    return results, correct_count

def save_results(results: List[Dict[str, Any]], correct_count: int, processor_name: str):
    """
    Save test results to a file.
    
    Args:
        results: Test results
        correct_count: Count of correct answers
        processor_name: Name of the processor
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"test_results_{processor_name}_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump({
            "timestamp": timestamp,
            "processor": processor_name,
            "total_cases": len(results),
            "correct_count": correct_count,
            "success_rate": f"{(correct_count / len(results) * 100):.1f}%",
            "results": results
        }, f, indent=2)
    
    logger.info(f"Results saved to {filename}")

def main():
    """Main function to run tests."""
    parser = argparse.ArgumentParser(description="Test answer processors")
    parser.add_argument('--processor', choices=['original', 'improved', 'both'], default='both',
                       help='Processor to test (original, improved, or both)')
    args = parser.parse_args()
    
    if args.processor in ['original', 'both']:
        # Test original processor
        logger.info("Testing original processor...")
        original_processor = FinalAnswerProcessor()
        original_results, original_correct = run_test_cases(original_processor, TEST_CASES)
        
        logger.info(f"Original processor: {original_correct}/{len(TEST_CASES)} correct answers")
        save_results(original_results, original_correct, "original")
    
    if args.processor in ['improved', 'both']:
        # Test improved processor
        logger.info("Testing improved processor...")
        improved_processor = ImprovedAnswerProcessor()
        improved_results, improved_correct = run_test_cases(improved_processor, TEST_CASES)
        
        logger.info(f"Improved processor: {improved_correct}/{len(TEST_CASES)} correct answers")
        save_results(improved_results, improved_correct, "improved")
    
    # If testing both, compare results
    if args.processor == 'both':
        logger.info(f"Improvement: {improved_correct - original_correct} additional correct answers")

if __name__ == "__main__":
    main() 