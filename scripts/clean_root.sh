#!/bin/bash

# Clean Root Directory Script
# This script safely removes files that have been copied to their proper subdirectories

echo "Cleaning up root directory..."
echo "Files will only be removed if they exist in their new locations."

# Check each file before removing
check_and_remove() {
    local original_file="$1"
    local new_location="$2"
    
    if [ -f "$original_file" ] && [ -f "$new_location" ]; then
        echo "Removing $original_file (copied to $new_location)"
        rm "$original_file"
    elif [ -f "$original_file" ]; then
        echo "⚠️ Warning: Not removing $original_file (not found at $new_location)"
    fi
}

# Source code files
check_and_remove "agent.py" "src/agent.py"
check_and_remove "agent_adapter.py" "src/agent_adapter.py"
check_and_remove "concise_agent.py" "src/concise_agent.py"
check_and_remove "openai_agent.py" "src/openai_agent.py"
check_and_remove "openrouter_agent.py" "src/openrouter_agent.py"

# Backup files
check_and_remove "agent.py.bak" "src/agent.py.bak"
check_and_remove "app.py.bak" "backups/app.py.bak"

# Test files
check_and_remove "test_hf_client.py" "tests/test_hf_client.py"
check_and_remove "test_implementations.py" "tests/test_implementations.py"
check_and_remove "test_model.py" "tests/test_model.py"

# Script files
check_and_remove "direct_env_checker.py" "scripts/direct_env_checker.py"
check_and_remove "fix_app.py" "scripts/fix_app.py"
check_and_remove "install.sh" "scripts/install.sh"
check_and_remove "save_to_github.sh" "scripts/save_to_github.sh"
check_and_remove "update_agent.py" "scripts/update_agent.py"

# Documentation files
check_and_remove "MODEL_TROUBLESHOOTING.md" "docs/model_troubleshooting.md"
check_and_remove "agentmind.md" "docs/agentmind.md"
check_and_remove "reorganization_plan.md" "docs/reorganization_plan.md"
check_and_remove "reorganization_summary.md" "docs/reorganization_summary.md"

# Environment files (only after confirming they're in config/)
if [ -f "config/.env" ] && [ -f ".env" ]; then
    echo "Removing .env (copied to config/.env)"
    rm ".env"
fi

if [ -f "config/.env.template" ] && [ -f ".env.template" ]; then
    echo "Removing .env.template (copied to config/.env.template)"
    rm ".env.template" 
fi

echo "Cleanup completed!" 