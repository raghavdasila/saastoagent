from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from toolrouter.integration.feedback import redact_secrets
from toolrouter.integration.saastoagent_adapter import route_tool_request


SANDBOX_ROOT = Path(__file__).resolve().parent


def append_sandbox_feedback(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "event_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **redact_secrets(payload),
    }
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(event, sort_keys=True) + "\n")
    return event


def _json_response(handler: BaseHTTPRequestHandler, status: int, payload: dict[str, Any]) -> None:
    body = json.dumps(payload, default=str).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _static_response(handler: BaseHTTPRequestHandler, path: Path, content_type: str) -> None:
    body = path.read_bytes()
    handler.send_response(200)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def make_handler(*, artifacts: Path, feedback_log: Path, guardrails: dict[str, Any]):
    class SandboxHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            if parsed.path in {"/", "/index.html"}:
                return _static_response(self, SANDBOX_ROOT / "index.html", "text/html; charset=utf-8")
            if parsed.path == "/app.js":
                return _static_response(self, SANDBOX_ROOT / "app.js", "text/javascript; charset=utf-8")
            if parsed.path == "/styles.css":
                return _static_response(self, SANDBOX_ROOT / "styles.css", "text/css; charset=utf-8")
            return _json_response(self, 404, {"error": "not_found"})

        def do_POST(self) -> None:  # noqa: N802
            length = int(self.headers.get("Content-Length", "0") or 0)
            try:
                payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            except Exception:
                return _json_response(self, 400, {"error": "invalid_json"})
            if self.path == "/api/route":
                try:
                    decision = route_tool_request(
                        tenant_id=str(payload.get("tenant_id") or "sandbox-tenant"),
                        integration_id=str(payload.get("integration_id") or "sandbox-integration"),
                        user_query=str(payload.get("query") or ""),
                        conversation_context=payload.get("conversation_context") if isinstance(payload.get("conversation_context"), list) else [],
                        artifacts_path=str(artifacts),
                        guardrail_config={**guardrails, **(payload.get("guardrails") if isinstance(payload.get("guardrails"), dict) else {})},
                        feedback_log_path=str(feedback_log),
                        feedback_model_path=str(payload.get("feedback_model_path") or "") or None,
                    )
                    return _json_response(self, 200, decision.model_dump(mode="json"))
                except Exception as exc:
                    return _json_response(self, 500, {"error": exc.__class__.__name__, "message": str(exc)})
            if self.path == "/api/feedback":
                event = append_sandbox_feedback(feedback_log, payload)
                return _json_response(self, 200, event)
            return _json_response(self, 404, {"error": "not_found"})

        def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
            return

    return SandboxHandler


def run_sandbox(host: str, port: int, artifacts: Path, feedback_log: Path, guardrails: dict[str, Any]) -> None:
    server = ThreadingHTTPServer((host, port), make_handler(artifacts=artifacts, feedback_log=feedback_log, guardrails=guardrails))
    print(f"SaaStoAgent ToolRouter sandbox running at http://{host}:{port}")
    print(f"Artifacts: {artifacts}")
    print(f"Feedback log: {feedback_log}")
    server.serve_forever()
