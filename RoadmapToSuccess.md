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

### 1.3 Enhanced Debugging Interface
**Objective**: Implement a more helpful debugging UI to diagnose answer processing issues.

#### 1.3.1 Answer Processing Stages Display
- [ ] Add visualization of all processing stages in the UI
- [ ] Show original model response, intermediate transformations, and final result
- [ ] Display format detection decisions for each answer
- [ ] Highlight removed or modified content during processing

#### 1.3.2 Error Tracing and Visualization
- [ ] Implement error tracing to show where in the processing pipeline errors occur
- [ ] Visualize regex pattern matches and their effects on the answer
- [ ] Add color coding to distinguish between original content and modified output
- [ ] Create collapsible sections for detailed debugging information

**Testing**:
1. [ ] Test UI components render correctly
2. [ ] Verify all processing stages are displayed
3. [ ] Validate error tracing functionality
4. [ ] Test with various answer types and processing paths

### Success Criteria for Phase 1

1. All test cases pass with 100% coverage
2. Currency values are consistently formatted with 2 decimal places
3. Lists are properly sorted when required
4. Python code execution handles timeouts gracefully
5. Numeric precision is maintained as specified
6. No regressions in existing functionality
7. Debugging UI provides clear visibility into answer processing stages

### Implementation Order

1. Start with currency and numeric formatting
2. Implement list processing improvements
3. Add exact match enhancements
4. Implement Python execution improvements
5. Add timeout handling
6. Implement comprehensive testing
7. Add debugging interface components

### Completion Checklist

- [x] Currency format detection implemented
- [x] Decimal precision control working
- [ ] List processing enhancement completed ❌
  - While working for some cases (vegetables list), it's inconsistently applied
  - The sorting and cleaning logic might be removing important information
- [ ] Exact match enhancement added ❌
  - Current implementation is incorrectly stripping essential information
  - Many answers show "Unable to determine" or "No information found" when the agent should provide precise answers
  - The regex patterns are likely removing valid parts of answers
- [x] Python output capture improved
- [x] Timeout handling implemented
- [x] Test cases added for all enhancements
- [x] Test scripts updated to run new tests
- [x] Full test suite passing
- [ ] Debugging UI components implemented ❌
  - Need to add visualization of processing stages
  - Error tracing and pattern match highlighting missing
- [x] Documentation updated
    - Added details on the improved indentation handling in PythonInterpreterTool
    - Added special handling for control flow statements to preserve indentation
- [ ] Code reviewed and approved

### 1.4 Response Over-filtering Analysis
**Objective**: Address the primary issue of response over-filtering to improve answer accuracy.

#### 1.4.1 Identified Issues
- [ ] Implement more conservative regex patterns for content stripping
  - Current patterns are too aggressive, removing valid information
  - Need more context-aware filtering based on question types
- [ ] Add content preservation flags for factual responses
  - Certain question types should preserve more explanatory text
  - Create a whitelist of question types that should maintain full responses
- [ ] Implement confidence-based filtering
  - Only strip content when confidence in the remaining answer is high
  - Preserve more information when answer confidence is low

#### 1.4.2 Solution Approach
- [ ] Revise Exact Match Enhancement to be more conservative
  - Only remove clearly explanatory text (e.g., "The answer is...")
  - Keep factual details intact even if they appear parenthetical
- [ ] Add content preservation logic based on question analysis
  - Analyze question to determine if it requires detailed or concise response
  - Apply different filtering rules based on question category
- [ ] Implement answer verification step
  - Check if post-processing answer makes logical sense
  - Roll back to less processed version if filtered answer seems incomplete

**Testing**:
1. [ ] Test with previously failing questions
2. [ ] Verify answers maintain essential information
3. [ ] Validate different filtering rules with various question types
4. [ ] Test answer verification and rollback mechanisms

----------------- STOP do not move on to phase 2 until phase 1 is complete

## Phase 2: Tool Infrastructure and File Processing
**Focus**: Fix tool initialization issues and improve file handling capabilities

### 2.1 Tool Initialization Framework
- [ ] Fix `SmolTool` wrapper to properly call `setup()` method for all wrapped tools ❌
  - [ ] Modify `SmolTool.__init__` to explicitly call `setup()` method if it exists
  - [ ] Implement attribute verification after setup to confirm proper initialization
  - [ ] Add setup logging for debugging tool initialization issues
  - [ ] Create fallback implementations for core functionality when setup fails
- [ ] Address specific tool issues:
  - [ ] Fix DuckDuckGoSearchTool's `requests` attribute issue
  - [ ] Fix YouTubeTool's initialization process
  - [ ] Resolve WebpageTool connectivity problems
- [ ] Implement robust error handling in tool initialization:
  - [ ] Clear error messages for specific failure modes
  - [ ] Automatic retry with exponential backoff
  - [ ] Graceful degradation with minimal functionality when full initialization fails

**Issues**:
- Web-based tools aren't properly initializing, causing research questions to fail
- The fallback implementations aren't providing meaningful responses

**Testing**:
1. [ ] Test initialization sequence for all tools
2. [ ] Verify attribute existence after initialization
3. [ ] Test fallback implementations
4. [ ] Validate error handling during initialization
5. [ ] Verify proper logging of initialization steps

### 2.2 Python Interpreter Enhancement
- [x] Address "signal only works in main thread" threading issue
  - [x] Replace signal-based timeout mechanism with threading.Timer
  - [x] Implement ThreadPoolExecutor for code execution in separate threads
  - [x] Add proper cleanup for thread resources
- [x] Improve error handling and recovery:
  - [x] Implement structured error responses
  - [x] Add descriptive error messages with debugging hints
  - [x] Create fallback execution mode for basic Python operations
- [x] Enhance code execution environment:
  - [x] Add missing standard library imports to authorized list
  - [x] Implement secure environment variables for execution context
  - [x] Add error line highlighting in output

**Testing**:
1. [x] Test Python execution in multithreaded environment
2. [x] Verify timeout handling without signals
3. [x] Validate structured error outputs
4. [x] Test fallback execution mode
5. [x] Verify authorized imports function correctly

### 2.3 Excel and Data File Processing
- [x] Enhance `FileHandlerTool` for Excel processing:
  - [x] Implement native Excel processing without external dependencies
  - [x] Add support for Excel formulas and calculations
  - [x] Create handlers for different Excel formats (XLSX, XLS, CSV)
  - [x] Implement proper cell type detection and conversion
- [x] Improve number formatting and currency handling:
  - [x] Add decimal precision control
  - [x] Implement proper currency symbol recognition and standardization
  - [x] Create locale-aware number formatting
  - [x] Add unit conversion capabilities for numeric values
- [x] Add validation and error recovery:
  - [x] Implement checksum verification for file integrity
  - [x] Add format validation for Excel files
  - [x] Create recovery mechanisms for partially corrupted files
  - [x] Implement row/column limit handling for large files

**Testing**:
1. [x] Test Excel file reading with various formats
2. [x] Verify currency and numeric formatting
3. [x] Validate formula calculation results
4. [x] Test error handling with corrupted files
5. [x] Verify performance with large files

### 2.4 File Type Detection and Specialized Handlers
- [x] Enhance file type detection:
  - [x] Implement content-based file type detection (magic numbers)
  - [x] Add extension-based validation as fallback
  - [x] Create MIME type mapping for proper content handling
- [x] Add specialized handlers for different formats:
  - [x] PDF extraction with text and table support
  - [x] Image analysis with metadata extraction
  - [x] Audio files with basic transcription capabilities
  - [x] ZIP/compressed file handling with extraction
- [x] Implement validation mechanisms:
  - [x] Add file integrity checks for all supported formats
  - [x] Create format specification validation
  - [x] Implement size and content limitation checks
- [x] Add error recovery:
  - [x] Create partial processing for damaged files
  - [x] Implement alternative parsing strategies when primary fails
  - [x] Add automatic format conversion for unsupported types
  - [x] Create meaningful error diagnostics for file issues

**Testing**:
1. [x] Test different file types and detection accuracy
2. [x] Verify specialized handler selection
3. [x] Validate error handling with corrupted files
4. [x] Test recovery mechanisms with partial data
5. [x] Verify cross-format compatibility

### 2.5 Basic Error Handling Framework
- [ ] Create standardized error formats for each tool: ❌
  - [ ] Implement consistent error message structure
  - [ ] Add error categorization (file error, network error, parsing error, etc.)
  - [ ] Include debugging information for troubleshooting
- [ ] Implement basic tool-specific recovery strategies:
  - [ ] Add retry mechanisms for transient errors
  - [ ] Create fallback options for each tool when primary method fails
  - [ ] Add graceful degradation options

**Issues**:
- Many questions result in "Unable to determine" responses instead of partial answers
- Error categorization isn't helping the agent recover gracefully

**Testing**:
1. [ ] Test error handling for each tool
2. [ ] Verify retry mechanisms
3. [ ] Validate fallback options
4. [ ] Test error message formatting

### 2.6 Partial Answer Preservation
**Objective**: Ensure that error handling preserves useful information rather than defaulting to "Unable to determine".

#### 2.6.1 Error Response Improvement
- [ ] Modify error handling to include partial information when available
  - Replace generic "Unable to determine" with specific partial information
  - Include context about what was found even when complete answer isn't available
- [ ] Implement information extraction from error states
  - Extract any useful facts from error responses
  - Maintain provenance information for partial results

#### 2.6.2 Fallback Chain Implementation
- [ ] Create hierarchical fallback sequences for each tool
  - When primary method fails, attempt progressively simpler approaches
  - Provide best available answer even with limited data
- [ ] Add confidence scoring for partial results
  - Indicate confidence level for each partial answer component
  - Use confidence to determine whether to return partial information

**Testing**:
1. [ ] Test with questions that previously returned "Unable to determine"
2. [ ] Verify partial information is preserved and returned
3. [ ] Validate fallback chain functionality
4. [ ] Test confidence scoring accuracy

### Implementation Order and Dependencies
1. [ ] Fix SmolTool wrapper (2.1) first as all other improvements depend on this
2. [x] Address Python Interpreter issues (2.2) next as file processing depends on it
3. [x] Implement Excel processing improvements (2.3)
4. [x] Enhance file type detection (2.4)
5. [ ] Implement basic error handling framework (2.5)
6. [ ] Add partial answer preservation (2.6)

### Phase 2 Completion Notes
- Several key tasks in Phase 2 need revision
- The SmolTool wrapper still has issues with properly initializing web-based tools
- Error handling framework needs significant improvement to preserve partial information
- Fallback implementations for web tools need to provide more meaningful responses
- The Python Interpreter and file handling components are working well

**----------- Stop here, you are only working on phase two, if you are looking for phase 3 keep going ------------------------**

## Phase 3: Web Integration
**Focus**: Enhance web search and media handling

### 3.1 YouTube Integration
- [ ] Enhance existing `YouTubeTool`
- [ ] Implement transcript API properly
- [ ] Add fallback mechanisms
- [ ] Improve error handling

**Testing**:
1. [ ] Test transcript retrieval
2. [ ] Verify fallback mechanisms
3. [ ] Validate error handling
4. [ ] Test with various video types

### 3.2 Web Search Enhancement
- [ ] Improve `DuckDuckGoSearchTool`
- [ ] Add result validation
- [ ] Implement retry logic
- [ ] Add specialized handlers for:
  - [ ] Wikipedia pages
  - [ ] News articles
  - [ ] Academic sources

**Testing**:
1. [ ] Test search functionality
2. [ ] Verify retry mechanism
3. [ ] Validate specialized handlers
4. [ ] Test error recovery

**----------- Stop here, you are only working on phase three, if you are looking for phase 4 keep going -----------------------**

## Phase 4: Agent Intelligence and Advanced Integration
**Focus**: Improve decision making, planning, and cross-tool integration

### 4.1 Planning Enhancement
- [ ] Implement planning steps using `planning_interval`
- [ ] Add result verification
- [ ] Implement confidence scoring
- [ ] Add cross-reference checking

**Testing**:
1. [ ] Test planning functionality
2. [ ] Verify result accuracy
3. [ ] Validate confidence scoring
4. [ ] Test cross-referencing

### 4.2 Advanced Error Recovery and Cross-Tool Integration
- [ ] Implement cross-tool integration framework:
  - [ ] Add shared resource management
  - [ ] Create tool dependency resolution
  - [ ] Implement proper cleanup procedures
  - [ ] Add cross-tool communication channels
- [ ] Create advanced error recovery strategies:
  - [ ] Implement multi-tool recovery flows
  - [ ] Add fallback sequences using alternative tools
  - [ ] Create human-in-the-loop fallback options
  - [ ] Implement self-healing mechanisms
- [ ] Add telemetry and diagnostics system:
  - [ ] Implement execution tracking
  - [ ] Add performance metrics collection
  - [ ] Create diagnostic logging system
  - [ ] Build tool usage statistics dashboard

**Testing**:
1. [ ] Test cross-tool interactions
2. [ ] Verify advanced error recovery strategies
3. [ ] Validate telemetry data accuracy
4. [ ] Test resource management across tools
5. [ ] Verify cleanup procedures

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