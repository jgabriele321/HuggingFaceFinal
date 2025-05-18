# Repository Reorganization Plan

## Directory Structure

- `src/`: Main source code
  - Core agent implementations
  - Adapter files
  - Utility classes

- `tests/`: All test files
  - Test scripts for different implementations
  - Model testing utilities

- `scripts/`: Helper scripts
  - Installation scripts
  - Environment setup
  - Maintenance utilities

- `docs/`: Documentation
  - Markdown documentation files
  - Troubleshooting guides

## File Movements

### src/
- `openrouter_agent.py` → `src/openrouter_agent.py`
- `openai_agent.py` → `src/openai_agent.py`
- `concise_agent.py` → `src/concise_agent.py`
- `agent_adapter.py` → `src/agent_adapter.py`
- `agent.py` → `src/agent.py` (current active implementation)

### tests/
- `test_implementations.py` → `tests/test_implementations.py`
- `test_hf_client.py` → `tests/test_hf_client.py`
- `test_model.py` → `tests/test_model.py`

### scripts/
- `update_agent.py` → `scripts/update_agent.py`
- `fix_app.py` → `scripts/fix_app.py`
- `save_to_github.sh` → `scripts/save_to_github.sh`
- `install.sh` → `scripts/install.sh`
- `direct_env_checker.py` → `scripts/direct_env_checker.py`

### docs/
- `MODEL_TROUBLESHOOTING.md` → `docs/model_troubleshooting.md`
- `agentmind.md` → `docs/agentmind.md`

### Root directory (keep in root)
- `app.py` (main application)
- `README.md`
- `requirements.txt`
- `.gitignore`
- `.gitattributes`

## Adjustments Required

After moving files, update import paths in:
- `app.py` to reference files in the src/ directory
- Update scripts to use correct paths
- Modify tests to import from src/ 