# AI Usage Log

## 2026-10-08 — Project setup
- Tool: Claude
- Prompt: Help choosing a project idea and setting up a basic Flask app that meets the container contract
- Disposition: Modified — picked the cafe passport idea and renamed paths/defaults for my project
- How it works: app.py reads PORT and DATA_DIR from environment variables with defaults, creates the data folder if missing, and runs Flask on 0.0.0.0 so it's reachable inside a container. /health returns a simple JSON status.