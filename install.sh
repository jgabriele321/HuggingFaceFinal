#!/bin/bash
# Installation script for SmolAgent implementations

echo "🚀 Setting up SmolAgent implementations..."

# Function to check if a command exists
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# Check for Python
if ! command_exists python3; then
  echo "❌ Python 3 is required but not installed. Please install Python 3 and try again."
  exit 1
fi

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
python_major=$(echo $python_version | cut -d. -f1)
python_minor=$(echo $python_version | cut -d. -f2)

if [ "$python_major" -lt 3 ] || ([ "$python_major" -eq 3 ] && [ "$python_minor" -lt 8 ]); then
  echo "❌ Python 3.8 or higher is required. You have Python $python_version."
  exit 1
fi

echo "✅ Python $python_version detected"

# Create virtual environment
echo "🔧 Creating virtual environment..."
if command_exists python3 -m venv; then
  python3 -m venv venv
  # Activate the virtual environment
  source venv/bin/activate
else
  echo "⚠️ python3-venv not installed. Using system Python."
fi

# Install required packages
echo "📦 Installing required packages..."
pip install -U pip
pip install python-dotenv requests smolagents  # Ensure python-dotenv is installed
pip install -r requirements.txt 2>/dev/null || echo "No requirements.txt found, using default packages"

# Check for environment variables
ENV_FILE_PATH="/Users/giovannigabriele/Documents/Code/HuggingFaceAgent/Final_Assignment_Template/.env"
DEFAULT_ENV_PATH=".env"

if [ -f "$ENV_FILE_PATH" ]; then
  echo "✅ .env file found at $ENV_FILE_PATH"
  ENV_FILE=$ENV_FILE_PATH
elif [ -f "$DEFAULT_ENV_PATH" ]; then
  echo "✅ .env file found at current directory"
  ENV_FILE=$DEFAULT_ENV_PATH
else
  echo "⚠️ .env file not found. Creating at $DEFAULT_ENV_PATH..."
  ENV_FILE=$DEFAULT_ENV_PATH
  
  # Create template .env file
  echo "# API Keys for SmolAgent" > $ENV_FILE
  echo "# Uncomment and add your keys below" >> $ENV_FILE
  echo "" >> $ENV_FILE
  echo "# OpenRouter API Key (get one at https://openrouter.ai/keys)" >> $ENV_FILE
  echo "# OPENROUTER_API_KEY=your_openrouter_key_here" >> $ENV_FILE
  echo "" >> $ENV_FILE
  echo "# OpenAI API Key (get one at https://platform.openai.com/api-keys)" >> $ENV_FILE
  echo "# OPENAI_API_KEY=your_openai_key_here" >> $ENV_FILE
  echo "" >> $ENV_FILE
  echo "# Which implementation to use as default (openrouter or openai)" >> $ENV_FILE
  echo "SMOL_IMPLEMENTATION=openrouter" >> $ENV_FILE
  
  echo "📝 Please edit the .env file and add your API keys."
fi

# Run the update agent script with the correct env file
echo "🔄 Setting up the agent implementation..."
python update_agent.py --env-file $ENV_FILE

echo ""
echo "🎉 Installation complete! You can now run: python test_implementations.py"
echo ""
echo "📋 Quick start guide:"
echo "1. Edit $ENV_FILE to set your API keys"
echo "2. Run 'python test_implementations.py' to test the implementations"
echo "3. To manually choose implementation, run 'python update_agent.py --env-file $ENV_FILE'"
echo "4. To fix app.py to use your implementation, run 'python fix_app.py'"
echo "5. Then run your app normally with 'python app.py'" 