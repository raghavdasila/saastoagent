from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.credentials import decrypt_value, inject_credentials
from backend.providers.base import AdapterRegistry, ConnectionAdapter, FieldDef
from backend.providers.rest.parser import (
    build_action_node_data,
    extract_endpoints,
    fetch_spec,
    parse_and_validate_spec,
)


@AdapterRegistry.register
class RestApiAdapter(ConnectionAdapter):
    provider_id = "rest_api"
    connection_type = "rest_api"
    display_name = "OpenAPI REST API"
    description = "Connect a REST API using an OpenAPI or Swagger specification."

    @classmethod
    def config_schema(cls) -> list[FieldDef]:
        return [
            FieldDef("base_url", "Base URL", required=True, placeholder="https://api.example.com"),
            FieldDef("spec_url", "OpenAPI Spec URL", required=True, placeholder="https://api.example.com/openapi.yaml"),
            FieldDef(
                "auth_type",
                "Auth Type",
                field_type="select",
                required=True,
                default="none",
                options=[
                    {"value": "none", "label": "No auth"},
                    {"value": "bearer", "label": "Bearer token"},
                    {"value": "api_key_header", "label": "API key header"},
                    {"value": "api_key_query", "label": "API key query param"},
                    {"value": "basic", "label": "Basic auth"},
                    {"value": "custom_header", "label": "Custom header"},
                ],
            ),
        ]

    @classmethod
    def credential_schema(cls) -> list[FieldDef]:
        return [
            FieldDef("credential_value", "Credential", field_type="password", placeholder="Token, API key, or user:pass"),
            FieldDef("header_name", "Header Name", placeholder="X-API-Key"),
            FieldDef("query_param_name", "Query Param Name", placeholder="api_key"),
        ]

    async def discover(self, connection: Any, session: AsyncSession) -> list[dict[str, Any]]:
        _ = session
        config = connection.config or {}
        spec_url = config.get("spec_url")
        if not spec_url:
            raise ValueError("REST API connection has no spec_url configured")

        headers: dict[str, str] = {}
        if connection.credentials:
            credential = connection.credentials[0]
            auth = await inject_credentials(
                auth_type=(connection.auth_type.value if hasattr(connection.auth_type, "value") else connection.auth_type),
                decrypted_value=decrypt_value(credential.encrypted_value),
                metadata=credential.metadata_,
            )
            headers.update(auth["headers"])

        raw = await fetch_spec(spec_url, headers=headers or None)
        spec = parse_and_validate_spec(raw)
        endpoints = extract_endpoints(spec)
        return [
            build_action_node_data(endpoint, connection.id, connection.saas_agent_id, spec_url)
            for endpoint in endpoints
        ]

    @classmethod
    def source_type(cls) -> str:
        return "openapi"
