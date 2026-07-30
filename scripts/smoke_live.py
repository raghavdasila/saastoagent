from __future__ import annotations

import argparse
import json
from uuid import uuid4

import httpx


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Exercise the running Corpus guest Lounge against its real model."
    )
    parser.add_argument("--base-url", default="http://127.0.0.1:8099")
    parser.add_argument(
        "--origin", default="http://127.0.0.1:5199"
    )
    parser.add_argument(
        "--message", default="What can Corpus help me build?"
    )
    arguments = parser.parse_args()
    run_id = uuid4().hex

    with httpx.Client(
        base_url=arguments.base_url,
        headers={"Origin": arguments.origin},
        timeout=120.0,
    ) as client:
        _expect_json(client.get("/healthz"), 200, {"status": "ok"})
        _expect_json(client.get("/readyz"), 200, {"status": "ready"})

        created = client.post(
            "/api/routedeck/sessions",
            json={"request_id": f"smoke-session-{run_id}"},
        )
        created.raise_for_status()
        projection = created.json()["projection"]
        if projection["current"]["node_id"] != "lounge.home":
            raise RuntimeError("The guest session did not enter lounge.home.")
        if "corpus_guest" not in client.cookies:
            raise RuntimeError("The guest session cookie was not created.")

        greeting = client.post(
            "/api/routedeck/conversation/assistant-turn",
            json={
                "request_id": f"smoke-entry-{run_id}",
                "expected_session_version": projection["session_version"],
            },
        )
        greeting.raise_for_status()
        greeting_text = _assistant_text(greeting.text)

        resumed = client.get("/api/routedeck/session")
        resumed.raise_for_status()
        current_version = resumed.json()["projection"]["session_version"]
        answer = client.post(
            "/api/routedeck/chat",
            json={
                "request_id": f"smoke-chat-{run_id}",
                "expected_session_version": current_version,
                "message": arguments.message,
            },
        )
        answer.raise_for_status()
        answer_text = _assistant_text(answer.text)

        history = client.get("/api/routedeck/conversation")
        history.raise_for_status()
        roles = [turn["role"] for turn in history.json()["turns"]]
        if roles[-3:] != ["assistant", "user", "assistant"]:
            raise RuntimeError(f"Unexpected durable conversation roles: {roles}")

    print("Corpus live smoke passed.")
    print("node=lounge.home cookie=corpus_guest")
    print(f"greeting_chars={len(greeting_text)} answer_chars={len(answer_text)}")
    print("history_tail=assistant,user,assistant")


def _expect_json(
    response: httpx.Response, status: int, expected: dict[str, str]
) -> None:
    response.raise_for_status()
    if response.status_code != status or response.json() != expected:
        raise RuntimeError(
            f"Unexpected response from {response.request.url}: "
            f"{response.status_code} {response.text}"
        )


def _assistant_text(body: str) -> str:
    events: list[tuple[str, dict[str, object]]] = []
    for frame in body.split("\n\n"):
        event_name: str | None = None
        event_data: dict[str, object] | None = None
        for line in frame.splitlines():
            if line.startswith("event: "):
                event_name = line.removeprefix("event: ")
            elif line.startswith("data: "):
                decoded = json.loads(line.removeprefix("data: "))
                if not isinstance(decoded, dict):
                    raise RuntimeError("A stream event did not contain an object.")
                event_data = decoded
        if event_name is not None and event_data is not None:
            events.append((event_name, event_data))
    names = [name for name, _data in events]
    if "assistant_end" not in names or "stream_end" not in names:
        raise RuntimeError(f"The assistant stream did not complete: {names}")
    text = "".join(
        content
        for name, data in events
        if name == "assistant_delta"
        and isinstance((content := data.get("content")), str)
    )
    if not text.strip():
        raise RuntimeError("The assistant completed without visible content.")
    return text


if __name__ == "__main__":
    main()
