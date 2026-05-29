# AI Upskill Project

**Blend's AI engineering onboarding curriculum.** A 5-week self-paced project
that takes engineers from async Python through agents, MCP, and evaluation
by building a small AI-powered news pipeline end-to-end.

- **Time commitment:** 1–2 hours per evening, ~5 weeks (38–54 hours total)
- **Format:** Self-paced. Each milestone ends with a PR checkpoint reviewed by two peers.
- **Outcome:** A working multi-agent news pipeline with tests, evaluation, and docs.

> **✅ Reference implementation complete.** All five milestones (M1–M5) are
> implemented in `src/`, with tests in `tests/`. Run the full pipeline with
> `python -m src.complete_pipeline`. See [`docs/architecture.md`](docs/architecture.md),
> [`docs/design-decisions.md`](docs/design-decisions.md), and
> [`docs/deployment.md`](docs/deployment.md). Quick commands are in
> [Running the pipeline](#running-the-pipeline) below.

---

## Where to start

1. Read [`docs/architecture/overview.md`](docs/architecture/overview.md) for the 20-min big-picture orientation.
2. Open [`docs/milestones/milestone-0-setup.md`](docs/milestones/milestone-0-setup.md) and follow it. It will get you to a working dev environment in one evening.
3. From there, milestones link to the next one in sequence.

---

## The 5-week arc

| Week | Milestone | What you build | Hours |
|------|-----------|----------------|-------|
| 0 (Evening 1) | [M0 — Setup](docs/milestones/milestone-0-setup.md) | Dev environment, API key, verify script passes | 1–2 |
| 1 | [M1 — Async News Fetcher](docs/milestones/milestone-1-async-fetcher.md) | Hacker News + RSS fetchers, orchestrator, rate limiting, tests | 6–8 |
| 2 | [M2 — SOLID Refactoring](docs/milestones/milestone-2-solid-refactoring.md) | All five SOLID principles applied; add GitHub Trending with zero edits to existing code | 8–10 |
| 3 | [M3 — First Agent](docs/milestones/milestone-3-first-agent.md) | `NewsFilterAgent` via LiteLLM, prompt engineering, function calling | 8–10 |
| 4 | [M4 — MCP Pipeline](docs/milestones/milestone-4-mcp-pipeline.md) | Database MCP server, three-agent pipeline (Filter → Summarize → Write) | 10–14 |
| 5 | [M5 — Evaluation](docs/milestones/milestone-5-evaluation.md) | Golden dataset, accuracy/precision/recall/F1, project docs | 4–6 |

Full curriculum overview lives in [`docs/curriculum/overview.md`](docs/curriculum/overview.md).

---

## Tech stack

- **Python 3.11+** with async/await throughout
- **`aiohttp`** for concurrent HTTP, **`feedparser`** for RSS
- **LiteLLM** as the LLM provider abstraction — default model is `claude-haiku-4-5-20251001`, swap to any [LiteLLM-supported provider](https://docs.litellm.ai/docs/providers) by changing one env var
- **MCP (Model Context Protocol)** for tool integration in Milestone 4
- **SQLite** for the database server in Milestone 4
- **pytest + pytest-asyncio** for tests
- **ruff** for formatting and linting

---

## Quickstart

```bash
git clone https://github.com/BLEND360/AIUpskillProject.git
cd AIUpskillProject

python3.11 -m venv venv
source venv/bin/activate          # macOS/Linux
# venv\Scripts\activate            # Windows

pip install --upgrade pip
pip install -r requirements.txt

cp .env.example .env               # then paste your API key
python scripts/verify_setup.py    # should print all ✅
```

Then open [`docs/milestones/milestone-0-setup.md`](docs/milestones/milestone-0-setup.md).

---

## Web UI (Streamlit)

A browser UI drives the whole pipeline — fetch, filter, summarize, write,
MCP search, and evaluation:

```bash
streamlit run app.py
```

Then open http://localhost:8501. Configure sources, the LLM filter budget, and
run any stage from the tabs.

## Running the pipeline (CLI)

```bash
python -m src.main                  # M1–M2: fetch from all sources → markdown
python -m src.pipeline              # M3: fetch + AI relevance filter
python -m src.complete_pipeline     # M4: fetch → DB → filter → summarize → newsletter
python scripts/populate_db.py       # load saved markdown into SQLite
python -m src.evaluation.evaluator  # M5: score the filter on the golden dataset

pytest                              # fast unit tests (no network / no LLM)
pytest -m integration               # live network + MCP server tests
pytest -m llm                       # live LLM call (needs an API key)
pytest --cov=src                    # with coverage
```

---

## Repository layout

```
AIUpskillProject/
├── README.md                  ← you are here
├── requirements.txt
├── pyproject.toml             # pytest + ruff + coverage config
├── .env.example
├── scripts/
│   ├── verify_setup.py        # M0 Task 5 runs this
│   └── populate_db.py         # markdown → SQLite
├── src/
│   ├── models/                # Article dataclass
│   ├── transformers/          # raw data → Article (SRP)
│   ├── storage/               # ArticleStorage interface + markdown impl
│   ├── fetchers/              # BaseFetcher + HN / RSS / GitHub Trending
│   ├── factories/             # FetcherFactory (Factory pattern)
│   ├── strategies/            # rate-limit strategies (Strategy pattern)
│   ├── utils/                 # RateLimiter
│   ├── orchestration/         # FetchOrchestrator (DI)
│   ├── agents/                # BaseAgent + Filter / Summarizer / Writer
│   ├── tools/                 # calculator, web_search (function calling)
│   ├── database/              # async SQLite DatabaseManager
│   ├── mcp_servers/           # hello + database MCP servers, client
│   ├── skills/                # SearchSkill (MCP client wrapper)
│   ├── evaluation/            # FilterEvaluator (metrics)
│   ├── main.py                # M1–M2 entry point
│   ├── pipeline.py            # M3 fetch + filter
│   └── complete_pipeline.py   # M4 full multi-agent pipeline
├── tests/                     # unit + (marked) integration / llm tests
├── data/                      # created at runtime; golden_dataset.json shipped
└── docs/
    ├── architecture.md        # implementation architecture (M5)
    ├── design-decisions.md    # SOLID + patterns writeup (M2)
    ├── deployment.md          # run / schedule / configure (M5)
    ├── architecture/overview.md
    ├── milestones/            # M0 → M5
    └── curriculum/            # high-level curriculum docs
```

---

## How checkpoints work

Each milestone ends with a PR you open against your fork of this repo. Two
reviewers approve before you move on. PR templates and review criteria live
inside the relevant milestone doc.

---

## Questions

Ask in Slack: `#ai-upskill-cohort-[X]`
