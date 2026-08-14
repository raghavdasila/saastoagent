from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping


def openapi_document_hash(document: Mapping[str, Any]) -> str:
    """Return the stable canonical identity used for reviewed OpenAPI documents."""

    return hashlib.sha256(
        json.dumps(document, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


__all__ = ["openapi_document_hash"]
