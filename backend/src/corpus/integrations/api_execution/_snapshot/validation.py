from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Mapping

from openapi_core import OpenAPI
from openapi_core.datatypes import RequestParameters

from .compiler import PreparedRequest
from .contracts import ValidationIssue


@dataclass(frozen=True)
class DetailedValidationIssue:
    phase: str
    message: str
    instance_path: str
    error_type: str


@dataclass
class OpenAPICoreRequest:
    prepared: PreparedRequest

    @property
    def host_url(self) -> str:
        return self.prepared.host_url

    @property
    def path(self) -> str:
        return self.prepared.path

    @property
    def full_url_pattern(self) -> str:
        return self.prepared.full_url_pattern

    @property
    def method(self) -> str:
        return self.prepared.method.lower()

    @property
    def body(self) -> bytes | None:
        return self.prepared.body

    @property
    def content_type(self) -> str:
        return self.prepared.content_type.lower()

    @property
    def parameters(self) -> RequestParameters:
        return RequestParameters(
            query=self.prepared.query,
            header=self.prepared.headers,
            cookie=self.prepared.cookies,
            path=self.prepared.path_parameters,
        )


@dataclass(frozen=True)
class OpenAPICoreResponse:
    status_code: int
    content_type: str
    headers: Mapping[str, Any]
    data: bytes | None


class OpenAPIValidator:
    def __init__(self) -> None:
        self._cache: dict[tuple[str, str], OpenAPI] = {}

    def api(
        self,
        document_hash: str,
        document: Mapping[str, Any],
        server_url: str,
    ) -> OpenAPI:
        key = (document_hash, server_url.rstrip("/"))
        value = self._cache.get(key)
        if value is None:
            configured = dict(document)
            configured["servers"] = [{"url": key[1]}]
            value = OpenAPI.from_dict(configured)
            self._cache[key] = value
        return value

    def request_issues(
        self,
        document_hash: str,
        document: Mapping[str, Any],
        prepared: PreparedRequest,
        server_url: str,
    ) -> tuple[ValidationIssue, ...]:
        api = self.api(document_hash, document, server_url)
        return tuple(
            ValidationIssue(phase="request", message=str(error))
            for error in api.iter_request_errors(OpenAPICoreRequest(prepared))
        )

    def response_issues(
        self,
        document_hash: str,
        document: Mapping[str, Any],
        prepared: PreparedRequest,
        server_url: str,
        *,
        status_code: int,
        content_type: str,
        headers: Mapping[str, Any],
        body: bytes,
    ) -> tuple[ValidationIssue, ...]:
        api = self.api(document_hash, document, server_url)
        request = OpenAPICoreRequest(prepared)
        response = OpenAPICoreResponse(
            status_code=status_code,
            content_type=content_type.lower(),
            headers=headers,
            data=body,
        )
        return tuple(
            ValidationIssue(phase="response", message=str(error))
            for error in api.iter_response_errors(request, response)
        )

    def response_issue_details(
        self,
        document_hash: str,
        document: Mapping[str, Any],
        prepared: PreparedRequest,
        server_url: str,
        *,
        status_code: int,
        content_type: str,
        headers: Mapping[str, Any],
        body: bytes,
    ) -> tuple[DetailedValidationIssue, ...]:
        api = self.api(document_hash, document, server_url)
        request = OpenAPICoreRequest(prepared)
        response = OpenAPICoreResponse(
            status_code=status_code,
            content_type=content_type.lower(),
            headers=headers,
            data=body,
        )
        details: list[DetailedValidationIssue] = []
        for error in api.iter_response_errors(request, response):
            value = getattr(error, "details", None)
            schema_errors = value.get("schema_errors", []) if isinstance(value, dict) else []
            if schema_errors:
                for schema_error in schema_errors:
                    details.append(
                        DetailedValidationIssue(
                            phase="response",
                            message=str(schema_error.get("message") or "Response schema mismatch"),
                            instance_path=_detail_instance_path(
                                schema_error.get("path") or [],
                                str(schema_error.get("message") or ""),
                            ),
                            error_type=str(value.get("cause_type") or value.get("error_type") or type(error).__name__),
                        )
                    )
            else:
                details.append(
                    DetailedValidationIssue(
                        phase="response",
                        message=str(error),
                        instance_path="/",
                        error_type=type(error).__name__,
                    )
                )
        return tuple(details)


def _instance_path(parts: list[Any]) -> str:
    if not parts:
        return "/"
    return "/" + "/".join(
        str(part).replace("~", "~0").replace("/", "~1") for part in parts
    )


def _detail_instance_path(parts: list[Any], message: str) -> str:
    resolved = list(parts)
    if message.endswith("is a required property") and message.startswith("'"):
        segments = message.split("'")
        if len(segments) >= 3 and segments[1]:
            resolved.append(segments[1])
    return _instance_path(resolved)
