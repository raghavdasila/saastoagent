from __future__ import annotations

import argparse
import json
from uuid import uuid4

import httpx


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Exercise bearer-selected Corpus runs and reconnect by cursor."
    )
    parser.add_argument("--base-url", default="http://127.0.0.1:8099")
    parser.add_argument("--origin", default="http://127.0.0.1:5199")
    parser.add_argument("--message", default="What can Corpus help me build?")
    arguments = parser.parse_args()
    run_id = uuid4().hex

    with httpx.Client(
        base_url=arguments.base_url,
        headers={"Origin": arguments.origin},
        timeout=180.0,
    ) as client:
        _expect_json(client.get("/healthz"), {"status": "ok"})
        _expect_json(client.get("/readyz"), {"status": "ready"})
        anonymous = client.post("/api/auth/anonymous")
        anonymous.raise_for_status()
        if "set-cookie" in anonymous.headers:
            raise RuntimeError("Bearer authentication unexpectedly set a cookie.")
        access_token = anonymous.json()["access_token"]
        client.headers["Authorization"] = f"Bearer {access_token}"

        created = client.post("/api/conversations", json={})
        created.raise_for_status()
        conversation = created.json()
        if conversation["current_node_id"] != "lounge.home":
            raise RuntimeError("The conversation did not enter lounge.home.")
        client.headers["X-Corpus-Conversation-ID"] = conversation["id"]
        active = conversation.get("active_run")
        if not isinstance(active, dict):
            raise RuntimeError("The declared entry run was not discoverable.")
        greeting = _disconnect_and_resume(client, active["request_id"])

        projection = client.get("/api/routedeck/session")
        projection.raise_for_status()
        request_id = f"smoke-chat-{run_id}"
        request = {
            "request_id": request_id,
            "expected_session_version": projection.json()["projection"][
                "session_version"
            ],
            "trigger": "user_message",
            "message": arguments.message,
        }
        started = client.post("/api/routedeck/conversation/runs", json=request)
        started.raise_for_status()
        answer = _disconnect_and_resume(client, request_id)
        attached = client.post("/api/routedeck/conversation/runs", json=request)
        attached.raise_for_status()
        if attached.json()["run"]["stage"] != "completed":
            raise RuntimeError("Idempotent run attachment did not return completion.")

        history = client.get("/api/routedeck/conversation")
        history.raise_for_status()
        turns = history.json()["turns"]
        roles = [turn["role"] for turn in turns]
        if roles[-3:] != ["assistant", "user", "assistant"]:
            raise RuntimeError(f"Unexpected durable conversation roles: {roles}")
        if sum(turn.get("request_id") == request_id for turn in turns) != 2:
            raise RuntimeError("The user run was committed more or less than once.")

    print("Corpus live bearer reconnect smoke passed.")
    print("node=lounge.home auth=bearer conversation=opaque")
    print(f"greeting_chars={len(greeting)} answer_chars={len(answer)}")
    print("disconnect_reconnect=entry,user history_tail=assistant,user,assistant")


def _disconnect_and_resume(client: httpx.Client, request_id: str) -> str:
    run = _load_run(client, request_id)
    cursor = run["cursor"]
    if run["stage"] not in {"completed", "interrupted"}:
        with client.stream(
            "GET",
            f"/api/routedeck/conversation/runs/{request_id}/events",
            params={"after": cursor},
        ) as response:
            response.raise_for_status()
            first = next(_run_events(response), None)
            if first is not None:
                cursor = first["cursor"]
        run = _load_run(client, request_id)
        cursor = run["cursor"]
    if run["stage"] not in {"completed", "interrupted"}:
        with client.stream(
            "GET",
            f"/api/routedeck/conversation/runs/{request_id}/events",
            params={"after": cursor},
        ) as response:
            response.raise_for_status()
            for run in _run_events(response):
                cursor = run["cursor"]
    run = _load_run(client, request_id)
    if run["stage"] != "completed":
        raise RuntimeError(
            f"Conversation run {request_id} ended as {run['stage']}: {run['failure']}"
        )
    content = run["assistant_content"]
    if not isinstance(content, str) or not content.strip():
        raise RuntimeError("The completed assistant run has no visible content.")
    return content


def _load_run(client: httpx.Client, request_id: str) -> dict[str, object]:
    response = client.get(f"/api/routedeck/conversation/runs/{request_id}")
    response.raise_for_status()
    run = response.json()["run"]
    if not isinstance(run, dict):
        raise RuntimeError("RouteDeck returned an invalid run envelope.")
    return run


def _run_events(response: httpx.Response):
    event_name: str | None = None
    data: str | None = None
    for line in response.iter_lines():
        if not line:
            if event_name == "conversation_run" and data is not None:
                decoded = json.loads(data)
                if not isinstance(decoded, dict):
                    raise RuntimeError("A run event did not contain an object.")
                yield decoded
            event_name = None
            data = None
        elif line.startswith("event: "):
            event_name = line.removeprefix("event: ")
        elif line.startswith("data: "):
            data = line.removeprefix("data: ")


def _expect_json(response: httpx.Response, expected: dict[str, str]) -> None:
    response.raise_for_status()
    if response.json() != expected:
        raise RuntimeError(
            f"Unexpected response from {response.request.url}: {response.text}"
        )


if __name__ == "__main__":
    main()
