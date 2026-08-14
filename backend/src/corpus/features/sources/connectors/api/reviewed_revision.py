from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from corpus.shared.openapi import openapi_document_hash

from ...models import SourceState, SourceView


class ReviewedApiRevisionMismatch(RuntimeError):
    pass


def require_reviewed_contract_hash(
    source: SourceView, *, owner_key: str
) -> str:
    summary = source.revision.summary
    contract_hash = summary.get("final_canonical_sha256")
    if (
        source.connector_key != "api"
        or source.revision.state is not SourceState.READY
        or summary.get("revision_kind") != "reviewed_api_contract"
        or summary.get("approved_by_owner_id") != owner_key
        or not isinstance(contract_hash, str)
        or len(contract_hash) != 64
        or any(character not in "0123456789abcdef" for character in contract_hash)
    ):
        raise ReviewedApiRevisionMismatch(
            "The selected Source version is not an approved executable API version."
        )
    return contract_hash


def load_reviewed_document(
    source: SourceView,
    revision_dir: Path,
    *,
    owner_key: str,
) -> tuple[Mapping[str, Any], str]:
    contract_hash = require_reviewed_contract_hash(source, owner_key=owner_key)
    path = revision_dir / "i" / source.revision.original_filename
    try:
        content = path.read_bytes()
        document = json.loads(content)
    except (OSError, json.JSONDecodeError) as error:
        raise ReviewedApiRevisionMismatch(
            "The approved API definition is unavailable."
        ) from error
    if (
        hashlib.sha256(content).hexdigest() != source.revision.content_sha256
        or not isinstance(document, Mapping)
        or openapi_document_hash(document) != contract_hash
    ):
        raise ReviewedApiRevisionMismatch(
            "The selected API version no longer matches its approved identity."
        )
    return document, contract_hash


__all__ = [
    "ReviewedApiRevisionMismatch",
    "load_reviewed_document",
    "require_reviewed_contract_hash",
]
