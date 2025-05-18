import os
import gradio as gr
import requests
import inspect
import pandas as pd
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import the SmolAgent class
from agent import SmolAgent

# --- Constants ---
DEFAULT_API_URL = "https://agents-course-unit4-scoring.hf.space"
FILES_DIR = "files"
CACHE_DIR = "cache"

# Ensure directories exist
os.makedirs(FILES_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)

def run_agent_locally():
    """
    Run the agent locally without submission - for testing purposes
    """
    print("Running agent locally for testing...")
    
    try:
        # Use mock model for local testing
        agent = SmolAgent(use_mock=True)
        print("SmolAgent initialized successfully with mock model.")
    except Exception as e:
        print(f"Error instantiating agent: {e}")
        return f"Error initializing agent: {e}"
    
    # Test question
    test_question = "What is 2 + 2?"
    print(f"Testing agent with question: {test_question}")
    
    try:
        answer = agent(test_question)
        return f"Agent test successful! Answer: {answer}"
    except Exception as e:
        print(f"Error running agent: {e}")
        return f"Error running agent: {e}"

def run_local_demo():
    """
    Simplified version for local testing - doesn't require HF login
    """
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
            answer = agent(q["question"])
            results.append({
                "Task ID": q["id"],
                "Question": q["question"],
                "Type": q["type"],
                "Answer": answer
            })
        
        return "Local test successful! Processed 3 test questions.", pd.DataFrame(results)
    except Exception as e:
        print(f"Error in local demo: {e}")
        return f"Error in local demo: {e}", None

def run_and_submit_all(profile: gr.OAuthProfile | None):
    """
    Fetches all questions, runs the SmolAgent on them, submits all answers,
    and displays the results.
    """
    # --- Determine HF Space Runtime URL and Repo URL ---
    space_id = os.getenv("SPACE_ID") # Get the SPACE_ID for sending link to the code

    if profile:
        username = f"{profile.username}"
        print(f"User logged in: {username}")
    else:
        print("User not logged in.")
        return "Please Login to Hugging Face with the button.", None

    api_url = DEFAULT_API_URL
    questions_url = f"{api_url}/questions"
    submit_url = f"{api_url}/submit"

    # 1. Instantiate Agent
    try:
        # Get Hugging Face API token from environment variable
        hf_token = os.environ.get("HF_TOKEN")
        if not hf_token:
            return "Error: Please set your HF_TOKEN in .env file or environment variables.", None
            
        agent = SmolAgent(hf_token=hf_token, api_url=api_url)
        print("SmolAgent initialized successfully.")
    except Exception as e:
        print(f"Error instantiating agent: {e}")
        return f"Error initializing agent: {e}", None
        
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
             return "Fetched questions list is empty or invalid format.", None
        print(f"Fetched {len(questions_data)} questions.")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching questions: {e}")
        return f"Error fetching questions: {e}", None
    except requests.exceptions.JSONDecodeError as e:
         print(f"Error decoding JSON response from questions endpoint: {e}")
         print(f"Response text: {response.text[:500]}")
         return f"Error decoding server response for questions: {e}", None
    except Exception as e:
        print(f"An unexpected error occurred fetching questions: {e}")
        return f"An unexpected error occurred fetching questions: {e}", None

    # 3. Run your Agent
    results_log = []
    answers_payload = []
    print(f"Running agent on {len(questions_data)} questions...")
    
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
            print(f"\nProcessing task: {task_id}")
            print(f"Question: {question_text[:100]}...")
            if file_name:
                print(f"Has associated file: {file_name}")
            
            # Process the question with our SmolAgent
            submitted_answer = agent(question_text, task_id=task_id, file_name=file_name)
            
            answers_payload.append({"task_id": task_id, "submitted_answer": submitted_answer})
            results_log.append({
                "Task ID": task_id, 
                "Question": question_text, 
                "File": file_name if file_name else "None",
                "Submitted Answer": submitted_answer
            })
            
            print(f"Answer: {submitted_answer}")
            
        except Exception as e:
             print(f"Error running agent on task {task_id}: {e}")
             results_log.append({"Task ID": task_id, "Question": question_text, "Submitted Answer": f"AGENT ERROR: {e}"})

    if not answers_payload:
        print("Agent did not produce any answers to submit.")
        return "Agent did not produce any answers to submit.", pd.DataFrame(results_log)

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
        final_status = (
            f"Submission Successful!\n"
            f"User: {result_data.get('username')}\n"
            f"Overall Score: {result_data.get('score', 'N/A')}% "
            f"({result_data.get('correct_count', '?')}/{result_data.get('total_attempted', '?')} correct)\n"
            f"Message: {result_data.get('message', 'No message received.')}"
        )
        print("Submission successful.")
        results_df = pd.DataFrame(results_log)
        return final_status, results_df
    except requests.exceptions.HTTPError as e:
        error_detail = f"Server responded with status {e.response.status_code}."
        try:
            error_json = e.response.json()
            error_detail += f" Detail: {error_json.get('detail', e.response.text)}"
        except requests.exceptions.JSONDecodeError:
            error_detail += f" Response: {e.response.text[:500]}"
        status_message = f"Submission Failed: {error_detail}"
        print(status_message)
        results_df = pd.DataFrame(results_log)
        return status_message, results_df
    except requests.exceptions.Timeout:
        status_message = "Submission Failed: The request timed out."
        print(status_message)
        results_df = pd.DataFrame(results_log)
        return status_message, results_df
    except requests.exceptions.RequestException as e:
        status_message = f"Submission Failed: Network error - {e}"
        print(status_message)
        results_df = pd.DataFrame(results_log)
        return status_message, results_df
    except Exception as e:
        status_message = f"An unexpected error occurred during submission: {e}"
        print(status_message)
        results_df = pd.DataFrame(results_log)
        return status_message, results_df


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
        - Documentation search
        
        The agent includes caching to save results between runs.
        """
    )

    gr.LoginButton()
    run_button = gr.Button("Run Evaluation & Submit All Answers")

    status_output = gr.Textbox(label="Run Status / Submission Result", lines=5, interactive=False)
    results_table = gr.DataFrame(label="Questions and Agent Answers", wrap=True)

    run_button.click(
        fn=run_and_submit_all,
        outputs=[status_output, results_table]
    )

if __name__ == "__main__":
    print("\n" + "-"*30 + " App Starting " + "-"*30)
    # Check for SPACE_HOST and SPACE_ID at startup for information
    space_host_startup = os.getenv("SPACE_HOST")
    space_id_startup = os.getenv("SPACE_ID") # Get SPACE_ID at startup

    if space_host_startup:
        print(f"✅ SPACE_HOST found: {space_host_startup}")
        print(f"   Runtime URL should be: https://{space_host_startup}.hf.space")
    else:
        print("ℹ️  SPACE_HOST environment variable not found (running locally?).")

    if space_id_startup: # Print repo URLs if SPACE_ID is found
        print(f"✅ SPACE_ID found: {space_id_startup}")
        print(f"   Repo URL: https://huggingface.co/spaces/{space_id_startup}")
        print(f"   Repo Tree URL: https://huggingface.co/spaces/{space_id_startup}/tree/main")
    else:
        print("ℹ️  SPACE_ID environment variable not found (running locally?). Repo URL cannot be determined.")

    print("-"*(60 + len(" App Starting ")) + "\n")

    print("Launching Gradio Interface for the Final Assignment...")
    demo.launch(debug=True, share=False)