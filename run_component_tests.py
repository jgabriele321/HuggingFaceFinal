#!/usr/bin/env python3
"""
Master script to run all component tests.

This script will execute all component-specific test scripts and report
their results without requiring the full assessment framework.
"""

import os
import sys
import subprocess
import time

def print_header(text):
    """Print a formatted header."""
    width = 80
    print("\n" + "=" * width)
    print(f"{text.center(width)}")
    print("=" * width + "\n")

def run_test(script_name, description):
    """Run a test script and report results."""
    print_header(f"Running {description}")
    
    start_time = time.time()
    result = subprocess.run([sys.executable, script_name], capture_output=True, text=True)
    end_time = time.time()
    
    # Print the output
    print(result.stdout)
    
    if result.stderr:
        print(f"Errors:\n{result.stderr}")
    
    success = result.returncode == 0
    status = "✅ PASSED" if success else "❌ FAILED"
    print(f"{status} in {end_time - start_time:.2f} seconds\n")
    
    return success

def main():
    """Run all component tests."""
    print_header("Component Tests for Agent Improvements")
    
    tests = [
        ("test_currency_formatting.py", "Currency Formatting Tests"),
        ("test_audio_processing.py", "Audio Processing Tests"),
        ("test_excel_processing.py", "Excel Processing Tests")
    ]
    
    results = []
    
    for script, description in tests:
        if not os.path.exists(script):
            print(f"⚠️ WARNING: Test script {script} not found. Skipping.")
            results.append((script, "SKIPPED"))
            continue
        
        success = run_test(script, description)
        results.append((script, "PASSED" if success else "FAILED"))
    
    # Print summary
    print_header("Test Summary")
    
    for script, status in results:
        status_symbol = "✅" if status == "PASSED" else "❌" if status == "FAILED" else "⚠️"
        print(f"{status_symbol} {script}: {status}")
    
    # Return success if all tests passed
    return all(status == "PASSED" for _, status in results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 