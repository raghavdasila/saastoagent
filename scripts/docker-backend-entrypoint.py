from __future__ import annotations

import os
from pathlib import Path
import secrets
import subprocess
import sys

from cryptography.fernet import Fernet


DEFAULT_SECRET_PATH = Path("/data/docker-runtime-secrets.env")
SECRET_PATH_ENV = "CORPUS_DOCKER_SECRET_FILE"
MANAGED_SECRETS = (
    "ROUTEDECK_STATE_ENCRYPTION_KEY",
    "CORPUS_RESET_SECRET",
    "CORPUS_VERIFICATION_SECRET",
)


def _read_managed_secrets(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if not raw_line or raw_line.startswith("#") or "=" not in raw_line:
            continue
        name, value = raw_line.split("=", 1)
        if name in MANAGED_SECRETS and value:
            values[name] = value
    return values


def _new_secret(name: str) -> str:
    if name == "ROUTEDECK_STATE_ENCRYPTION_KEY":
        return Fernet.generate_key().decode("ascii")
    return secrets.token_urlsafe(48)


def ensure_runtime_secrets(path: Path) -> dict[str, str]:
    existing = _read_managed_secrets(path)
    resolved = {
        name: os.environ.get(name) or existing.get(name) or _new_secret(name)
        for name in MANAGED_SECRETS
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    temporary_path.write_text(
        "".join(f"{name}={resolved[name]}\n" for name in MANAGED_SECRETS),
        encoding="utf-8",
    )
    os.replace(temporary_path, path)
    try:
        path.chmod(0o600)
    except OSError:
        # Windows bind mounts may not expose POSIX permission changes.
        pass
    return resolved


def main(arguments: list[str]) -> None:
    if not arguments:
        raise SystemExit("A backend command is required.")

    secret_path = Path(os.environ.get(SECRET_PATH_ENV, str(DEFAULT_SECRET_PATH)))
    for name, value in ensure_runtime_secrets(secret_path).items():
        os.environ[name] = value

    print(f"Using persistent Docker development secrets from {secret_path}.")
    print("Running Corpus owner-auth migrations.")
    subprocess.run(
        [sys.executable, "-m", "corpus.auth.migrations"],
        check=True,
        env=os.environ,
    )
    print(f"Starting backend command: {' '.join(arguments)}")
    os.execvp(arguments[0], arguments)


if __name__ == "__main__":
    main(sys.argv[1:])

