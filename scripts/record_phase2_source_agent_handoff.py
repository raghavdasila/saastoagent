from __future__ import annotations

import argparse
import asyncio
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import uuid4

from playwright.async_api import async_playwright


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Preflight, record, or verify the isolated Phase 2 Source stay handoff."
    )
    parser.add_argument("mode", choices=("preflight", "record", "verify"))
    parser.add_argument("--url", default="http://127.0.0.1:5199")
    parser.add_argument("--backend-url", default="http://127.0.0.1:8099")
    parser.add_argument("--conversation-id")
    parser.add_argument("--resume-url")
    parser.add_argument("--expected-node", default="sources.api")
    parser.add_argument("--expected-agent-ref")
    parser.add_argument("--expected-source-id")
    parser.add_argument("--expected-revision-id")
    parser.add_argument("--message", default="Stay with this API because I still need to choose what it may access.")
    parser.add_argument("--artifact")
    return parser.parse_args()


def _access_token() -> str:
    token = os.environ.get("CORPUS_PHASE2_ACCESS_TOKEN", "").strip()
    if not token:
        raise RuntimeError("CORPUS_PHASE2_ACCESS_TOKEN is required and is never written to evidence.")
    return token


def _refresh_token() -> str:
    token = os.environ.get("CORPUS_PHASE2_REFRESH_TOKEN", "").strip()
    if not token:
        raise RuntimeError("CORPUS_PHASE2_REFRESH_TOKEN is required for record mode and is never written to evidence.")
    return token


def _get_json(url: str, token: str, conversation_id: str) -> dict[str, object]:
    request = Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "X-Corpus-Conversation-ID": conversation_id,
            "Accept": "application/json",
            "Cache-Control": "no-cache",
        },
    )
    try:
        with urlopen(request, timeout=10) as response:
            payload = json.load(response)
    except HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"preflight HTTP {error.code}: {body}") from error
    if not isinstance(payload, dict):
        raise RuntimeError("Preflight response was not an object.")
    return payload


def _operation_ids(value: object) -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        operation_id = value.get("operation_id") or value.get("operationId")
        if isinstance(operation_id, str):
            found.append(operation_id)
        for nested in value.values():
            found.extend(_operation_ids(nested))
    elif isinstance(value, list):
        for nested in value:
            found.extend(_operation_ids(nested))
    return found


def _committed_operation_ids(inspection: dict[str, object]) -> list[str]:
    recent = inspection.get("recent_operations")
    return _operation_ids(recent) if isinstance(recent, list) else []


def _chat_messages(inspection: dict[str, object]) -> list[dict[str, object]]:
    context = inspection.get("agent_context")
    messages = context.get("messages") if isinstance(context, dict) else None
    return [item for item in messages if isinstance(item, dict)] if isinstance(messages, list) else []


def _active_surface_values(inspection: dict[str, object]) -> dict[str, object]:
    context = inspection.get("agent_context")
    model_context = context.get("model_context") if isinstance(context, dict) else None
    surface = model_context.get("active_surface") if isinstance(model_context, dict) else None
    values = surface.get("values") if isinstance(surface, dict) else None
    return {
        item["name"]: item.get("value")
        for item in values
        if isinstance(item, dict) and isinstance(item.get("name"), str)
    } if isinstance(values, list) else {}


def _preflight(args: argparse.Namespace) -> dict[str, object]:
    if not args.conversation_id:
        raise RuntimeError("--conversation-id is required.")
    token = _access_token()
    conversation = _get_json(
        f"{args.backend_url.rstrip('/')}/api/conversations/{args.conversation_id}",
        token,
        args.conversation_id,
    )
    inspection = _get_json(
        f"{args.backend_url.rstrip('/')}/api/routedeck/inspect",
        token,
        args.conversation_id,
    )
    node = conversation.get("current_node_id")
    if node != args.expected_node:
        raise RuntimeError(f"checkpoint node is {node!r}; expected {args.expected_node!r}")
    snapshot = inspection.get("agent_context")
    if not isinstance(snapshot, dict):
        raise RuntimeError("Checkpoint has no authenticated Agent context.")
    messages = _chat_messages(inspection)
    surface_values = _active_surface_values(inspection)
    expected_values = {
        "return_agent_ref": args.expected_agent_ref,
        "selected_source_id": args.expected_source_id,
        "selected_source_revision_id": args.expected_revision_id,
    }
    for name, expected in expected_values.items():
        if expected is not None and surface_values.get(name) != expected:
            raise RuntimeError(
                f"checkpoint {name} is {surface_values.get(name)!r}; expected {expected!r}"
            )
    return {
        "conversationId": args.conversation_id,
        "nodeId": node,
        "sessionVersion": conversation.get("session_version"),
        "operationIds": list(dict.fromkeys(_operation_ids(inspection))),
        "committedOperationIds": _committed_operation_ids(inspection),
        "chatMessageCount": len(messages),
        "latestAssistant": next(
            (
                item.get("content")
                for item in reversed(messages)
                if item.get("role") in {"assistant", "ai"}
                and isinstance(item.get("content"), str)
                and item["content"].strip()
            ),
            None,
        ),
        "agentRef": surface_values.get("return_agent_ref"),
        "sourceId": surface_values.get("selected_source_id"),
        "revisionId": surface_values.get("selected_source_revision_id"),
    }


async def _record(args: argparse.Namespace) -> int:
    if not args.resume_url or "resume_handle=" not in args.resume_url:
        raise RuntimeError("record requires an exact canonical --resume-url with resume_handle")
    before = await asyncio.to_thread(_preflight, args)
    repository = Path(__file__).resolve().parents[1]
    run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:10]
    directory = repository / "artifacts" / "phase2-source-agent-handoff" / run_id
    raw_video = directory / "raw-video"
    raw_video.mkdir(parents=True)
    diagnostics: dict[str, list[object]] = {"console": [], "page": [], "http": []}
    error: str | None = None
    video: Path | None = None
    try:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={"width": 1440, "height": 1000},
                record_video_dir=raw_video,
                record_video_size={"width": 1440, "height": 1000},
            )
            page = await context.new_page()
            page.on("console", lambda item: diagnostics["console"].append(item.text) if item.type == "error" else None)
            page.on("pageerror", lambda item: diagnostics["page"].append(str(item)))
            page.on("response", lambda item: diagnostics["http"].append({"status": item.status, "url": item.url}) if item.status >= 400 else None)
            await page.goto(args.url)
            await page.evaluate(
                """async ({token, conversation}) => {
                  const opened = indexedDB.open('corpus-auth', 1);
                  await new Promise((resolve, reject) => {
                    opened.onupgradeneeded = () => {
                      if (!opened.result.objectStoreNames.contains('credentials')) opened.result.createObjectStore('credentials');
                    };
                    opened.onsuccess = resolve;
                    opened.onerror = () => reject(opened.error);
                  });
                  const db = opened.result;
                  const tx = db.transaction('credentials', 'readwrite');
                  tx.objectStore('credentials').put(token, 'refresh_token');
                  await new Promise((resolve, reject) => { tx.oncomplete = resolve; tx.onerror = () => reject(tx.error); });
                  db.close();
                  sessionStorage.setItem('corpus.selected-conversation.v1', conversation);
                }""",
                {"token": _refresh_token(), "conversation": args.conversation_id},
            )
            await page.goto(args.resume_url)
            await page.get_by_text("Loading Corpus…", exact=True).wait_for(state="detached", timeout=30_000)
            maximize = page.get_by_role("button", name="Maximize surface", exact=True)
            await maximize.wait_for(timeout=20_000)
            await maximize.click()
            composer = page.get_by_role("textbox", name="Message the assistant", exact=True)
            await composer.fill(args.message)
            await composer.press("Enter")
            deadline = asyncio.get_running_loop().time() + 180
            after = before
            while asyncio.get_running_loop().time() < deadline:
                after = await asyncio.to_thread(_preflight, args)
                if (
                    int(after["chatMessageCount"]) >= int(before["chatMessageCount"]) + 2
                    and after["latestAssistant"] is not None
                    and int(after["sessionVersion"]) > int(before["sessionVersion"])
                ):
                    break
                await asyncio.sleep(0.5)
            else:
                raise TimeoutError("The isolated chat turn did not become durably complete.")
            delta = after["committedOperationIds"][len(before["committedOperationIds"]):]
            if "agents.return_from_source" in delta:
                raise RuntimeError("The chat turn incorrectly returned from the active API Source.")
            if after["nodeId"] != args.expected_node:
                raise RuntimeError("The chat turn did not remain in the exact API Source node.")
            await page.screenshot(path=directory / "phase2-source-agent-stay-maximized.png")
            await page.wait_for_timeout(1500)
    except Exception as caught:
        error = f"{type(caught).__name__}: {caught}"
    finally:
        candidates = sorted(raw_video.glob("*.webm"), key=lambda value: value.stat().st_mtime)
        video = candidates[-1] if candidates else None
    passed = error is None and video is not None and not any(diagnostics.values())
    result = {
        "runId": run_id,
        "status": "passed" if passed else "failed",
        "preflight": before,
        "after": after if "after" in locals() else None,
        "diagnostics": diagnostics,
        "video": str(video.relative_to(repository)) if video else None,
        "error": error,
        "boundary": "One isolated retained Phase 2 chat turn; no full journey or feature replay.",
    }
    (directory / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))
    return 0 if passed else 1


def _verify(path: str | None) -> int:
    if not path:
        raise RuntimeError("verify requires --artifact.")
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    diagnostics = payload.get("diagnostics")
    clean_diagnostics = (
        isinstance(diagnostics, dict)
        and bool(diagnostics)
        and all(isinstance(value, list) and not value for value in diagnostics.values())
    )
    if payload.get("status") != "passed" or not payload.get("video") or not clean_diagnostics:
        raise RuntimeError("Artifact does not prove a clean passed Phase 2 recording.")
    print(json.dumps({"status": "passed", "artifact": path}))
    return 0


async def main(args: argparse.Namespace) -> int:
    if args.mode == "preflight":
        print(json.dumps(await asyncio.to_thread(_preflight, args)))
        return 0
    if args.mode == "record":
        return await _record(args)
    return _verify(args.artifact)


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main(arguments())))
