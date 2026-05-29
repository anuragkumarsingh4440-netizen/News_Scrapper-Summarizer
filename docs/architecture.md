# Architecture Documentation

A multi-agent AI system that fetches news, filters it for AI/ML relevance,
summarizes it, and writes a daily newsletter. Everything runs locally.

## Design Principles
- **SOLID** throughout — see [`design-decisions.md`](design-decisions.md).
- **Design patterns** — Template Method (`BaseFetcher`, `BaseAgent`), Factory
  (`FetcherFactory`), Strategy (`RateLimitStrategy`).
- **Async-first** — all network I/O is async; sources are fetched concurrently.
- **Markdown as interchange format** — each stage reads/writes markdown, so the
  pipeline is debuggable by opening a file.

## Components

### Fetchers (M1–M2)
`HackerNewsFetcher`, `RSSFetcher`, `GitHubTrendingFetcher` all extend
`BaseFetcher`. `ArticleTransformer` maps raw data to `Article`; `MarkdownStorage`
persists. `FetchOrchestrator` runs them concurrently with rate limiting.

### Agents (M3–M4)
`BaseAgent` provides the `load → process → save` lifecycle plus LLM helpers
(`_call_llm`, `_call_llm_with_tools`) via LiteLLM.

- `NewsFilterAgent` — scores each article for AI/ML relevance, keeps those ≥ 6/10.
- `EnhancedFilterAgent` — same, but the LLM may call the `calculator` / `web_search` tools.
- `SummarizerAgent` — groups kept articles by topic and summarizes each group.
- `WriterAgent` — composes the final newsletter.

### MCP Integration (M4)
`src/mcp_servers/database_server.py` exposes the SQLite article DB as three MCP
tools (`query_articles`, `search_articles`, `get_sources`) over stdio.
`SearchSkill` is a reusable client wrapper that calls `search_articles` so agents
don't deal with MCP plumbing directly. `hello_server.py` + `simple_client.py`
are the minimal protocol demo.

### Evaluation (M5)
`FilterEvaluator` runs `NewsFilterAgent` over a 10-case hand-labeled golden
dataset and reports accuracy / precision / recall / F1.

## Data Flow
```
External APIs
   → Fetchers (async, concurrent)
   → Markdown (data/articles/) + SQLite (data/news_agent.db)
   → NewsFilterAgent          → data/context/filtered_articles.md
   → SummarizerAgent          → data/context/summary.md
   → WriterAgent              → data/output/newsletter.md
```

## Technology Choices
- **Python 3.11+** — strong async support, rich AI ecosystem.
- **LiteLLM** — one API across providers; swap models via `LITELLM_MODEL`.
- **SQLite / aiosqlite** — zero-config local persistence.
- **MCP** — standard, reusable, LLM-agnostic tool interface.
- **Markdown** — human-readable, git-friendly, easy to debug.

## Security
- API keys live in `.env` (gitignored), loaded at runtime, never logged.
- DB access uses parameterized queries (no SQL injection).
- The `calculator` tool uses a restricted AST evaluator, not `eval`.

## Known Limitations / Future Work
- `search_articles` does a Python-side substring scan; a real deployment would
  use SQL `LIKE` / FTS5.
- `web_search` is mocked.
- Golden dataset is small (10 cases); expand for stronger metrics.
