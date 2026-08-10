from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Mapping
from urllib.parse import quote, urlencode, urlsplit, urlunsplit

from .contracts import ExecutionRequest
from .errors import ContractError, RequestValidationError
from .plugins import PluginRegistry


_PATH_PARAMETER = re.compile(r"\{([^{}]+)\}")
_LOCATIONS = ("path", "query", "header", "cookie")


@dataclass(frozen=True)
class PreparedRequest:
    method: str
    url: str
    host_url: str
    path: str
    full_url_pattern: str
    headers: dict[str, str]
    query: dict[str, Any]
    cookies: dict[str, str]
    path_parameters: dict[str, Any]
    body: bytes | None
    content_type: str


def compile_request(
    request: ExecutionRequest,
    *,
    plugins: PluginRegistry,
) -> PreparedRequest:
    operation = request.operation
    connection = request.connection
    method = operation.method.strip().upper()
    if not method or not operation.path_template.startswith("/"):
        raise ContractError(
            "operation_contract_invalid",
            "The operation contract is invalid.",
        )

    _assert_declared_inputs(request)
    path = operation.path_template
    path_parameters = dict(request.inputs.path)
    for name in _PATH_PARAMETER.findall(operation.path_template):
        if name not in path_parameters:
            raise RequestValidationError(
                "required_input_missing",
                f"Required path input {name} is missing.",
            )
        path = path.replace("{" + name + "}", quote(str(path_parameters[name]), safe=""))
    if _PATH_PARAMETER.search(path):
        raise RequestValidationError(
            "required_input_missing",
            "One or more required path inputs are missing.",
        )

    parsed = urlsplit(connection.base_url)
    if parsed.query or parsed.fragment or not parsed.scheme or not parsed.netloc:
        raise ContractError(
            "connection_base_url_invalid",
            "The configured API base URL is invalid.",
        )
    base_path = parsed.path.rstrip("/")
    actual_path = base_path + path
    host_url = urlunsplit((parsed.scheme, parsed.netloc, "", "", ""))
    query = dict(request.inputs.query)
    query_text = urlencode(query, doseq=True)
    url = urlunsplit((parsed.scheme, parsed.netloc, actual_path, query_text, ""))
    full_url_pattern = urlunsplit(
        (parsed.scheme, parsed.netloc, base_path + operation.path_template, "", "")
    )

    body: bytes | None = None
    content_type = ""
    if request.inputs.body is not None:
        if operation.request_media_type is None:
            raise RequestValidationError(
                "request_body_not_declared",
                "The operation does not declare a request body.",
            )
        body, content_type = plugins.media(operation.request_media_type).encode(
            request.inputs.body
        )
        if len(body) > connection.network_policy.max_request_bytes:
            raise RequestValidationError(
                "request_too_large",
                "The encoded request exceeds the configured size limit.",
            )

    headers = {str(key): str(value) for key, value in request.inputs.header.items()}
    if content_type:
        headers["Content-Type"] = content_type
    cookies = {str(key): str(value) for key, value in request.inputs.cookie.items()}
    return PreparedRequest(
        method=method,
        url=url,
        host_url=host_url,
        path=actual_path,
        full_url_pattern=full_url_pattern,
        headers=headers,
        query=query,
        cookies=cookies,
        path_parameters=path_parameters,
        body=body,
        content_type=content_type,
    )


def _assert_declared_inputs(request: ExecutionRequest) -> None:
    declared: dict[str, set[str]] = {location: set() for location in _LOCATIONS}
    required: dict[str, set[str]] = {location: set() for location in _LOCATIONS}
    managed: dict[str, set[str]] = {location: set() for location in _LOCATIONS}
    for parameter in request.operation.parameters:
        if parameter.location not in declared:
            raise ContractError(
                "parameter_location_unsupported",
                f"Parameter location {parameter.location} is unsupported.",
            )
        declared[parameter.location].add(parameter.name)
        if parameter.managed_by_auth:
            managed[parameter.location].add(parameter.name)
        elif parameter.required:
            required[parameter.location].add(parameter.name)

    supplied: Mapping[str, Mapping[str, Any]] = {
        "path": request.inputs.path,
        "query": request.inputs.query,
        "header": request.inputs.header,
        "cookie": request.inputs.cookie,
    }
    for location, values in supplied.items():
        forbidden = sorted(set(values) & managed[location])
        if forbidden:
            raise RequestValidationError(
                "credential_input_forbidden",
                f"Credential-managed {location} inputs cannot be supplied directly: {forbidden}.",
            )
        unknown = sorted(set(values) - declared[location])
        if unknown:
            raise RequestValidationError(
                "undeclared_input",
                f"Undeclared {location} inputs were supplied: {unknown}.",
            )
        missing = sorted(required[location] - set(values))
        if missing:
            raise RequestValidationError(
                "required_input_missing",
                f"Required {location} inputs are missing: {missing}.",
            )
