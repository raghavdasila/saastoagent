from __future__ import annotations

import argparse
import asyncio
import os
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

import httpx
from cryptography.fernet import Fernet

from corpus.auth.config import AuthSettings
from corpus.persistence.migrations import upgrade_database
from scripts.smoke_restart_recovery import _prepare, _verify


_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_LOOPBACK_HOST = "127.0.0.1"


@dataclass(frozen=True)
class IsolatedRuntime:
    directory: Path
    database_url: str
    migration_revision: str
    routedeck_database_url: str
    state_file: Path
    log_file: Path
    base_url: str
    origin: str
    environment: dict[str, str]


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Prove Corpus restart recovery in a disposable local runtime that "
            "owns both the Corpus domain and RouteDeck runtime databases."
        )
    )
    parser.add_argument(
        "--port",
        type=int,
        default=0,
        help="Unused loopback port; zero selects an available port.",
    )
    arguments = parser.parse_args()
    runtime = create_isolated_runtime(port=arguments.port)
    process: subprocess.Popen[bytes] | None = None
    succeeded = False
    try:
        asyncio.run(upgrade_database(runtime.database_url))
        settings = AuthSettings.from_env()

        process = start_backend(runtime)
        wait_until_ready(runtime, process)
        _prepare(
            runtime.base_url,
            runtime.origin,
            runtime.state_file,
            settings=settings,
            database_url=runtime.database_url,
            migration_revision=runtime.migration_revision,
        )

        stop_backend(process)
        process = start_backend(runtime)
        wait_until_ready(runtime, process)
        _verify(
            runtime.base_url,
            runtime.origin,
            runtime.state_file,
            settings=settings,
            database_url=runtime.database_url,
            migration_revision=runtime.migration_revision,
        )
        succeeded = True
    finally:
        if process is not None:
            stop_backend(process)
        if succeeded:
            remove_isolated_runtime(runtime)
        else:
            print(
                "Isolated restart smoke failed; retained owned runtime at "
                f"{runtime.directory}",
                file=sys.stderr,
            )
            print(f"Backend log: {runtime.log_file}", file=sys.stderr)

    print("Isolated Corpus restart recovery smoke passed.")
    print(
        "runtime=disposable corpus_database=removed "
        "routedeck_database=removed normal_runtime=untouched"
    )


def create_isolated_runtime(*, port: int = 0) -> IsolatedRuntime:
    if port == 0:
        port = _available_loopback_port()
    if not 1 <= port <= 65535:
        raise ValueError("The isolated runtime port must be between 1 and 65535.")

    directory = Path(tempfile.mkdtemp(prefix="corpus-restart-smoke-"))
    database_path = directory / "corpus.sqlite3"
    routedeck_path = directory / "routedeck.sqlite"
    source_path = directory / "sources"
    origin = f"http://{_LOOPBACK_HOST}:{port + 1 if port < 65535 else port - 1}"
    base_url = f"http://{_LOOPBACK_HOST}:{port}"
    environment = os.environ.copy()
    existing_python_path = environment.get("PYTHONPATH")
    backend_source = str(_PROJECT_ROOT / "backend" / "src")
    environment["PYTHONPATH"] = (
        os.pathsep.join((backend_source, existing_python_path))
        if existing_python_path
        else backend_source
    )
    environment.update(
        {
            "ROUTEDECK_DATABASE_URL": _sqlite_url(routedeck_path, driver="pysqlite"),
            "ROUTEDECK_STATE_ENCRYPTION_KEY": Fernet.generate_key().decode("ascii"),
            "ROUTEDECK_INSTANCE_ID": f"restart-smoke-{uuid4().hex}",
            "ROUTEDECK_BROWSER_ORIGINS": origin,
            "ROUTEDECK_WORKER_COUNT": "1",
            "CORPUS_DATABASE_URL": _sqlite_url(database_path, driver="aiosqlite"),
            "CORPUS_MIGRATION_REVISION": "0006_restrict_agent_attachment_delete",
            "CORPUS_RESET_SECRET": Fernet.generate_key().decode("ascii"),
            "CORPUS_VERIFICATION_SECRET": Fernet.generate_key().decode("ascii"),
            "CORPUS_PUBLIC_FRONTEND_URL": origin,
            "CORPUS_SOURCE_DATA_ROOT": str(source_path),
        }
    )
    return IsolatedRuntime(
        directory=directory,
        database_url=environment["CORPUS_DATABASE_URL"],
        migration_revision=environment["CORPUS_MIGRATION_REVISION"],
        routedeck_database_url=environment["ROUTEDECK_DATABASE_URL"],
        state_file=directory / "restart-state.json",
        log_file=directory / "backend.log",
        base_url=base_url,
        origin=origin,
        environment=environment,
    )


def start_backend(runtime: IsolatedRuntime) -> subprocess.Popen[bytes]:
    command = (
        sys.executable,
        "-m",
        "uvicorn",
        "corpus.main:create_live_app",
        "--factory",
        "--host",
        _LOOPBACK_HOST,
        "--port",
        runtime.base_url.rsplit(":", maxsplit=1)[1],
        "--timeout-graceful-shutdown",
        "5",
    )
    creation_flags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    log_stream = runtime.log_file.open("ab")
    try:
        process = subprocess.Popen(
            command,
            cwd=_PROJECT_ROOT,
            env=runtime.environment,
            stdout=log_stream,
            stderr=subprocess.STDOUT,
            creationflags=creation_flags,
        )
    finally:
        log_stream.close()
    return process


def wait_until_ready(
    runtime: IsolatedRuntime,
    process: subprocess.Popen[bytes],
    *,
    timeout_seconds: float = 180.0,
) -> None:
    deadline = time.monotonic() + timeout_seconds
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        return_code = process.poll()
        if return_code is not None:
            raise RuntimeError(
                f"The isolated backend exited with code {return_code}; "
                f"inspect {runtime.log_file}."
            )
        try:
            response = httpx.get(f"{runtime.base_url}/readyz", timeout=2.0)
            if response.is_success:
                return
            last_error = RuntimeError(
                f"Readiness returned HTTP {response.status_code}."
            )
        except httpx.HTTPError as error:
            last_error = error
        time.sleep(0.25)
    raise RuntimeError(
        f"The isolated backend did not become ready: {last_error}; "
        f"inspect {runtime.log_file}."
    )


def stop_backend(
    process: subprocess.Popen[bytes], *, timeout_seconds: float = 15.0
) -> None:
    if process.poll() is not None:
        return
    if os.name == "nt":
        process.send_signal(signal.CTRL_BREAK_EVENT)
    else:
        process.terminate()
    try:
        process.wait(timeout=timeout_seconds)
    except subprocess.TimeoutExpired as error:
        process.kill()
        process.wait(timeout=5.0)
        raise RuntimeError(
            "The isolated backend did not stop gracefully and was force-killed."
        ) from error


def remove_isolated_runtime(runtime: IsolatedRuntime) -> None:
    directory = runtime.directory.resolve()
    expected_prefix = "corpus-restart-smoke-"
    if directory.parent != Path(tempfile.gettempdir()).resolve() or not (
        directory.name.startswith(expected_prefix)
    ):
        raise RuntimeError(
            f"Refusing to remove an unowned runtime directory: {directory}"
        )
    shutil.rmtree(directory)


def _available_loopback_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind((_LOOPBACK_HOST, 0))
        return int(listener.getsockname()[1])


def _sqlite_url(path: Path, *, driver: str) -> str:
    return f"sqlite+{driver}:///{path.resolve().as_posix()}"


if __name__ == "__main__":
    main()
