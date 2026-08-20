from __future__ import annotations

import os
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

import httpx

from corpus.persistence.migrations import upgrade_database


@dataclass(frozen=True)
class IsolatedRuntimeEndpoints:
    frontend_url: str
    backend_url: str
    database_url: str


class IsolatedCorpusRuntime:
    """Own two local dev processes and disposable persistent state for an eval run."""

    def __init__(
        self,
        repository: Path,
        *,
        name: str,
        backend_port: int,
        frontend_port: int,
        mail_outage: bool = False,
    ) -> None:
        self.repository = repository
        self.name = name
        self.backend_port = backend_port
        self.frontend_port = frontend_port
        self.mail_outage = mail_outage
        self.runtime_root = repository / ".runtime" / "product-journeys" / name
        self.processes: list[subprocess.Popen[bytes]] = []
        self._logs: list[object] = []
        database_path = (self.runtime_root / "corpus.sqlite3").resolve()
        self.endpoints = IsolatedRuntimeEndpoints(
            frontend_url=f"http://127.0.0.1:{frontend_port}",
            backend_url=f"http://127.0.0.1:{backend_port}",
            database_url=f"sqlite+aiosqlite:///{database_path.as_posix()}",
        )

    async def start(self) -> IsolatedRuntimeEndpoints:
        self.runtime_root.mkdir(parents=True, exist_ok=False)
        await upgrade_database(self.endpoints.database_url)
        environment = _read_env_file(self.repository / ".env.local")
        environment.update(os.environ)
        environment.update(
            {
                "PYTHONPATH": str(self.repository / "backend" / "src"),
                "ROUTEDECK_DATABASE_URL": (
                    "sqlite+pysqlite:///"
                    + (self.runtime_root / "routedeck.sqlite").resolve().as_posix()
                ),
                "ROUTEDECK_INSTANCE_ID": f"corpus-product-eval-{self.name}",
                "ROUTEDECK_BROWSER_ORIGINS": self.endpoints.frontend_url,
                "CORPUS_DATABASE_URL": self.endpoints.database_url,
                "CORPUS_MIGRATION_REVISION": "0020_sandbox_deployment_mode",
                "CORPUS_PUBLIC_FRONTEND_URL": self.endpoints.frontend_url,
                "CORPUS_SOURCE_DATA_ROOT": str(self.runtime_root / "sources"),
            }
        )
        if self.mail_outage:
            environment["CORPUS_SMTP_HOST"] = "smtp-outage.invalid"
            environment["CORPUS_SMTP_TIMEOUT_SECONDS"] = "1"
        creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        backend_log = (self.runtime_root / "backend.log").open("wb")
        self._logs.append(backend_log)
        backend = subprocess.Popen(
            [
                str(self.repository / ".venv" / "Scripts" / "python.exe"),
                "-m",
                "uvicorn",
                "corpus.main:create_live_app",
                "--factory",
                "--host",
                "127.0.0.1",
                "--port",
                str(self.backend_port),
            ],
            cwd=self.repository / "backend",
            env=environment,
            stdout=backend_log,
            stderr=subprocess.STDOUT,
            creationflags=creation_flags,
        )
        self.processes.append(backend)
        await _wait_ready(f"{self.endpoints.backend_url}/readyz", backend, 180)
        frontend_environment = dict(environment)
        frontend_environment["CORPUS_BACKEND_PROXY_URL"] = self.endpoints.backend_url
        frontend_log = (self.runtime_root / "frontend.log").open("wb")
        self._logs.append(frontend_log)
        node = shutil.which("node")
        if node is None:
            raise RuntimeError("Node.js is required for the isolated Corpus frontend.")
        frontend = subprocess.Popen(
            [
                node,
                str(
                    self.repository
                    / "frontend"
                    / "node_modules"
                    / "vite"
                    / "bin"
                    / "vite.js"
                ),
                "--host",
                "127.0.0.1",
                "--port",
                str(self.frontend_port),
                "--strictPort",
            ],
            cwd=self.repository / "frontend",
            env=frontend_environment,
            stdout=frontend_log,
            stderr=subprocess.STDOUT,
            creationflags=creation_flags,
        )
        self.processes.append(frontend)
        await _wait_ready(self.endpoints.frontend_url, frontend, 60)
        return self.endpoints

    async def close(self) -> None:
        for process in reversed(self.processes):
            if process.poll() is None:
                process.terminate()
        deadline = time.monotonic() + 10
        for process in reversed(self.processes):
            remaining = max(0.0, deadline - time.monotonic())
            try:
                process.wait(timeout=remaining)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        self.processes.clear()
        for log in self._logs:
            log.close()
        self._logs.clear()


async def _wait_ready(url: str, process: subprocess.Popen[bytes], timeout: float) -> None:
    import asyncio

    deadline = time.monotonic() + timeout
    async with httpx.AsyncClient(timeout=5.0) as client:
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError(
                    f"Isolated runtime process exited with code {process.returncode}."
                )
            try:
                response = await client.get(url)
                if response.is_success:
                    return
            except httpx.HTTPError:
                pass
            await asyncio.sleep(0.25)
    raise TimeoutError(f"Isolated runtime did not become ready at {url}.")


def _read_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


__all__ = ["IsolatedCorpusRuntime", "IsolatedRuntimeEndpoints"]
