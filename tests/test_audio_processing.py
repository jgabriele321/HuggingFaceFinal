#!/usr/bin/env python3
"""
Test script for audio file processing improvements in FileHandlerTool.
"""

import os
import sys
import json
from src.file_handler_tool import FileHandlerTool

def test_audio_transcription():
    """
    Test audio transcription functionality with various audio files.
    """
    print("Running audio transcription tests...")
    
    # Initialize the file handler
    handler = FileHandlerTool()
    
    test_cases = [
        # Strawberry pie recipe audio
        {
            "file_name": "99c9cc74-fdc8-46c6-8f8d-3ce2d3bfeea3.mp3",
            "expected_keywords": ["strawberry", "pie", "filling", "sugar", "cornstarch", "lemon"],
            "check_keywords": True
        },
        # Calculus homework audio with page numbers
        {
            "file_name": "1f975693-876d-457b-a649-393859e79bf3.mp3",
            "expected_pages": ["23", "27", "29", "34", "38", "42", "45"],
            "check_pages": True
        }
    ]
    
    failures = 0
    for i, case in enumerate(test_cases, 1):
        print(f"\nTest {i}: Processing audio file '{case['file_name']}'")
        try:
            # Process the audio file
            result = handler.read_file("test", case["file_name"])
            
            # Check if processing succeeded
            if "error" in result:
                print(f"❌ FAIL: Error processing file: {result['error']}")
                failures += 1
                continue
                
            # Check transcript
            transcript = result.get("transcript", "")
            print(f"Transcript excerpt: {transcript[:100]}...")
            
            # Check for keywords if specified
            if case.get("check_keywords") and "expected_keywords" in case:
                keywords_found = all(keyword.lower() in transcript.lower() for keyword in case["expected_keywords"])
                if keywords_found:
                    print(f"✅ PASS: All expected keywords found in transcript")
                else:
                    missing = [k for k in case["expected_keywords"] if k.lower() not in transcript.lower()]
                    print(f"❌ FAIL: Missing keywords in transcript: {missing}")
                    failures += 1
            
            # Check for page numbers if specified
            if case.get("check_pages") and "expected_pages" in case:
                pages = result.get("page_numbers", [])
                print(f"Extracted page numbers: {pages}")
                
                # Check if all expected pages are found
                all_found = all(page in pages for page in case["expected_pages"])
                if all_found:
                    print(f"✅ PASS: All expected page numbers found")
                else:
                    missing = [p for p in case["expected_pages"] if p not in pages]
                    print(f"❌ FAIL: Missing page numbers: {missing}")
                    failures += 1
            
        except Exception as e:
            print(f"❌ FAIL: Exception during test: {str(e)}")
            failures += 1
    
    print(f"\nAudio processing tests completed: {len(test_cases) - failures}/{len(test_cases)} passed")
    return failures == 0

def test_audio_metadata():
    """
    Test audio metadata extraction.
    """
    print("\nRunning audio metadata extraction tests...")
    
    # Initialize the file handler
    handler = FileHandlerTool()
    
    test_cases = [
        # MP3 file
        {
            "file_name": "99c9cc74-fdc8-46c6-8f8d-3ce2d3bfeea3.mp3",
            "expected_fields": ["duration", "format", "type"]
        },
        # Another MP3 file
        {
            "file_name": "1f975693-876d-457b-a649-393859e79bf3.mp3",
            "expected_fields": ["duration", "format", "type"]
        }
    ]
    
    failures = 0
    for i, case in enumerate(test_cases, 1):
        print(f"\nTest {i}: Extracting metadata from '{case['file_name']}'")
        try:
            # Process the audio file
            result = handler.read_file("test", case["file_name"])
            
            # Check if processing succeeded
            if "error" in result:
                print(f"❌ FAIL: Error processing file: {result['error']}")
                failures += 1
                continue
                
            # Check that all expected fields are present
            missing_fields = [field for field in case["expected_fields"] if field not in result]
            if missing_fields:
                print(f"❌ FAIL: Missing expected fields: {missing_fields}")
                failures += 1
            else:
                print(f"✅ PASS: All expected metadata fields present")
                print(f"File info: Type={result.get('type')}, Format={result.get('format')}, Duration={result.get('duration', 'N/A')}")
            
        except Exception as e:
            print(f"❌ FAIL: Exception during test: {str(e)}")
            failures += 1
    
    print(f"\nAudio metadata tests completed: {len(test_cases) - failures}/{len(test_cases)} passed")
    return failures == 0

if __name__ == "__main__":
    print("=== Audio Processing Tests ===\n")
    
    # Check if test files exist
    test_files = ["99c9cc74-fdc8-46c6-8f8d-3ce2d3bfeea3.mp3", "1f975693-876d-457b-a649-393859e79bf3.mp3"]
    missing_files = []
    
    for file_name in test_files:
        if not os.path.exists(os.path.join("files", file_name)) and not os.path.exists(os.path.join("test", file_name)):
            missing_files.append(file_name)
    
    if missing_files:
        print(f"WARNING: The following test files are missing: {missing_files}")
        print("Tests may fail if these files are not present in the 'files' or 'test' directory.")
    
    transcription_success = test_audio_transcription()
    metadata_success = test_audio_metadata()
    
    if transcription_success and metadata_success:
        print("\nALL TESTS PASSED!")
        sys.exit(0)
    else:
        print("\nSOME TESTS FAILED!")
        sys.exit(1) 