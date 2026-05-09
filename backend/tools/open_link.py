from __future__ import annotations

import httpx
from bs4 import BeautifulSoup
from langchain_core.tools import tool

MAX_CONTENT_LENGTH = 10_000


@tool
async def open_link(url: str) -> str:
    """Fetch and extract the main text content from a URL.

    Use this when the user shares a link and wants you to read, summarize,
    or analyze the content of a web page.

    Args:
        url: The full URL to fetch (must start with http:// or https://).
    """
    if not url.startswith(("http://", "https://")):
        return f"Invalid URL: {url}. Must start with http:// or https://"

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as client:
            resp = await client.get(
                url, headers={"User-Agent": "SaaStoAgent/0.1 (link reader)"}
            )
            resp.raise_for_status()
    except httpx.HTTPStatusError as e:
        return f"HTTP error {e.response.status_code} fetching {url}"
    except httpx.RequestError as e:
        return f"Failed to fetch {url}: {e}"

    content_type = resp.headers.get("content-type", "")
    if "text/html" not in content_type and "text/plain" not in content_type:
        return f"Unsupported content type: {content_type}."

    if "text/plain" in content_type:
        return f"URL: {url}\n\n--- Content ---\n{resp.text[:MAX_CONTENT_LENGTH]}"

    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    title = soup.title.string.strip() if soup.title and soup.title.string else url
    main = soup.find("main") or soup.find("article") or soup.find("body")
    text = main.get_text(separator="\n", strip=True) if main else soup.get_text(
        separator="\n", strip=True
    )
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    clean_text = "\n".join(lines)[:MAX_CONTENT_LENGTH]
    return f"Title: {title}\nURL: {url}\n\n--- Content ---\n{clean_text}"
