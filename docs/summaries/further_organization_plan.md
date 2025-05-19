# Further Repository Organization Plan

## Files to Move or Clean Up

### Create a `config/` directory
- Move `.env` → `config/.env`
- Move `.env.template` → `config/.env.template`
- Keep `.gitattributes` and `.gitignore` in root (git expects them there)

### Move remaining agent files to `src/`
- Move `agent.py` → already copied to `src/`, can delete from root
- Move `agent.py.bak` → `src/agent.py.bak`
- Move `agent_adapter.py` → already copied to `src/`, can delete from root
- Move `concise_agent.py` → already copied to `src/`, can delete from root
- Move `openai_agent.py` → already copied to `src/`, can delete from root
- Move `openrouter_agent.py` → already copied to `src/`, can delete from root

### Move backup files to `backups/` directory
- Create a new `backups/` directory
- Move `app.py.bak` → `backups/app.py.bak`

### Move tests to `tests/` directory
- Move `test_hf_client.py` → already copied to `tests/`, can delete from root
- Move `test_implementations.py` → already copied to `tests/`, can delete from root 
- Move `test_model.py` → already copied to `tests/`, can delete from root

### Move scripts to `scripts/` directory
- Move `direct_env_checker.py` → already copied to `scripts/`, can delete from root
- Move `fix_app.py` → already copied to `scripts/`, can delete from root
- Move `install.sh` → already copied to `scripts/`, can delete from root
- Move `save_to_github.sh` → already copied to `scripts/`, can delete from root
- Move `update_agent.py` → already copied to `scripts/`, can delete from root

### Move documentation to `docs/` directory
- Move `MODEL_TROUBLESHOOTING.md` → already copied to `docs/`, can delete from root
- Move `agentmind.md` → already copied to `docs/`, can delete from root
- Move `reorganization_plan.md` → `docs/reorganization_plan.md`
- Move `reorganization_summary.md` → `docs/reorganization_summary.md`

### Keep in root directory
- `README.md` (standard location)
- `requirements.txt` (standard location)
- `app.py` (main entry point)
- `run_tests.sh` (convenience script)

## Update File References

- Update any scripts that might still reference files in the root directory
- Update README to reference the new file locations
- Ensure app.py correctly references config/.env 