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
    description_filename = upload.description_filename
    description_content = upload.description_content
    description_content_type = upload.description_content_type
    if any(
        value is not None
        for value in (
            description_filename,
            description_content,
            description_content_type,
        )
    ):
        if not description_filename or description_content is None:
            raise SourceUploadError(
                "The optional API description must include a Markdown file."
            )
        if (
            Path(description_filename).name != description_filename
            or any(separator in description_filename for separator in ("/", "\\"))
            or Path(description_filename).suffix.casefold() not in {".md", ".markdown"}
        ):
            raise SourceUploadError(
                "The optional API description must use a plain Markdown filename."
            )
        if not description_content:
            raise SourceUploadError("The optional API description is empty.")
        if len(description_content) > min(max_upload_bytes, 1024 * 1024):
            raise SourceUploadError(
                "The optional API description exceeds the 1 MiB upload limit."
            )
        media_type = (description_content_type or "").partition(";")[0].strip().casefold()
        if media_type not in {"", "application/octet-stream", "text/markdown", "text/plain"}:
            raise SourceUploadError(
                "The optional API description media type is unsupported."
            )
        try:
            description_content.decode("utf-8")
        except UnicodeDecodeError as error:
            raise SourceUploadError(
                "The optional API description must be valid UTF-8 Markdown."
            ) from error
        description_content_type = media_type
    return ValidatedSourceUpload(
        filename=filename,
        content_type=content_type,
        content=upload.content,
        description_filename=description_filename,
        description_content_type=description_content_type,
        description_content=description_content,
    )


__all__ = ["SourceUploadError", "validate_api_upload"]
