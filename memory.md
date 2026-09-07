# Agent Memory

This file serves as a persistent memory of the current task, recent actions, and context, so that if the agent's execution is cancelled or restarted, the context is not lost.

## Project: SIH2026PROJECTEMS
- **Repo**: https://github.com/aman2413226-dotcom/SIH2026PROJECTEMS.git
- **Branches**: `main`, `sangambranch`

## CRITICAL RULES
- **NEVER create `node_modules/`, `.next/`, or `__pycache__/`** — these are auto-generated and must not be created or committed by the agent.

## Session: 2026-09-08

### Problem Solved: GitHub push rejected due to large files
- `frontend/node_modules/` was committed to git history (129 MB file exceeded GitHub's 100 MB limit).
- `.next/` build cache and `__pycache__/` were also tracked.

### Fix Applied
1. Updated `.gitignore` to exclude: `node_modules/`, `.next/`, `__pycache__/`, `*.pyc`, `venv/`, `.env`, etc.
2. On `sangambranch`: squashed unpushed commits into one clean commit, pushed successfully.
3. On `main`: soft-reset unpushed commits, removed cached `node_modules/.next/__pycache__`, recommitted clean, pushed successfully.
4. Deleted `node_modules/`, `.next/`, and all `__pycache__/` folders from disk.

### Current State
- Both `main` and `sangambranch` are pushed to origin successfully.
- `.gitignore` is properly configured on both branches.
- Generated folders have been deleted from disk.

## Next Steps
- [To be filled based on user's next request]
