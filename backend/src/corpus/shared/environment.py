from __future__ import annotations

import os
from collections.abc import Collection
from pathlib import Path


def read_environment(path: Path, names: Collection[str]) -> dict[str, str]:
    """Read only the requested names, with process values overriding the file."""
    allowed = frozenset(names)
    values: dict[str, str] = {}
    if path.is_file():
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            name, value = line.split("=", 1)
            name = name.strip()
            if name in allowed:
                values[name] = value.strip().strip('"').strip("'")
    values.update(
        {name: value for name, value in os.environ.items() if name in allowed}
    )
    return values


__all__ = ["read_environment"]
