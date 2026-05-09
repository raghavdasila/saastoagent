from __future__ import annotations

from langchain_core.tools import tool


@tool
def web_search(query: str, max_results: int = 5) -> str:
    """Search the web for current information about a topic.

    Use this when the user asks about recent events, news, or anything
    that requires up-to-date information beyond your training data.

    Args:
        query: The search query string.
        max_results: Maximum number of results to return (default 5).
    """
    return (
        f"[Web Search Placeholder] No real search provider configured.\n"
        f"Query: {query}\n"
        f"To enable real web search, integrate a search API (e.g., Tavily, "
        f"Brave Search, DuckDuckGo) in backend/tools/web_search.py."
    )
