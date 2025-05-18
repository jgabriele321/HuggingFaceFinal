---
title: Hugging Face Agents Course - Final Assignment
emoji: 🕵️‍♂️
colorFrom: indigo
colorTo: indigo
sdk: gradio
sdk_version: 5.25.2
app_file: app.py
pinned: false
hf_oauth: true
# optional, default duration is 8 hours/480 minutes. Max duration is 30 days/43200 minutes.
hf_oauth_expiration_minutes: 480
---

# Hugging Face Agents Course - Final Assignment

This project implements an intelligent agent using the smolagents framework for the Hugging Face Agents Course final assignment. The agent is designed to answer a variety of questions, including those requiring analysis of images, chess positions, data files, and more.

## Setup Instructions

1. Clone this repository
2. Install dependencies with `pip install -r requirements.txt`
3. Create a `.env` file in the root directory with your Hugging Face API token:
   ```
   HF_TOKEN=your_huggingface_token_here
   API_URL=https://agents-course-unit4-scoring.hf.space
   ```
4. Run the application with `python app.py`

## Agent Features

The agent uses a modular architecture with the following components:

- **SmolAgent**: Main agent class that orchestrates the entire process
- **Specialized Tools**:
  - `analyze_image`: For general image analysis
  - `analyze_chess_position`: For chess-specific image analysis
  - `analyze_data_file`: For CSV, JSON, and text files
  - `execute_code`: For running code snippets safely
  - `search_documentation`: For retrieving relevant information
- **Question Processing**:
  - Question type detection
  - Pre-processing with context enhancement
  - Post-processing to format answers according to requirements
- **File Handling**:
  - Automatic download of question-related files
  - Organized storage in the `files` directory
- **Caching**:
  - Results are cached to avoid recomputing answers
  - Cache is maintained between runs in the `cache` directory

## How It Works

1. The app fetches questions from the API endpoint
2. For each question, it detects the question type and downloads any associated files
3. It then processes the question with the appropriate tools
4. The answer is formatted according to the question type and cached
5. All answers are submitted back to the API for scoring

## Contributing

Feel free to contribute to this project by submitting pull requests or opening issues.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

Check out the configuration reference at https://huggingface.co/docs/hub/spaces-config-reference