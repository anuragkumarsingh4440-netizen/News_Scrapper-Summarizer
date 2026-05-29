"""AI Upskill Project — reference implementation.

    models/         Article and other data classes (M1)
    transformers/   Raw source data → Article (M2, SRP)
    fetchers/       News source fetchers (M1, extended in M2)
    factories/      FetcherFactory (M2, Factory pattern)
    strategies/     Rate-limit strategies (M2, Strategy pattern)
    storage/        Markdown + SQLite storage (M1, M4)
    agents/         AI agents — Filter, Summarizer, Writer (M3, M4)
    tools/          LLM-callable tools — calculator, web_search (M3)
    database/       Async SQLite manager (M4)
    mcp_servers/    MCP server(s) — Database (M4)
    skills/         Reusable agent skills, e.g. SearchSkill (M4)
    orchestration/  Pipeline glue (M1 onwards)
    evaluation/     Filter agent evaluation + metrics (M5)
"""

from __future__ import annotations

# The pipeline prints emoji status lines. On Windows the default console code
# page (cp1252) can't encode them and raises UnicodeEncodeError. Reconfigure the
# standard streams to UTF-8 (with a safe fallback) so every entry point runs in
# a plain console. This is a no-op where UTF-8 is already in effect.
import sys as _sys

for _stream in (_sys.stdout, _sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):  # not a reconfigurable TextIO
        pass
