from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import yaml  # type: ignore[import-untyped]


def _load_entrypoint() -> ModuleType:
    repository_root = Path(__file__).resolve().parents[3]
    script_path = repository_root / "scripts" / "docker-backend-entrypoint.py"
    spec = importlib.util.spec_from_file_location("docker_backend_entrypoint", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_runtime_secrets_are_complete_and_reused(tmp_path: Path) -> None:
    entrypoint = _load_entrypoint()
    secret_path = tmp_path / "docker-runtime-secrets.env"

    first = entrypoint.ensure_runtime_secrets(secret_path)
    second = entrypoint.ensure_runtime_secrets(secret_path)

    assert first == second
    assert set(first) == set(entrypoint.MANAGED_SECRETS)
    assert all(first.values())
    assert secret_path.is_file()


def test_environment_values_explicitly_override_persisted_values(
    tmp_path: Path, monkeypatch
) -> None:
    entrypoint = _load_entrypoint()
    secret_path = tmp_path / "docker-runtime-secrets.env"
    original = entrypoint.ensure_runtime_secrets(secret_path)
    replacement = "explicit-development-secret-value-that-is-long-enough"
    monkeypatch.setenv("CORPUS_RESET_SECRET", replacement)

    resolved = entrypoint.ensure_runtime_secrets(secret_path)

    assert resolved["CORPUS_RESET_SECRET"] == replacement
    assert resolved["CORPUS_VERIFICATION_SECRET"] == original[
        "CORPUS_VERIFICATION_SECRET"
    ]


def test_compose_backend_gracefully_cancels_active_runs_before_docker_kill() -> None:
    repository_root = Path(__file__).resolve().parents[3]
    compose = yaml.safe_load(
        (repository_root / "compose.yaml").read_text(encoding="utf-8")
    )
    backend = compose["services"]["backend"]
    command = backend["command"]
    timeout_index = command.index("--timeout-graceful-shutdown")

    uvicorn_timeout = int(command[timeout_index + 1])
    docker_stop_grace = int(backend["stop_grace_period"].removesuffix("s"))

    assert uvicorn_timeout == 5
    assert docker_stop_grace == 10
    assert uvicorn_timeout < docker_stop_grace
