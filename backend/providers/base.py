from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession


@dataclass(frozen=True)
class FieldDef:
    key: str
    label: str
    field_type: str = "text"
    required: bool = False
    placeholder: str = ""
    default: Any = None
    options: list[dict[str, str]] | None = None
    help_text: str = ""


class ConnectionAdapter(ABC):
    provider_id = ""
    connection_type = ""
    display_name = ""
    description = ""

    @classmethod
    @abstractmethod
    def config_schema(cls) -> list[FieldDef]:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def credential_schema(cls) -> list[FieldDef]:
        raise NotImplementedError

    @abstractmethod
    async def discover(self, connection: Any, session: AsyncSession) -> list[dict[str, Any]]:
        raise NotImplementedError

    @classmethod
    def source_type(cls) -> str:
        return cls.provider_id


class AdapterRegistry:
    _adapters: dict[str, type[ConnectionAdapter]] = {}

    @classmethod
    def register(cls, adapter: type[ConnectionAdapter]) -> type[ConnectionAdapter]:
        if not adapter.provider_id:
            raise ValueError(f"{adapter.__name__} has no provider_id")
        cls._adapters[adapter.provider_id] = adapter
        return adapter

    @classmethod
    def get(cls, provider_id: str) -> type[ConnectionAdapter]:
        adapter = cls._adapters.get(provider_id)
        if adapter is None:
            raise ValueError(f"No adapter registered for provider: {provider_id}")
        return adapter

    @classmethod
    def get_provider_catalog(cls) -> dict[str, list[dict[str, Any]]]:
        catalog: dict[str, list[dict[str, Any]]] = {}
        for adapter in cls._adapters.values():
            catalog.setdefault(adapter.connection_type, []).append(
                {
                    "id": adapter.provider_id,
                    "name": adapter.display_name,
                    "description": adapter.description,
                    "config_schema": [_field_to_dict(f) for f in adapter.config_schema()],
                    "credential_schema": [_field_to_dict(f) for f in adapter.credential_schema()],
                }
            )
        return catalog


def _field_to_dict(field: FieldDef) -> dict[str, Any]:
    return {
        "key": field.key,
        "label": field.label,
        "type": field.field_type,
        "required": field.required,
        "placeholder": field.placeholder,
        "default": field.default,
        "options": field.options,
        "help_text": field.help_text,
    }
