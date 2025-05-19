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

- [x] Currency format detection implemented
- [x] Decimal precision control working
- [x] List processing enhancement completed
- [x] Exact match enhancement added
- [x] Python output capture improved
- [x] Timeout handling implemented
- [x] Test cases added for all enhancements
- [x] Test scripts updated to run new tests
- [x] Full test suite passing
- [x] Documentation updated
    - Added details on the improved indentation handling in PythonInterpreterTool
    - Added special handling for control flow statements to preserve indentation
- [ ] Code reviewed and approved

