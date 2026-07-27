from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any


def write_json_atomic(
    path: Path,
    value: Any,
    *,
    replace_attempts: int = 20,
    retry_delay_seconds: float = 0.05,
) -> None:
    if replace_attempts < 1:
        raise ValueError("replace_attempts must be at least 1")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + f".{os.getpid()}.tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True), encoding="utf-8")
    try:
        for attempt in range(replace_attempts):
            try:
                os.replace(temporary, path)
                return
            except PermissionError:
                if attempt + 1 >= replace_attempts:
                    raise
                time.sleep(retry_delay_seconds)
    finally:
        if temporary.exists():
            temporary.unlink()
