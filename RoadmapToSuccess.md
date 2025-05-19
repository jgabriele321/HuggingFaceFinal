# Roadmap to Success: Improving Agent Performance

## Overview
This roadmap outlines the step-by-step process to improve our agent's performance from 2/20 to 15/20 questions. Each phase must be completed and tested before moving to the next phase. The phases are designed to build upon each other, starting with core functionality and moving to more complex features.

## Implementation Guidelines

1. Each phase must be completed and tested before moving to the next
2. All changes should be committed to git after testing
3. Use existing tools and infrastructure where possible
4. Focus on improving rather than replacing
5. Maintain academic honesty - no hardcoding
6. Document all changes and improvements

## Success Criteria

For each phase:
1. All tests pass
2. Performance improves on relevant test questions
3. No regression in other areas
4. Code remains maintainable and documented

## Moving Between Phases

To move to the next phase:
1. All tests for current phase must pass
2. Performance improvement must be demonstrated
3. Code must be committed and stable
4. Documentation must be updated
5. Explicit approval from supervisor required

## Final Validation

After all phases:
1. Run full test suite
2. Verify performance on all 20 questions
3. Document any remaining issues
4. Plan for future improvements 

## Phase 1: Core Answer Processing
**Focus**: Improve answer formatting and validation

### 1.1 Final Answer Processor Enhancement
**Objective**: Enhance the existing `FinalAnswerProcessor` class to handle specific output formats more accurately.

#### 1.1.1 Currency Format Detection
```python
# Add to _detect_answer_format method
currency_patterns = [
    r'\$|\busd\b|\bdollars?\b',
    r'\bprice\b|\bcost\b|\bworth\b|\bvalue\b',
    r'\bspent\b|\bpaid\b|\bexpense\b'
]
format_info["currency"] = any(re.search(pattern, question.lower()) for pattern in currency_patterns)
format_info["decimal_places"] = 2 if format_info["currency"] else None
```

#### 1.1.2 Decimal Precision Control
```python
# Add to _validate_format method
if format_info["numeric_answer"]:
    # Extract the number
    number_match = re.search(r'(\d+\.?\d*)', answer)
    if number_match:
        number = float(number_match.group(1))
        if format_info["currency"]:
            # Format as USD with 2 decimal places
            return f"{number:.2f}"
        elif format_info["decimal_places"]:
            # Format with specified precision
            return f"{number:.{format_info['decimal_places']}f}"
```

#### 1.1.3 List Processing Enhancement
```python
# Add to _validate_format method
if format_info["list_answer"]:
    items = [item.strip() for item in answer.split(",")]
    # Remove empty items and "and"
    items = [item for item in items if item and not item.lower().startswith("and")]
    # Remove articles
    items = [re.sub(r'^(the|a|an)\s+', '', item, flags=re.IGNORECASE) for item in items]
    if format_info["alphabetical"]:
        items = sorted(items, key=str.lower)
    return ", ".join(items)
```

#### 1.1.4 Exact Match Enhancement
```python
# Add to _validate_format method
if format_info["exact_match"]:
    # Remove explanatory text
    answer = re.sub(r'\s*\([^)]*\)', '', answer)  # Remove parentheticals
    answer = re.sub(r'\s*-.*$', '', answer)  # Remove everything after dash
    answer = re.sub(r'\s*:.*$', '', answer)  # Remove everything after colon
    return answer.strip()
```

#### Testing Plan
1. Create test suite in `tests/test_final_answer_processor.py`:
```python
def test_currency_formatting(self):
    processor = FinalAnswerProcessor()
    test_cases = [
        ("What is the total cost in USD?", "The total is 42.1", "42.10"),
        ("How many dollars were spent?", "They spent $123.456", "123.46"),
        ("What is the value?", "Value is 89", "89.00")
    ]
    for question, answer, expected in test_cases:
        self.assertEqual(processor.process_answer(question, answer), expected)

def test_list_formatting(self):
    processor = FinalAnswerProcessor()
    test_cases = [
        ("List the items alphabetically", "dog, cat, bird", "bird, cat, dog"),
        ("What are the components?", "The CPU, and the GPU, the RAM", "CPU, GPU, RAM")
    ]
    for question, answer, expected in test_cases:
        self.assertEqual(processor.process_answer(question, answer), expected)
```

### 1.2 Python Code Execution
**Objective**: Enhance the `PythonInterpreterTool` to handle code execution and output formatting more reliably.

#### 1.2.1 Output Capture Enhancement
```python
# Add to PythonInterpreterTool class
def _capture_output(self, code: str) -> str:
    import io
    import sys
    from contextlib import redirect_stdout, redirect_stderr

    output = io.StringIO()
    with redirect_stdout(output), redirect_stderr(output):
        try:
            # Execute in isolated namespace
            namespace = {}
            exec(code, namespace)
            # Check for return value
            if '_return_value' in namespace:
                return str(namespace['_return_value'])
        except Exception as e:
            return f"Error: {str(e)}"
    return output.getvalue()
```

#### 1.2.2 Decimal Precision Control
```python
# Add to PythonInterpreterTool class
def _format_numeric_output(self, output: str, precision: Optional[int] = None) -> str:
    try:
        # Try to convert to float
        value = float(output)
        if precision is not None:
            return f"{value:.{precision}f}"
        # Default formatting for integers
        if value.is_integer():
            return str(int(value))
        return str(value)
    except ValueError:
        return output
```

#### 1.2.3 Timeout Implementation
```python
# Add to PythonInterpreterTool class
import signal
from contextlib import contextmanager

@contextmanager
def timeout(seconds: int):
    def handler(signum, frame):
        raise TimeoutError(f"Code execution timed out after {seconds} seconds")
    
    # Set signal handler
    signal.signal(signal.SIGALRM, handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        # Restore default handler
        signal.alarm(0)
```

#### Testing Plan
1. Create test suite in `tests/test_python_interpreter.py`:
```python
def test_output_capture(self):
    interpreter = PythonInterpreterTool()
    test_cases = [
        ("print('hello')", "hello\n"),
        ("x = 5; print(x)", "5\n"),
        ("def f(): return 42\nf()", "42")
    ]
    for code, expected in test_cases:
        self.assertEqual(interpreter.execute(code), expected)

def test_numeric_precision(self):
    interpreter = PythonInterpreterTool()
    test_cases = [
        ("print(1/3)", 2, "0.33"),
        ("print(42.123456)", 3, "42.123"),
        ("print(100)", None, "100")
    ]
    for code, precision, expected in test_cases:
        self.assertEqual(
            interpreter._format_numeric_output(
                interpreter.execute(code), 
                precision
            ), 
            expected
        )
```

### Success Criteria for Phase 1

1. All test cases pass with 100% coverage
2. Currency values are consistently formatted with 2 decimal places
3. Lists are properly sorted when required
4. Python code execution handles timeouts gracefully
5. Numeric precision is maintained as specified
6. No regressions in existing functionality

### Validation Steps

1. Run the full test suite:
```bash
python -m pytest tests/
```

2. Test with specific format cases:
```python
# Test currency formatting
processor = FinalAnswerProcessor()
result = processor.process_answer(
    "What was the total cost?",
    "The total cost was $42.1"
)
assert result == "42.10"

# Test list formatting
result = processor.process_answer(
    "List all vegetables alphabetically",
    "tomatoes, carrots, and broccoli"
)
assert result == "broccoli, carrots, tomatoes"
```

3. Test Python execution:
```python
interpreter = PythonInterpreterTool()
result = interpreter.execute("""
def calculate_total(items):
    return sum(items)
print(calculate_total([1.23, 4.56, 7.89]))
""")
assert float(result) == 13.68
```

### Implementation Order

1. Start with currency and numeric formatting
2. Implement list processing improvements
3. Add exact match enhancements
4. Implement Python execution improvements
5. Add timeout handling
6. Implement comprehensive testing

### Completion Checklist

- [ ] Currency format detection implemented
- [ ] Decimal precision control working
- [ ] List processing enhancement completed
- [ ] Exact match enhancement added
- [ ] Python output capture improved
- [ ] Timeout handling implemented
- [ ] All tests passing
- [ ] Documentation updated
- [ ] Code reviewed and approved

Only proceed to Phase 2 when all items in the checklist are complete and verified.

**----------- Stop here, you are only working on phase one, if you are looking for phase 2 keep going ------------------------**

## Phase 2: File Processing
**Focus**: Improve file handling and data extraction

≈### 2.1 Excel Processing
- Enhance `FileHandlerTool` for Excel
- Add number formatting control
- Implement currency handling
- Add data validation

**Testing**:
1. Test Excel file reading
2. Verify currency formatting
3. Validate numerical precision
4. Test error handling

### 2.2 File Type Detection
- Enhance `FileHandlerTool` type detection
- Add specialized handlers for different formats
- Implement validation checks
- Add error recovery

**Testing**:
1. Test different file types
2. Verify correct handler selection
3. Validate error handling
4. Test recovery mechanisms

**----------- Stop here, you are only working on phase two, if you are looking for phase 3 keep going ------------------------**


## Phase 3: Web Integration
**Focus**: Enhance web search and media handling

### 3.1 YouTube Integration
- Enhance existing `YouTubeTool`
- Implement transcript API properly
- Add fallback mechanisms
- Improve error handling

**Testing**:
1. Test transcript retrieval
2. Verify fallback mechanisms
3. Validate error handling
4. Test with various video types

### 3.2 Web Search Enhancement
- Improve `DuckDuckGoSearchTool`
- Add result validation
- Implement retry logic
- Add specialized handlers for:
  - Wikipedia pages
  - News articles
  - Academic sources

**Testing**:
1. Test search functionality
2. Verify retry mechanism
3. Validate specialized handlers
4. Test error recovery

**----------- Stop here, you are only working on phase three, if you are looking for phase 4 keep going -----------------------**

## Phase 4: Agent Intelligence
**Focus**: Improve decision making and planning

### 4.1 Planning Enhancement
- Implement planning steps using `planning_interval`
- Add result verification
- Implement confidence scoring
- Add cross-reference checking

**Testing**:
1. Test planning functionality
2. Verify result accuracy
3. Validate confidence scoring
4. Test cross-referencing

### 4.2 Error Recovery
- Implement graceful fallbacks
- Add retry strategies
- Improve error messages
- Add recovery suggestions

**Testing**:
1. Test error handling
2. Verify recovery mechanisms
3. Validate retry logic
4. Test fallback strategies

## Implementation Guidelines

1. Each phase must be completed and tested before moving to the next
2. All changes should be committed to git after testing
3. Use existing tools and infrastructure where possible
4. Focus on improving rather than replacing
5. Maintain academic honesty - no hardcoding
6. Document all changes and improvements

## Success Criteria

For each phase:
1. All tests pass
2. Performance improves on relevant test questions
3. No regression in other areas
4. Code remains maintainable and documented

## Moving Between Phases

To move to the next phase:
1. All tests for current phase must pass
2. Performance improvement must be demonstrated
3. Code must be committed and stable
4. Documentation must be updated
5. Explicit approval from supervisor required

## Final Validation

After all phases:
1. Run full test suite
2. Verify performance on all 20 questions
3. Document any remaining issues
4. Plan for future improvements 