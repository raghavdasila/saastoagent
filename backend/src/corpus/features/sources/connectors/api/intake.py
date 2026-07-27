from __future__ import annotations

from pathlib import Path

import yaml

from ..base import SourceUpload, ValidatedSourceUpload


class SourceUploadError(ValueError):
    pass


def validate_api_upload(
    upload: SourceUpload,
    *,
    max_upload_bytes: int,
) -> ValidatedSourceUpload:
    filename = upload.filename.strip()
    if (
        not filename
        or Path(filename).name != filename
        or any(separator in filename for separator in ("/", "\\"))
    ):
        raise SourceUploadError("The upload must use a plain filename.")
    if Path(filename).suffix.casefold() not in {".json", ".yaml", ".yml"}:
        raise SourceUploadError("API collections must be JSON, YAML, or YML files.")
    if not upload.content:
        raise SourceUploadError("The API collection upload is empty.")
    if len(upload.content) > max_upload_bytes:
        raise SourceUploadError(
            f"The API collection exceeds the {max_upload_bytes} byte upload limit."
        )
    allowed_media = {
        "",
        "application/json",
        "application/octet-stream",
        "application/x-yaml",
        "application/yaml",
        "text/x-yaml",
        "text/yaml",
    }
    content_type = upload.content_type.partition(";")[0].strip().casefold()
    if content_type not in allowed_media:
        raise SourceUploadError(
            f"The API collection media type is unsupported: {upload.content_type}"
        )
    try:
        parsed = yaml.safe_load(upload.content.decode("utf-8"))
    except (UnicodeDecodeError, yaml.YAMLError) as error:
        raise SourceUploadError(
            f"The API collection is not valid UTF-8 JSON/YAML: {error}"
        ) from error
    if not isinstance(parsed, dict):
        raise SourceUploadError("The API collection must parse to an object.")
    if not str(parsed.get("openapi") or parsed.get("swagger") or "").strip():
        raise SourceUploadError(
            "The API collection must declare an OpenAPI or Swagger version."
        )
    return ValidatedSourceUpload(
        filename=filename,
        content_type=content_type,
        content=upload.content,
    )


__all__ = ["SourceUploadError", "validate_api_upload"]

