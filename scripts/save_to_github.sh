#!/bin/bash
# Script to save the SmolAgent implementation to GitHub

echo "📦 Saving SmolAgent implementation to GitHub..."

# Create .gitignore if it doesn't exist
if [ ! -f .gitignore ]; then
  echo "Creating .gitignore file..."
  cat > .gitignore << EOF
# Python artifacts
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
env/
ENV/

# IDE files
.idea/
.vscode/
*.swp
*.swo

# Environment variables
.env
.env.local

# Cache and logs
cache/
logs/

# Backup files
*.bak
EOF
  echo "✅ .gitignore created"
fi

# Ensure we're not adding sensitive files
echo "🔒 Ensuring no sensitive files are committed..."
if [ -f .env ]; then
  cp .env .env.template
  # Remove any values from the template
  sed -i '' 's/\(^[A-Za-z0-9_]*=\).*/\1your_key_here/g' .env.template
  echo "✅ Created sanitized .env.template file"
fi

# Stage the important files
echo "📋 Staging important files..."
git add agent_adapter.py openrouter_agent.py openai_agent.py update_agent.py fix_app.py install.sh test_implementations.py direct_env_checker.py requirements.txt .env.template README.md .gitignore save_to_github.sh

# Check if agent.py is modified and add it
if git status --porcelain | grep "M agent.py"; then
  git add agent.py
  echo "✅ Added modified agent.py"
fi

# Check if app.py is modified and add it
if git status --porcelain | grep "M app.py"; then
  git add app.py
  echo "✅ Added modified app.py"
fi

# Commit the changes
echo "💾 Committing changes..."
git commit -m "Add reliable SmolAgent implementation with OpenRouter and OpenAI fallbacks"

# Ask user for GitHub repository URL
read -p "Enter GitHub repository URL (or press Enter to skip push): " github_url

if [ -n "$github_url" ]; then
  # Extract the repository name from the URL
  repo_name=$(echo "$github_url" | sed -E 's/.*github.com\/([^\/]+\/[^\/]+)(\.git)?$/\1/')
  
  # Check if remote already exists
  if git remote | grep -q "github"; then
    echo "Remote 'github' already exists. Updating URL..."
    git remote set-url github "$github_url"
  else
    echo "Adding remote 'github'..."
    git remote add github "$github_url"
  fi
  
  # Push to GitHub
  echo "🚀 Pushing to GitHub..."
  git push github main || git push github master
  
  echo "✅ Successfully pushed to $github_url"
else
  echo "⏭️ Skipping push to GitHub"
  echo "To push later, run: git push <remote> <branch>"
fi

echo "✅ All done!" 