from __future__ import annotations

import importlib.util
import json
import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


def read_env_file(path: Path | None) -> dict[str, str]:
    values: dict[str, str] = {}
    if path is None or not path.exists():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def resolve_config_path(value: str | None, base_dir: Path) -> Path | None:
    if not value:
        return None
    path = Path(value)
    return path if path.is_absolute() else (base_dir / path).resolve()


@dataclass
class LadderRuntimeConfig:
    env_file: Path | None = None
    openai_key_env: str = "STA_OPENAI_API_KEY"
    llm_model: str = "gpt-5-mini"
    embedding_model: str = "text-embedding-3-small"
    local_embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    dense_embedding_provider: str = "auto"
    embedding_batch_size: int = 128
    feedback_log: Path | None = Path("data/feedback_events.jsonl")
    cache_dir: Path = Path("artifacts/ladder_cache")
    gpu_enabled: str = "auto"
    gpu_device: str = "cuda:0"
    llm_mode: str = "auto"
    external_data: dict[str, Any] = field(default_factory=dict)
    _env_values: dict[str, str] = field(default_factory=dict, repr=False)

    @property
    def openai_api_key(self) -> str:
        return self._env_values.get(self.openai_key_env) or os.environ.get(self.openai_key_env, "")

    @property
    def openai_api_key_available(self) -> bool:
        return bool(self.openai_api_key)

    def sanitized_record(self) -> dict[str, Any]:
        return {
            "env_file": str(self.env_file) if self.env_file else None,
            "openai_key_env": self.openai_key_env,
            "openai_api_key_available": self.openai_api_key_available,
            "llm_model": self.llm_model,
            "embedding_model": self.embedding_model,
            "local_embedding_model": self.local_embedding_model,
            "dense_embedding_provider": self.dense_embedding_provider,
            "embedding_batch_size": self.embedding_batch_size,
            "feedback_log": str(self.feedback_log) if self.feedback_log else None,
            "cache_dir": str(self.cache_dir),
            "gpu_enabled": self.gpu_enabled,
            "gpu_device": self.gpu_device,
            "llm_mode": self.llm_mode,
            "external_data": self.external_data,
        }


def default_ladder_runtime_config(base_dir: Path | None = None) -> LadderRuntimeConfig:
    base = base_dir or Path.cwd()
    env_file = (base / ".env").resolve()
    config = LadderRuntimeConfig(
        env_file=env_file,
        feedback_log=Path("data/feedback_events.jsonl"),
        cache_dir=Path("artifacts/ladder_cache"),
    )
    config._env_values = read_env_file(env_file)
    return config


def load_ladder_runtime_config(path: Path | None, base_dir: Path | None = None) -> LadderRuntimeConfig:
    base = base_dir or Path.cwd()
    if path is None or not path.exists():
        config = default_ladder_runtime_config(base)
        config.cache_dir = (base / config.cache_dir).resolve() if not config.cache_dir.is_absolute() else config.cache_dir
        if config.feedback_log and not config.feedback_log.is_absolute():
            config.feedback_log = (base / config.feedback_log).resolve()
        return config
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        payload = {}
    config = default_ladder_runtime_config(base)
    config.env_file = resolve_config_path(payload.get("env_file"), base) or config.env_file
    config.openai_key_env = str(payload.get("openai_key_env", config.openai_key_env))
    config.llm_model = str(payload.get("llm_model", config.llm_model))
    config.embedding_model = str(payload.get("embedding_model", config.embedding_model))
    config.local_embedding_model = str(payload.get("local_embedding_model", config.local_embedding_model))
    config.dense_embedding_provider = str(payload.get("dense_embedding_provider", config.dense_embedding_provider))
    config.embedding_batch_size = int(payload.get("embedding_batch_size", config.embedding_batch_size))
    config.feedback_log = resolve_config_path(payload.get("feedback_log"), base) or config.feedback_log
    config.cache_dir = resolve_config_path(payload.get("cache_dir"), base) or config.cache_dir
    config.gpu_enabled = str(payload.get("gpu_enabled", config.gpu_enabled))
    config.gpu_device = str(payload.get("gpu_device", config.gpu_device))
    config.llm_mode = str(payload.get("llm_mode", config.llm_mode))
    external = payload.get("external_data", {})
    config.external_data = external if isinstance(external, dict) else {}
    config._env_values = read_env_file(config.env_file)
    return config


def package_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def hardware_probe(runtime: LadderRuntimeConfig | None = None) -> dict[str, Any]:
    runtime = runtime or default_ladder_runtime_config(Path.cwd())
    gpu = {"available": False, "name": None, "memory_total": None, "driver_version": None}
    try:
        completed = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
        if completed.returncode == 0 and completed.stdout.strip():
            first = completed.stdout.strip().splitlines()[0]
            parts = [part.strip() for part in first.split(",")]
            gpu = {
                "available": True,
                "name": parts[0] if len(parts) > 0 else None,
                "memory_total": parts[1] if len(parts) > 1 else None,
                "driver_version": parts[2] if len(parts) > 2 else None,
            }
    except Exception:
        pass
    packages = {
        name: package_available(name)
        for name in ["torch", "transformers", "sentence_transformers", "faiss", "sklearn", "openai", "datasets"]
    }
    selected_device = "cpu"
    fallback_reason = "GPU disabled or unavailable."
    if runtime.gpu_enabled != "false" and gpu["available"] and packages.get("torch"):
        selected_device = runtime.gpu_device
        fallback_reason = ""
    elif gpu["available"] and not packages.get("torch"):
        fallback_reason = "GPU detected, but torch is not installed."
    return {
        "gpu": gpu,
        "packages": packages,
        "selected_device": selected_device,
        "fallback_reason": fallback_reason,
    }


def write_hardware_probe_report(path: Path, probe: dict[str, Any]) -> None:
    gpu = probe.get("gpu", {})
    lines = [
        "# Hardware Probe",
        "",
        f"- GPU available: `{gpu.get('available')}`",
        f"- GPU name: `{gpu.get('name')}`",
        f"- GPU memory: `{gpu.get('memory_total')}`",
        f"- Driver: `{gpu.get('driver_version')}`",
        f"- Selected device: `{probe.get('selected_device')}`",
        f"- Fallback reason: `{probe.get('fallback_reason') or 'none'}`",
        "",
        "| Package | Available |",
        "|---|---:|",
    ]
    for name, available in sorted((probe.get("packages") or {}).items()):
        lines.append(f"| `{name}` | `{available}` |")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
