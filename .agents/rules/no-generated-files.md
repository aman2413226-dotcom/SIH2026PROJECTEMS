# Project Rules

## NEVER generate these folders/files:
- `node_modules/` — Do NOT run `npm install` or any command that creates this folder.
- `.next/` — Do NOT run `npm run dev`, `npm run build`, or `next build` that creates this folder.
- `__pycache__/` / `*.pyc` / `*.pyo` — Do NOT run Python scripts that create bytecode cache.

The agent must NEVER execute commands that produce these directories. 
If the user needs to run these commands, instruct them to do it manually.
