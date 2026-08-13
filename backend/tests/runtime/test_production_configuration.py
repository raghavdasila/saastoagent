from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[3]


def _compose() -> dict:
    return yaml.safe_load((ROOT / "compose.production.yaml").read_text(encoding="utf-8"))


def test_production_compose_has_only_the_runtime_services() -> None:
    compose = _compose()
    services = compose["services"]

    assert set(services) == {"web", "backend", "worker"}
    assert "--reload" not in services["backend"]["command"]
    assert "ports" not in services["backend"]
    assert "ports" not in services["worker"]
    assert services["backend"]["environment"]["ROUTEDECK_WORKER_COUNT"] == "1"
    assert all(service["restart"] == "unless-stopped" for service in services.values())
    assert all(".env.local" not in str(service.get("env_file", "")) for service in services.values())


def test_backend_and_worker_share_only_the_declared_persistent_roots() -> None:
    services = _compose()["services"]
    for name in ("backend", "worker"):
        mounts = services[name]["volumes"]
        assert "/srv/corpus/state:/srv/corpus/state" in mounts
        assert "/srv/corpus/data:/srv/corpus/data" in mounts


def test_production_openai_and_public_origin_are_explicit() -> None:
    environment = _compose()["services"]["backend"]["environment"]

    assert environment["CORPUS_MODEL_PROVIDER"] == "openai"
    assert environment["CORPUS_OPENAI_MODEL"] == "gpt-5.6-luna"
    assert environment["CORPUS_OPENAI_REASONING_EFFORT"] == "low"
    assert environment["CORPUS_PUBLIC_FRONTEND_URL"] == "https://corpus.saastoagent.com"
    assert environment["ROUTEDECK_BROWSER_ORIGINS"] == "https://corpus.saastoagent.com"


def test_caddy_is_the_only_public_listener_and_routes_backend_paths() -> None:
    compose = _compose()
    assert compose["services"]["web"]["ports"] == ["80:80", "443:443"]

    caddyfile = (ROOT / "deploy" / "Caddyfile").read_text(encoding="utf-8")
    assert "corpus.saastoagent.com" in caddyfile
    assert "reverse_proxy backend:8099" in caddyfile
    assert "try_files {path} /index.html" in caddyfile
    assert "Content-Security-Policy" in caddyfile
    assert "max_size 20MB" in caddyfile


def test_production_images_are_immutable_runtime_targets() -> None:
    dockerfile = (ROOT / "Dockerfile.production").read_text(encoding="utf-8")

    assert "AS backend-runtime" in dockerfile
    assert "AS web-runtime" in dockerfile
    assert "USER corpus" in dockerfile
    assert "backend[testing]" not in dockerfile
    assert ".env.local" not in dockerfile
