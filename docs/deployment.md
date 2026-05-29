# Deployment Guide

This project is designed to run locally — no cloud required.

## Requirements
- macOS, Linux, or Windows
- Python 3.11+
- One LLM provider API key (Anthropic / OpenAI / Gemini / any LiteLLM provider)

## Setup
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env        # then edit and add your key
python scripts/verify_setup.py
```

## Running
```bash
# Fetch only (Milestones 1–2)
python -m src.main

# Fetch + filter (Milestone 3)
python -m src.pipeline

# Full pipeline: fetch → db → filter → summarize → write (Milestone 4)
python -m src.complete_pipeline

# Populate the database from saved markdown
python scripts/populate_db.py

# Evaluate the filter agent (Milestone 5)
python -m src.evaluation.evaluator
```

Outputs:
- `data/articles/all_articles.md` — fetched articles
- `data/context/filtered_articles.md`, `summary.md` — intermediate agent output
- `data/output/newsletter.md` — final newsletter
- `data/news_agent.db` — SQLite database
- `data/evaluation/evaluation_report.md` — metrics

## Scheduling
**macOS/Linux (cron):**
```bash
0 9 * * * cd /path/to/project && /path/to/venv/bin/python -m src.complete_pipeline
```
**Windows (Task Scheduler):** create a daily task running
`venv\Scripts\python.exe` with argument `-m src.complete_pipeline` and "Start in"
set to the project directory.

## Configuration (env vars)
- `LITELLM_MODEL` — required, e.g. `claude-haiku-4-5-20251001` or `gemini/gemini-2.5-flash-lite`
- `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` / `GEMINI_API_KEY` — one, matching the model
- `ENVIRONMENT`, `LOG_LEVEL` — optional

## Tests
```bash
pytest                    # fast unit tests (no network/LLM)
pytest -m integration     # live network + MCP server tests
pytest -m llm             # live LLM call (needs an API key)
pytest --cov=src          # with coverage
```

## Troubleshooting
- **LLM errors** — check the key matches `LITELLM_MODEL`; verify with
  `python scripts/verify_setup.py`.
- **Empty fetch results** — public APIs occasionally rate-limit; rerun.
- **DB inspection** — `sqlite3 data/news_agent.db "SELECT COUNT(*) FROM articles;"`
