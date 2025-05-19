#!/usr/bin/env python3
"""
Test examples for the final answer processor.
"""

from src.final_answer_processor import process_final_answer

def test_examples():
    """Test the processor on specific examples."""
    
    examples = [
        {
            "question": "How many studio albums did Mercedes Sosa release between 2000 and 2009?",
            "answer": "Based on the analysis done above, the answer is: Mercedes Sosa published 4 studio albums between 2000 and 2009 (included)."
        },
        {
            "question": "What is the best move in this chess position?",
            "answer": "After analyzing the position, I believe Qh4 is the best move as it threatens checkmate."
        },
        {
            "question": "List the ingredients in this recipe, alphabetically.",
            "answer": "The recipe includes the following ingredients: cornstarch, ripe strawberries, salt, white sugar."
        },
        {
            "question": "What page numbers do I need to study for the Calculus mid-term?",
            "answer": "The page numbers you need to study for the Calculus mid-term, as mentioned in the audio recording, are: 5, 12, 25, 31, 42, 57. Please study the material on these page numbers in ascending order."
        },
        {
            "question": "What is the NASA award number that supported the work?",
            "answer": "The answer to the user task is: The work performed by R. Thompson, S. Barthelmy, and D. Palmer was supported by NASA award number NAS5-26555."
        },
        {
            "question": "According to the recording, which city has the highest pollution levels?",
            "answer": "Based on the information gathered in the previous exchange, the answer is: Hanoi"
        },
        {
            "question": "Who were the pitchers mentioned in the baseball discussion?",
            "answer": "The answer to the user's task is: Uehara,"
        }
    ]
    
    print("Testing answer processor on specific examples:")
    print("=============================================")
    
    for i, example in enumerate(examples):
        print(f"\nExample {i+1}:")
        print(f"Question: {example['question']}")
        print(f"Verbose answer: {example['answer']}")
        
        processed = process_final_answer(example['question'], example['answer'])
        print(f"Processed answer: '{processed}'")
        
        # Check length
        word_count = len(processed.split())
        if word_count <= 10:
            print(f"✅ Concise: {word_count} words")
        else:
            print(f"❌ Too verbose: {word_count} words")
        
        # Check for explanatory phrases
        explanation_markers = ["because", "since", "as it", "which", "that is", "the answer is"]
        has_explanation = any(marker in processed.lower() for marker in explanation_markers)
        if not has_explanation:
            print("✅ No explanatory phrases")
        else:
            print("❌ Contains explanations")

if __name__ == "__main__":
    test_examples() 