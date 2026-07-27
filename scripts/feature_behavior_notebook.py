"""Serve the 11-feature behavior notebook and persist its notes as Markdown."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
NOTEBOOK_PATH = REPOSITORY_ROOT / "docs" / "corpus-feature-behavior-notebook.html"
DESIGN_NOTEBOOK_PATH = REPOSITORY_ROOT / "docs" / "corpus-routedeck-design-notebook.html"
DEFAULT_OUTPUT_PATH = REPOSITORY_ROOT / "docs" / "feature-behavior-notes.md"
MAX_REQUEST_BYTES = 512_000

FEATURES = (
    {"id": "workspace", "name": "Workspace"},
    {"id": "agents", "name": "Agents"},
    {"id": "source-hub", "name": "Source Hub"},
    {"id": "api-source", "name": "API Source / API Collection"},
    {"id": "agent-designer", "name": "Agent Designer"},
    {"id": "agent-builder", "name": "Agent Builder"},
    {"id": "sandbox", "name": "Sandbox"},
    {"id": "evaluation", "name": "Evaluation"},
    {"id": "channels", "name": "Channels"},
    {"id": "deployment", "name": "Deployment"},
    {"id": "operations", "name": "Operations"},
)


def _validated_notes(notes: Any) -> dict[str, str]:
    expected_keys = [feature["id"] for feature in FEATURES]
    if not isinstance(notes, dict) or set(notes) != set(expected_keys):
        raise ValueError("Notes must contain exactly the 11 approved feature keys.")

    validated: dict[str, str] = {}
    for key in expected_keys:
        value = notes[key]
        if not isinstance(value, str):
            raise ValueError(f"Note '{key}' must be text.")
        if len(value) > 40_000:
            raise ValueError(f"Note '{key}' exceeds the 40,000 character limit.")
        validated[key] = value.strip()
    return validated


def render_markdown(
    notes: Any,
    *,
    updated_at: str | None = None,
) -> str:
    """Render a complete, deterministic Markdown snapshot for all 11 features."""

    validated = _validated_notes(notes)
    timestamp = updated_at or datetime.now().astimezone().isoformat(timespec="seconds")
    sections = [
        "# Corpus Basic Agent Feature Behavior Notes",
        "",
        f"Updated: {timestamp}",
        "",
        (
            "Status: Owner-authored working notes. These are discussion input and do not "
            "become formal product contracts until reconciled."
        ),
        "",
    ]

    for index, feature in enumerate(FEATURES, start=1):
        sections.extend(
            [
                f"## {index}. {feature['name']}",
                "",
                validated[feature["id"]],
                "",
            ]
        )
    return "\n".join(sections).rstrip() + "\n"


def parse_markdown(markdown: str) -> dict[str, str]:
    """Read notes from a file previously emitted by ``render_markdown``."""

    notes: dict[str, str] = {}
    lines = markdown.splitlines()
    heading_lookup = {
        f"## {index}. {feature['name']}": feature["id"]
        for index, feature in enumerate(FEATURES, start=1)
    }
    active_key: str | None = None
    active_lines: list[str] = []

    def commit() -> None:
        if active_key is not None:
            notes[active_key] = "\n".join(active_lines).strip()

    for line in lines:
        if line in heading_lookup:
            commit()
            active_key = heading_lookup[line]
            active_lines = []
        elif active_key is not None:
            active_lines.append(line)
    commit()

    return {feature["id"]: notes.get(feature["id"], "") for feature in FEATURES}


def save_notes(
    notes: Any,
    *,
    output_path: Path = DEFAULT_OUTPUT_PATH,
    updated_at: str | None = None,
) -> str:
    """Atomically replace the fixed Markdown note file and return its timestamp."""

    timestamp = updated_at or datetime.now().astimezone().isoformat(timespec="seconds")
    markdown = render_markdown(notes, updated_at=timestamp)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = output_path.with_suffix(output_path.suffix + ".tmp")
    temporary_path.write_text(markdown, encoding="utf-8")
    temporary_path.replace(output_path)
    return timestamp


def load_notes(output_path: Path = DEFAULT_OUTPUT_PATH) -> dict[str, str]:
    if not output_path.exists():
        return {feature["id"]: "" for feature in FEATURES}
    return parse_markdown(output_path.read_text(encoding="utf-8"))


class FeatureBehaviorNotebookHandler(BaseHTTPRequestHandler):
    server_version = "CorpusFeatureBehaviorNotebook/1.0"

    @property
    def output_path(self) -> Path:
        return self.server.output_path  # type: ignore[attr-defined]

    def _send_bytes(self, content: bytes, content_type: str, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(content)

    def _send_json(self, payload: dict[str, Any], status: int = 200) -> None:
        self._send_bytes(
            json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            "application/json; charset=utf-8",
            status,
        )

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        path = self.path.split("?", 1)[0]
        if path in {"/", "/corpus-feature-behavior-notebook.html"}:
            if not NOTEBOOK_PATH.exists():
                self._send_json({"error": "Notebook HTML is missing."}, HTTPStatus.NOT_FOUND)
                return
            self._send_bytes(
                NOTEBOOK_PATH.read_bytes(),
                "text/html; charset=utf-8",
            )
            return
        if path == "/design-notebook":
            self._send_bytes(
                DESIGN_NOTEBOOK_PATH.read_bytes(),
                "text/html; charset=utf-8",
            )
            return
        if path == "/api/notes":
            self._send_json(
                {
                    "notes": load_notes(self.output_path),
                    "outputPath": str(self.output_path),
                }
            )
            return
        if path == "/api/health":
            self._send_json({"status": "ok"})
            return
        self._send_json({"error": "Not found."}, HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        if self.path.split("?", 1)[0] != "/api/notes":
            self._send_json({"error": "Not found."}, HTTPStatus.NOT_FOUND)
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            if content_length <= 0 or content_length > MAX_REQUEST_BYTES:
                raise ValueError("Request body size is invalid.")
            payload = json.loads(self.rfile.read(content_length).decode("utf-8"))
            if not isinstance(payload, dict) or "notes" not in payload:
                raise ValueError("Request must contain a notes object.")
            timestamp = save_notes(payload["notes"], output_path=self.output_path)
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
            self._send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
            return
        except OSError as error:
            self._send_json(
                {"error": f"The notes file could not be written: {error}"},
                HTTPStatus.INTERNAL_SERVER_ERROR,
            )
            return

        self._send_json(
            {
                "status": "saved",
                "savedAt": timestamp,
                "outputPath": str(self.output_path),
            }
        )

    def log_message(self, format: str, *args: Any) -> None:
        print(f"[{self.log_date_time_string()}] {format % args}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Serve the Corpus feature behavior notebook on localhost."
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8771)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument(
        "--allow-container-bind",
        action="store_true",
        help="Allow an explicit 0.0.0.0 bind for a loopback-published container.",
    )
    arguments = parser.parse_args()

    is_loopback = arguments.host in {"127.0.0.1", "localhost", "::1"}
    is_explicit_container_bind = (
        arguments.allow_container_bind and arguments.host == "0.0.0.0"
    )
    if not is_loopback and not is_explicit_container_bind:
        raise SystemExit("This authoring server may only bind to a loopback address.")

    server = ThreadingHTTPServer(
        (arguments.host, arguments.port),
        FeatureBehaviorNotebookHandler,
    )
    server.output_path = arguments.output.resolve()  # type: ignore[attr-defined]
    print(f"Notebook: http://{arguments.host}:{arguments.port}/")
    print(f"Notes file: {server.output_path}")  # type: ignore[attr-defined]
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
