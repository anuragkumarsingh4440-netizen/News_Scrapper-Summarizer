# Design Decisions — SOLID Refactoring (Milestone 2)

This document records how the codebase applies the five SOLID principles and
three design patterns. It is the deliverable for Milestone 2 and the reference
for how the rest of the system is structured.

## SOLID Principles

### 1. Single Responsibility Principle
Each class has exactly one reason to change:

| Class | Sole responsibility |
|-------|---------------------|
| `ArticleTransformer` | Map raw source data → `Article` |
| `MarkdownStorage` | Write articles to markdown files |
| `HackerNewsFetcher` / `RSSFetcher` / `GitHubTrendingFetcher` | Fetch from one source |
| `FetchOrchestrator` | Coordinate fetchers concurrently |

A change to the file format touches only `MarkdownStorage`; a change to HN's API
touches only `HackerNewsFetcher`.

### 2. Open/Closed Principle
`BaseFetcher` defines the contract. `GitHubTrendingFetcher` was added as a brand
new source **without editing** `hackernews_fetcher.py`, `rss_fetcher.py`,
`base_fetcher.py`, `article_transformer.py`, or `markdown_storage.py`. New
sources extend; existing code stays closed for modification.

### 3. Liskov Substitution Principle
Every fetcher returns `list[Article]` (empty on failure, never `None`, never an
uncaught exception). `tests/test_substitutability.py` proves any fetcher can be
used wherever a `BaseFetcher` is expected.

### 4. Interface Segregation Principle
`BaseFetcher` exposes only the three methods every fetcher needs
(`fetch_articles`, `get_source_name`, `fetch_and_save`). Capabilities only some
sources need — authentication, pagination — live in separate optional
interfaces in `src/fetchers/interfaces.py`, so no fetcher implements methods it
doesn't use.

### 5. Dependency Inversion Principle
`FetchOrchestrator` depends on the abstractions `BaseFetcher` and
`ArticleStorage`, injected through its constructor. Tests drive it entirely with
mocks (`tests/test_orchestrator.py`) — no real HTTP or file I/O.

## Design Patterns

### Template Method — `BaseFetcher.fetch_and_save` / `BaseAgent.execute`
The base class fixes the algorithm skeleton (fetch → save; load → process →
save) and subclasses fill in the variable steps.

### Factory — `FetcherFactory`
Creates fetchers from a string identifier and supports `register()` so new types
can be added without editing the factory (OCP again).

### Strategy — `RateLimitStrategy`
`SemaphoreStrategy` (cap concurrency) and `TokenBucketStrategy` (cap average
rate) are interchangeable. A fetcher accepts whichever strategy it's given.

## Trade-offs
- **More classes / files** — but each is small and focused.
- **More abstraction** — slightly higher upfront complexity, much lower cost to
  extend and test.
- **Dependency injection** — more wiring in `main.py`, far easier mocking.
