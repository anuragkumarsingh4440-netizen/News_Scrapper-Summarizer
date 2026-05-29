"""Streamlit UI for the News Scraper & Summarizer pipeline.

Drives the full multi-agent pipeline (fetch → filter → summarize → write),
the MCP-backed search, and the filter evaluation — all from the browser.

Run with:
    streamlit run app.py
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from src import service

load_dotenv()

st.set_page_config(
    page_title="News Scraper & Summarizer",
    page_icon="📰",
    layout="wide",
)


def run_async(coro):
    """Run an async coroutine from Streamlit's synchronous script context."""
    return asyncio.run(coro)


def guard(coro):
    """Run an LLM/pipeline coroutine, turning failures into friendly UI errors.

    Returns the result, or None if it failed (and shows an st.error explaining
    what happened — rate limits get a tailored message).
    """
    try:
        return run_async(coro)
    except Exception as exc:  # noqa: BLE001 - surface any failure to the user
        msg = str(exc)
        is_rate_limit = (
            "RateLimit" in type(exc).__name__
            or "429" in msg
            or "RESOURCE_EXHAUSTED" in msg
            or "quota" in msg.lower()
        )
        if is_rate_limit:
            st.error(
                "⛔ **LLM rate limit / quota hit.** The provider is throttling or "
                "you've exhausted your quota.\n\n"
                "**Fixes:** lower *Max articles to filter* in the sidebar, wait for "
                "the quota window to reset, or switch the **Model** in the sidebar "
                "to another provider you have a key for (e.g. "
                "`claude-haiku-4-5-20251001` or `gpt-4o-mini`).\n\n"
                "_Google's Gemini free tier allows only ~20 requests/day._"
            )
        else:
            st.error(f"Pipeline error: {msg[:800]}")
        with st.expander("Technical details"):
            st.code(msg)
        return None


def key_for_model(model: str) -> str:
    """Map a LiteLLM model string to the provider env var it needs."""
    ml = model.lower()
    if "gemini" in ml:
        return "GEMINI_API_KEY"
    if "claude" in ml or "anthropic" in ml:
        return "ANTHROPIC_API_KEY"
    if "gpt" in ml or "openai" in ml or ml.startswith("o1"):
        return "OPENAI_API_KEY"
    return ""


def provider_key_status(model: str) -> tuple[bool, str]:
    """Check whether the key the *current model* needs is configured."""
    needed = key_for_model(model)
    candidates = (
        [needed] if needed else ["ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY"]
    )
    for key in candidates:
        val = os.getenv(key)
        if val and not val.endswith("your_key_here"):
            return True, key
    return False, needed or "ANTHROPIC_API_KEY/OPENAI_API_KEY/GEMINI_API_KEY"


# --- Session state -----------------------------------------------------------
for k in ("articles", "filtered", "summary", "newsletter", "search", "evaluation"):
    st.session_state.setdefault(k, None)

# --- Sidebar -----------------------------------------------------------------
st.sidebar.title("⚙️ Configuration")

model = st.sidebar.text_input(
    "Model (LiteLLM string)",
    value=os.getenv("LITELLM_MODEL", ""),
    help=(
        "Switch providers here without editing .env, e.g. "
        "`claude-haiku-4-5-20251001`, `gpt-4o-mini`, or `gemini/gemini-2.5-flash-lite`. "
        "The matching API key must be set in .env."
    ),
).strip()

has_key, key_name = provider_key_status(model)
if has_key:
    st.sidebar.success(f"Using `{key_name}` for this model")
else:
    st.sidebar.error(f"No `{key_name}` found in .env for model `{model or 'not set'}`.")

st.sidebar.divider()
sources = st.sidebar.multiselect(
    "Sources to fetch",
    ["HackerNews", "RSS", "GitHub Trending"],
    default=["HackerNews", "RSS", "GitHub Trending"],
)
hn_limit = st.sidebar.slider("HackerNews stories", 5, 50, 15, step=5)
rss_feed = st.sidebar.text_input("RSS feed URL", "https://hnrss.org/frontpage")
max_filter = st.sidebar.slider(
    "Max articles to send to the LLM filter",
    1,
    40,
    5,
    help=(
        "Each article is one LLM call. Keep this small on free tiers — "
        "Gemini's free tier allows only ~20 requests/day."
    ),
)

# --- Header ------------------------------------------------------------------
st.title("📰 News Scraper & Summarizer")
st.caption(
    "Async fetch → AI relevance filter → topic summary → newsletter. "
    "Built on a SOLID, MCP-powered multi-agent pipeline."
)

tab_fetch, tab_filter, tab_write, tab_full, tab_search, tab_eval, tab_about = st.tabs(
    [
        "1 · Fetch",
        "2 · Filter",
        "3 · Summarize & Write",
        "🚀 Full pipeline",
        "🔎 Search (MCP)",
        "📊 Evaluation",
        "ℹ️ About",
    ]
)

# --- Tab: Fetch --------------------------------------------------------------
with tab_fetch:
    st.subheader("Fetch articles")
    st.write(
        "Pulls from the selected sources concurrently and saves to markdown + SQLite."
    )
    if st.button("Fetch now", type="primary", key="btn_fetch"):
        if not sources:
            st.warning("Select at least one source in the sidebar.")
        else:
            with st.spinner("Fetching from sources..."):
                articles = guard(
                    service.fetch_articles(sources, hn_limit=hn_limit, rss_feed=rss_feed)
                )
            if articles is not None:
                st.session_state.articles = articles
                st.success(
                    f"Fetched {len(articles)} articles (also saved to the database)."
                )

    if st.session_state.articles:
        rows = [service.article_to_row(a) for a in st.session_state.articles]
        st.metric("Total fetched", len(rows))
        st.dataframe(
            rows,
            use_container_width=True,
            column_config={"url": st.column_config.LinkColumn("url")},
            hide_index=True,
        )
    else:
        st.info("No articles fetched yet.")

# --- Tab: Filter -------------------------------------------------------------
with tab_filter:
    st.subheader("AI/ML relevance filter")
    st.write("The NewsFilterAgent scores each article 1–10 and keeps those ≥ 6.")
    if st.button("Run filter", type="primary", key="btn_filter"):
        if not st.session_state.articles:
            st.warning("Fetch some articles first (tab 1).")
        elif not has_key:
            st.error("No API key configured.")
        else:
            with st.spinner(f"Filtering up to {max_filter} articles with the LLM..."):
                result = guard(
                    service.filter_articles(
                        st.session_state.articles, max_filter, model=model or None
                    )
                )
            if result is not None:
                st.session_state.filtered = result
                st.success(f"Kept {result['kept']} of {result['considered']} articles.")

    if st.session_state.filtered:
        res = st.session_state.filtered
        c1, c2 = st.columns(2)
        c1.metric("Considered", res["considered"])
        c2.metric("Kept (relevant)", res["kept"])
        for a in res["articles"]:
            with st.expander(f"⭐ {a['score']}/10 — {a['title']}"):
                st.write(f"**Reasoning:** {a['reasoning']}")
                st.write(f"**Key topics:** {a['topics']}")
                if a["url"]:
                    st.write(f"[Open article]({a['url']})")
    else:
        st.info("No filtered results yet.")

# --- Tab: Summarize & Write --------------------------------------------------
with tab_write:
    st.subheader("Summarize & write the newsletter")
    col_a, col_b = st.columns(2)

    with col_a:
        if st.button("Summarize", key="btn_summarize"):
            if not st.session_state.filtered:
                st.warning("Run the filter first (tab 2).")
            elif not has_key:
                st.error("No API key configured.")
            else:
                with st.spinner("Summarizing by topic..."):
                    summary = guard(service.summarize(model=model or None))
                if summary is not None:
                    st.session_state.summary = summary
        if st.session_state.summary:
            st.markdown(st.session_state.summary)

    with col_b:
        if st.button("Write newsletter", type="primary", key="btn_write"):
            if not st.session_state.summary:
                st.warning("Summarize first.")
            elif not has_key:
                st.error("No API key configured.")
            else:
                with st.spinner("Writing the newsletter..."):
                    newsletter = guard(service.write_newsletter(model=model or None))
                if newsletter is not None:
                    st.session_state.newsletter = newsletter
        if st.session_state.newsletter:
            st.markdown(st.session_state.newsletter)
            st.download_button(
                "⬇️ Download newsletter.md",
                st.session_state.newsletter,
                file_name="newsletter.md",
                mime="text/markdown",
            )

# --- Tab: Full pipeline ------------------------------------------------------
with tab_full:
    st.subheader("Run the whole pipeline")
    st.write("Fetch → database → filter → summarize → write, in one go.")
    if st.button("Run full pipeline", type="primary", key="btn_full"):
        if not sources:
            st.warning("Select at least one source in the sidebar.")
        elif not has_key:
            st.error("No API key configured.")
        else:
            progress = st.progress(0, text="Fetching...")
            articles = guard(
                service.fetch_articles(sources, hn_limit=hn_limit, rss_feed=rss_feed)
            )
            if articles is not None:
                st.session_state.articles = articles
                progress.progress(30, text=f"Fetched {len(articles)} — filtering...")

                filtered = guard(
                    service.filter_articles(articles, max_filter, model=model or None)
                )
                if filtered is not None:
                    st.session_state.filtered = filtered
                    progress.progress(60, text="Summarizing...")

                    summary = guard(service.summarize(model=model or None))
                    if summary is not None:
                        st.session_state.summary = summary
                        progress.progress(80, text="Writing newsletter...")

                        newsletter = guard(service.write_newsletter(model=model or None))
                        if newsletter is not None:
                            st.session_state.newsletter = newsletter
                            progress.progress(100, text="Done!")
                            st.success("Pipeline complete — see the newsletter below.")

    if st.session_state.newsletter:
        st.markdown(st.session_state.newsletter)
        st.download_button(
            "⬇️ Download newsletter.md",
            st.session_state.newsletter,
            file_name="newsletter.md",
            mime="text/markdown",
            key="dl_full",
        )

# --- Tab: Search -------------------------------------------------------------
with tab_search:
    st.subheader("Search the article database (via MCP)")
    st.write("Queries the SQLite database through the database MCP server + SearchSkill.")
    query = st.text_input("Search query", "machine learning")
    if st.button("Search", type="primary", key="btn_search"):
        with st.spinner("Querying the MCP database server..."):
            st.session_state.search = guard(service.search(query, limit=20))

    res = st.session_state.search
    if res:
        if res["success"]:
            st.success(f"Found {res['total']} matches for '{res['query']}'.")
            if res["articles"]:
                st.dataframe(
                    [
                        {
                            "title": a.get("title"),
                            "source": a.get("source"),
                            "url": a.get("url"),
                        }
                        for a in res["articles"]
                    ],
                    use_container_width=True,
                    column_config={"url": st.column_config.LinkColumn("url")},
                    hide_index=True,
                )
        else:
            st.error(f"Search failed: {res.get('error')}")

# --- Tab: Evaluation ---------------------------------------------------------
with tab_eval:
    st.subheader("Evaluate the filter agent")
    st.write("Runs the filter over a 10-case golden dataset and reports metrics.")
    if st.button("Run evaluation", type="primary", key="btn_eval"):
        if not has_key:
            st.error("No API key configured.")
        else:
            with st.spinner("Evaluating against the golden dataset (10 LLM calls)..."):
                ev_result = guard(service.evaluate(model=model or None))
            if ev_result is not None:
                st.session_state.evaluation = ev_result

    ev = st.session_state.evaluation
    if ev:
        m = ev["metrics"]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Accuracy", f"{m['accuracy']:.0%}")
        c2.metric("Precision", f"{m['precision']:.0%}")
        c3.metric("Recall", f"{m['recall']:.0%}")
        c4.metric("F1 score", f"{m['f1_score']:.3f}")
        st.dataframe(
            [
                {
                    "id": r["test_case_id"],
                    "title": r["title"],
                    "expected": r["expected"],
                    "predicted": r["predicted"],
                    "score": r["score"],
                    "correct": "✅" if r["correct"] else "❌",
                }
                for r in ev["results"]
            ],
            use_container_width=True,
            hide_index=True,
        )

# --- Tab: About --------------------------------------------------------------
with tab_about:
    st.subheader("About this project")
    st.markdown(
        """
This is the reference implementation of the **AI Upskill** news pipeline:

- **Fetch** — async, concurrent fetchers for HackerNews, RSS, and GitHub Trending.
- **Filter** — `NewsFilterAgent` scores AI/ML relevance via LiteLLM.
- **Summarize → Write** — `SummarizerAgent` groups by topic, `WriterAgent` drafts a newsletter.
- **MCP** — a database MCP server exposes the SQLite store; `SearchSkill` queries it.
- **Evaluation** — accuracy / precision / recall / F1 on a golden dataset.

Built with SOLID principles and the Factory, Strategy, and Template Method patterns.
See `docs/architecture.md` and `docs/design-decisions.md`.
"""
    )
    if Path(service.NEWSLETTER_MD).exists():
        st.caption(f"Latest newsletter: `{service.NEWSLETTER_MD}`")
