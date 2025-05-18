import os
import gradio as gr
import requests
import inspect
import pandas as pd
import json
import sys
import time
import datetime
import io
import threading
import re
from contextlib import contextmanager
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from config/.env file
config_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config', '.env')
if os.path.exists(config_env_path):
    load_dotenv(dotenv_path=config_env_path)
else:
    # Fallback to .env in root directory (for backward compatibility)
    root_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if os.path.exists(root_env_path):
        load_dotenv(dotenv_path=root_env_path)
    else:
        print("Warning: No .env file found in config/ or root directory.")

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

# Import the SmolAgent class
from src.agent_adapter import SmolAgent

# Add import for the final answer processor
from src.final_answer_processor import process_final_answer

# --- Constants ---
DEFAULT_API_URL = "https://agents-course-unit4-scoring.hf.space"
FILES_DIR = "files"
CACHE_DIR = "cache"
AGENT_MIND_FILE = "docs/agentmind.md"

# Custom print function to capture terminal output
original_print = print
def custom_print(*args, **kwargs):
    # Call the original print function with all args and kwargs to preserve colors
    original_print(*args, **kwargs)
    
    # Strip ANSI color codes before writing to the agent mind file
    # Join all arguments as strings for the log file
    plain_text = ' '.join(str(arg) for arg in args)
    # Strip ANSI escape sequences for the log file (they won't render in markdown)
    plain_text = re.sub(r'\x1b\[[0-9;]*m', '', plain_text)
    append_to_agent_mind(plain_text)

# Replace the built-in print function with our custom one
print = custom_print

# Create a context manager to capture stdout
@contextmanager
def capture_stdout():
    """Context manager to capture stdout and append it to the agent mind file"""
    stdout_original = sys.stdout
    stdout_buffer = io.StringIO()
    
    # Create a thread-safe wrapper that writes to both original stdout and buffer
    class TeeStdout:
        def write(self, data):
            # Write original data to terminal (preserving colors)
            stdout_original.write(data)
            
            # Strip ANSI color codes before writing to buffer
            plain_data = re.sub(r'\x1b\[[0-9;]*m', '', data)
            stdout_buffer.write(plain_data)
            
            stdout_original.flush()
            
        def flush(self):
            stdout_original.flush()
    
    sys.stdout = TeeStdout()
    
    try:
        yield
    finally:
        sys.stdout = stdout_original
        captured = stdout_buffer.getvalue()
        if captured.strip():  # Only append non-empty output
            append_to_agent_mind(f"Captured output:\n```\n{captured}\n```")

def append_to_agent_mind(text):
    """Append text to the agent mind file"""
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(AGENT_MIND_FILE), exist_ok=True)
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # If file doesn't exist, create it with a header
    if not os.path.exists(AGENT_MIND_FILE):
        with open(AGENT_MIND_FILE, 'w') as f:
            f.write(f"# Agent Mind Log\n\n*Started at: {timestamp}*\n\n")
            f.write("This file tracks the agent's thought process and terminal output in real time.\n\n---\n\n")
    
    # Append the text with a timestamp
    with open(AGENT_MIND_FILE, 'a') as f:
        f.write(f"[{timestamp}] {text}\n")

# Ensure directories exist
os.makedirs(FILES_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)

# Track submission statistics
submission_stats = {
    "total": 0,
    "correct": 0,
    "incorrect": 0,
    "unknown": 0
}

def reset_stats():
    """Reset the submission statistics."""
    global submission_stats
    submission_stats = {
        "total": 0,
        "correct": 0,
        "incorrect": 0,
        "unknown": 0
    }

def reset_agent_mind(title="Starting New Run"):
    """Reset the agent mind file and create a fresh one with the given title."""
    if os.path.exists(AGENT_MIND_FILE):
        os.remove(AGENT_MIND_FILE)
    
    # Create a fresh agent mind file with timestamp
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    append_to_agent_mind(f"# Agent Mind Log\n\n*Started at: {timestamp}*\n\n")
    append_to_agent_mind("This file tracks the agent's thought process and terminal output in real time.\n\n---\n\n")
    append_to_agent_mind(f"=== {title} ===\n")

def update_agent_mind_display():
    """Read and return the content of the agent mind file."""
    if os.path.exists(AGENT_MIND_FILE):
        with open(AGENT_MIND_FILE, 'r') as f:
            return f.read()
    return "Agent mind log not found."

def run_agent_locally():
    """
    Run the agent locally without submission - for testing purposes
    """
    # Reset the agent mind file
    reset_agent_mind("Starting Local Test")
    
    with capture_stdout():
        print("Running agent locally for testing...")
        
        try:
            # Use mock model for local testing
            agent = SmolAgent(use_mock=True)
            print("SmolAgent initialized successfully with mock model.")
        except Exception as e:
            print(f"Error instantiating agent: {e}")
            append_to_agent_mind(f"**Error:** {e}")
            append_to_agent_mind("=== End of Local Test ===\n\n")
            return f"Error initializing agent: {e}"
        
        # Test question
        test_question = "What is 2 + 2?"
        print(f"Testing agent with question: {test_question}")
        append_to_agent_mind(f"**Test Question:** {test_question}")
        
        try:
            answer = agent(test_question)
            print(f"Agent response: {answer}")
            append_to_agent_mind(f"**Answer:** {answer}")
            append_to_agent_mind("=== End of Local Test ===\n\n")
            return f"Agent test successful! Answer: {answer}"
        except Exception as e:
            print(f"Error running agent: {e}")
            append_to_agent_mind(f"**Error:** {e}")
            append_to_agent_mind("=== End of Local Test ===\n\n")
            return f"Error running agent: {e}"

def run_local_demo():
    """
    Simplified version for local testing - doesn't require HF login
    """
    # Reset the agent mind file
    reset_agent_mind("Starting Local Demo")
    
    with capture_stdout():
        print("Running in local demo mode...")
        
        # Test questions
        test_questions = [
            {"id": "q1", "question": "What is 2 + 2?", "type": "math"},
            {"id": "q2", "question": "Analyze this chess position and find the best move.", "type": "chess"},
            {"id": "q3", "question": "Describe what's in this image.", "type": "image"}
        ]
        
        try:
            # Use mock model for local testing
            agent = SmolAgent(use_mock=True)
            print("SmolAgent initialized successfully with mock model.")
            
            results = []
            for q in test_questions:
                print(f"\nProcessing question: {q['question']}")
                append_to_agent_mind(f"## Test Question ({q['id']}):")
                append_to_agent_mind(f"**Question:** {q['question']}")
                append_to_agent_mind(f"**Type:** {q['type']}")
                
                answer = agent(q["question"])
                results.append({
                    "Task ID": q["id"],
                    "Question": q["question"],
                    "Type": q["type"],
                    "Answer": answer
                })
                
                print(f"Answer: {answer}")
                append_to_agent_mind(f"**Answer:** {answer}")
                append_to_agent_mind("---\n")
            
            append_to_agent_mind("=== End of Local Demo ===\n\n")
            return "Local test successful! Processed 3 test questions.", pd.DataFrame(results)
        except Exception as e:
            print(f"Error in local demo: {e}")
            append_to_agent_mind(f"**Error:** {e}")
            append_to_agent_mind("=== End of Local Demo ===\n\n")
            return f"Error in local demo: {e}", None

def run_and_submit_all(profile: gr.OAuthProfile | None):
    """
    Fetches all questions, runs the SmolAgent on them, submits all answers,
    and displays the results.
    """
    # Reset the agent mind file
    reset_agent_mind("Starting Full Evaluation Run")
    
    # Use our capture_stdout context manager to capture all output
    with capture_stdout():
        # Reset statistics at the start of a new run
        reset_stats()
        
    # --- Determine HF Space Runtime URL and Repo URL ---
    space_id = os.getenv("SPACE_ID") # Get the SPACE_ID for sending link to the code

    if profile:
        username = f"{profile.username}"
        print(f"User logged in: {username}")
    else:
        print("User not logged in.")
        return "Please Login to Hugging Face with the button.", None, update_agent_mind_display()

    api_url = DEFAULT_API_URL
    questions_url = f"{api_url}/questions"
    submit_url = f"{api_url}/submit"

    # 1. Instantiate Agent
    try:
        # Get Hugging Face API token from environment variable
        hf_token = os.environ.get("HF_TOKEN")
        if not hf_token:
            return "Error: Please set your HF_TOKEN in .env file or environment variables.", None, update_agent_mind_display()
            
        agent = SmolAgent(hf_token=hf_token, api_url=api_url)
        print("SmolAgent initialized successfully.")
    except Exception as e:
        print(f"Error instantiating agent: {e}")
        return f"Error initializing agent: {e}", None, update_agent_mind_display()
        
    # In the case of an app running as a Hugging Face space, this link points toward your codebase
    agent_code = f"https://huggingface.co/spaces/{space_id}/tree/main"
    print(f"Agent code URL: {agent_code}")

    # 2. Fetch Questions
    print(f"Fetching questions from: {questions_url}")
    try:
        response = requests.get(questions_url, timeout=15)
        response.raise_for_status()
        questions_data = response.json()
        if not questions_data:
            print("Fetched questions list is empty.")
            return "Fetched questions list is empty or invalid format.", None, update_agent_mind_display()
        print(f"Fetched {len(questions_data)} questions.")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching questions: {e}")
        return f"Error fetching questions: {e}", None, update_agent_mind_display()
    except requests.exceptions.JSONDecodeError as e:
        print(f"Error decoding JSON response from questions endpoint: {e}")
        print(f"Response text: {response.text[:500]}")
        return f"Error decoding server response for questions: {e}", None, update_agent_mind_display()
    except Exception as e:
        print(f"An unexpected error occurred fetching questions: {e}")
        return f"An unexpected error occurred fetching questions: {e}", None, update_agent_mind_display()

    # 3. Run your Agent
    results_log = []
    answers_payload = []
    print(f"Running agent on {len(questions_data)} questions...")
    submission_stats["total"] = len(questions_data)
    
    # Load cache to avoid reprocessing questions
    cache_path = Path(CACHE_DIR) / "answers_cache.json"
    cache = {}
    if cache_path.exists():
        try:
            with open(cache_path, "r") as f:
                cache = json.load(f)
            print(f"Loaded {len(cache)} cached answers.")
        except Exception as e:
            print(f"Error loading cache: {e}")
    
    for item in questions_data:
        task_id = item.get("task_id")
        question_text = item.get("question")
        file_name = item.get("file_name")  # Get file name if present
        
        if not task_id or question_text is None:
            print(f"Skipping item with missing task_id or question: {item}")
            continue
        
        try:
            # Mark the start of a new question in the agent mind file
            append_to_agent_mind(f"## Processing Task: {task_id}")
            append_to_agent_mind(f"**Question:** {question_text}")
            if file_name:
                append_to_agent_mind(f"**File:** {file_name}")
            
            print(f"\nProcessing task: {task_id}")
            print(f"Question: {question_text[:100]}...")
            if file_name:
                print(f"Has associated file: {file_name}")
            
            # Process the question with our SmolAgent
            verbose_answer = agent(question_text, task_id=task_id, file_name=file_name)
            
            # Apply final answer processing to get concise, exact-match answers
            submitted_answer = process_final_answer(question_text, verbose_answer)
            
            # Log both the verbose and concise answers
            print(f"Verbose Answer: {verbose_answer[:100]}...")
            print(f"Final Answer: {submitted_answer}")
            append_to_agent_mind(f"**Verbose Answer:** {verbose_answer}")
            append_to_agent_mind(f"**Final Answer:** {submitted_answer}")
            
            answers_payload.append({"task_id": task_id, "submitted_answer": submitted_answer})
            results_log.append({
                "Task ID": task_id, 
                "Question": question_text, 
                "File": file_name if file_name else "None",
                "Verbose Answer": verbose_answer,
                "Submitted Answer": submitted_answer
            })
            
            append_to_agent_mind("---\n")
            
        except Exception as e:
            print(f"Error running agent on task {task_id}: {e}")
            results_log.append({"Task ID": task_id, "Question": question_text, "Submitted Answer": f"AGENT ERROR: {e}"})
            submission_stats["unknown"] += 1
            append_to_agent_mind(f"**Error:** {e}")
            append_to_agent_mind("---\n")

    if not answers_payload:
        print("Agent did not produce any answers to submit.")
        return "Agent did not produce any answers to submit.", pd.DataFrame(results_log), update_agent_mind_display()

    # 4. Prepare Submission 
    submission_data = {"username": username.strip(), "agent_code": agent_code, "answers": answers_payload}
    status_update = f"Agent finished. Submitting {len(answers_payload)} answers for user '{username}'..."
    print(status_update)

    # 5. Submit
    print(f"Submitting {len(answers_payload)} answers to: {submit_url}")
    try:
        response = requests.post(submit_url, json=submission_data, timeout=60)
        response.raise_for_status()
        result_data = response.json()
        
        # Update statistics
        if "correct_count" in result_data and "total_attempted" in result_data:
            submission_stats["correct"] = result_data.get("correct_count", 0)
            submission_stats["incorrect"] = result_data.get("total_attempted", 0) - result_data.get("correct_count", 0)
            submission_stats["unknown"] = submission_stats["total"] - result_data.get("total_attempted", 0)
        
        final_status = (
            f"Submission Successful!\n"
            f"User: {result_data.get('username')}\n"
            f"Message: {result_data.get('message', 'No message received.')}"
        )
        print("Submission successful.")
        append_to_agent_mind(f"### Submission Results:\n{final_status}\n\n")
        append_to_agent_mind(f"- Correct: {submission_stats['correct']}")
        append_to_agent_mind(f"- Incorrect: {submission_stats['incorrect']}")
        append_to_agent_mind(f"- Unknown: {submission_stats['unknown']}")
        append_to_agent_mind(f"- Total: {submission_stats['total']}")
        append_to_agent_mind("=== End of Run ===\n\n")
        
        results_df = pd.DataFrame(results_log)
        
        return final_status, results_df, update_agent_mind_display()
    except requests.exceptions.HTTPError as e:
        error_detail = f"Server responded with status {e.response.status_code}."
        try:
            error_json = e.response.json()
            error_detail += f" Detail: {error_json.get('detail', e.response.text)}"
        except requests.exceptions.JSONDecodeError:
            error_detail += f" Response: {e.response.text[:500]}"
        status_message = f"Submission Failed: {error_detail}"
        print(status_message)
        append_to_agent_mind(f"### Submission Error:\n{status_message}\n\n")
        append_to_agent_mind("=== End of Run ===\n\n")
        
        results_df = pd.DataFrame(results_log)
        
        return status_message, results_df, update_agent_mind_display()
    except requests.exceptions.Timeout:
        status_message = "Submission Failed: The request timed out."
        print(status_message)
        append_to_agent_mind(f"### Submission Error:\n{status_message}\n\n")
        append_to_agent_mind("=== End of Run ===\n\n")
        
        results_df = pd.DataFrame(results_log)
        
        return status_message, results_df, update_agent_mind_display()
    except requests.exceptions.RequestException as e:
        status_message = f"Submission Failed: Network error - {e}"
        print(status_message)
        append_to_agent_mind(f"### Submission Error:\n{status_message}\n\n")
        append_to_agent_mind("=== End of Run ===\n\n")
        
        results_df = pd.DataFrame(results_log)
        
        return status_message, results_df, update_agent_mind_display()
    except Exception as e:
        status_message = f"An unexpected error occurred during submission: {e}"
        print(status_message)
        append_to_agent_mind(f"### Submission Error:\n{status_message}\n\n")
        append_to_agent_mind("=== End of Run ===\n\n")
        
        results_df = pd.DataFrame(results_log)
        
        return status_message, results_df, update_agent_mind_display()


# --- Build Gradio Interface using Blocks ---
with gr.Blocks() as demo:
    gr.Markdown("# Hugging Face Agents Course - Final Assignment")
    gr.Markdown(
        """
        **Instructions:**

        1. Make sure to set your Hugging Face API token in the .env file
        2. Log in to your Hugging Face account using the button below
        3. Click 'Run Evaluation & Submit All Answers' to fetch questions, run the agent, and submit answers

        This agent uses the smolagents framework with specialized tools for:
        - Chess analysis
        - Image analysis
        - Data file analysis
        - Code execution
        - Web search for factual questions
        - YouTube video analysis
        - Documentation search
        
        **Latest Improvements:**
        - 🔄 Robust model loading with multiple fallbacks (Llama 3, Mistral, Claude, Gemma)
        - 🌐 Web search integration for factual questions
        - 🎬 YouTube video transcript analysis
        - 📊 Enhanced file type detection and processing
        - 🛡️ Improved error handling with automatic retries
        """
    )

    with gr.Row():
        with gr.Column():
            gr.LoginButton()
            run_button = gr.Button("Run Evaluation & Submit All Answers", variant="primary")
            clear_mind_button = gr.Button("Clear Agent Mind Log", variant="secondary")

    with gr.Tab("Results"):
        status_output = gr.Textbox(label="Run Status / Submission Result", lines=5, interactive=False)
        results_table = gr.DataFrame(label="Questions and Agent Answers", wrap=True)
    
    with gr.Tab("Agent Mind"):
        agent_mind_output = gr.Markdown(
            "Agent's thoughts will appear here during execution...",
            label="Agent's Thought Process"
        )

    run_button.click(
        fn=run_and_submit_all,
        outputs=[status_output, results_table, agent_mind_output]
    )
    
    def clear_agent_mind():
        """Clear the agent mind file and create a fresh one."""
        if os.path.exists(AGENT_MIND_FILE):
            os.remove(AGENT_MIND_FILE)
        
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        append_to_agent_mind(f"# Agent Mind Log\n\n*Cleared and restarted at: {timestamp}*\n\n")
        append_to_agent_mind("This file tracks the agent's thought process and terminal output in real time.\n\n---\n\n")
        
        return update_agent_mind_display()
    
    clear_mind_button.click(
        fn=clear_agent_mind,
        outputs=[agent_mind_output]
    )

if __name__ == "__main__":
    # Capture app startup info in agent mind
    with capture_stdout():
        print("\n" + "-"*30 + " App Starting " + "-"*30)
        
        # Add timestamp to agent mind
        start_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        append_to_agent_mind(f"# App Started at {start_time}")
        
    # Check for SPACE_HOST and SPACE_ID at startup for information
    space_host_startup = os.getenv("SPACE_HOST")
    space_id_startup = os.getenv("SPACE_ID") # Get SPACE_ID at startup

    if space_host_startup:
        print(f"✅ SPACE_HOST found: {space_host_startup}")
        print(f"   Runtime URL should be: https://{space_host_startup}.hf.space")
        append_to_agent_mind(f"SPACE_HOST: {space_host_startup}")
        append_to_agent_mind(f"Runtime URL: https://{space_host_startup}.hf.space")
    else:
        print("ℹ️  SPACE_HOST environment variable not found (running locally?).")
        append_to_agent_mind("Running locally (no SPACE_HOST found)")

    if space_id_startup: # Print repo URLs if SPACE_ID is found
        print(f"✅ SPACE_ID found: {space_id_startup}")
        print(f"   Repo URL: https://huggingface.co/spaces/{space_id_startup}")
        print(f"   Repo Tree URL: https://huggingface.co/spaces/{space_id_startup}/tree/main")
        append_to_agent_mind(f"SPACE_ID: {space_id_startup}")
        append_to_agent_mind(f"Repo URL: https://huggingface.co/spaces/{space_id_startup}")
    else:
        print("ℹ️  SPACE_ID environment variable not found (running locally?). Repo URL cannot be determined.")

    print("-"*(60 + len(" App Starting ")) + "\n")
    append_to_agent_mind("---\n\n")

    print("Launching Gradio Interface for the Final Assignment...")
    append_to_agent_mind("Gradio Interface launched")

    # Launch the application
    demo.launch(debug=True, share=False)