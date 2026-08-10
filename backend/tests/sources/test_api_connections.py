from __future__ import annotations

import asyncio
import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

from corpus.credentials import SecretBoxCredentialVault
from corpus.features.sources.connectors.api.connections import (
    ApiAuthenticationMethod,
    ApiConnectionConflict,
    ApiConnectionPrivateForm,
    ApiConnectionProfileRepository,
    ApiConnectionService,
)
from corpus.features.sources.declarations import API_CONNECTION_FORM_ID
from corpus.features.sources.operations import SaveApiConnectionHandler
from corpus.features.sources.repository import LocalSourceRepository
from corpus.persistence import CorpusDatabase
from corpus.auth.models import Organization


class RecordingPrivateForms:
    def __init__(self, value: ApiConnectionPrivateForm) -> None:
        self.value = value
        self.calls: list[tuple[str, str, type]] = []

    async def load(self, session_id: str, form_id: str, model: type):
        self.calls.append((session_id, form_id, model))
        return self.value


class RecordingConnectionService:
    def __init__(self) -> None:
        self.saved: list[tuple[uuid.UUID, ApiConnectionPrivateForm]] = []

    async def save(
        self,
        *,
        owner_id: uuid.UUID,
        value: ApiConnectionPrivateForm,
    ) -> None:
        self.saved.append((owner_id, value))


class FixedOwnerScope:
    def __init__(self, owner_id: uuid.UUID) -> None:
        self.owner_id = owner_id

    async def organization_id_for_route(self, session_id: str) -> uuid.UUID:
        assert session_id == "source-session"
        return self.owner_id


def test_api_connection_persists_only_an_encrypted_credential_reference(
    tmp_path: Path,
) -> None:
    asyncio.run(_exercise_connection(tmp_path))


def test_save_handler_loads_secret_from_private_form_and_rejects_public_values() -> None:
    asyncio.run(_exercise_private_form_handler())


async def _exercise_private_form_handler() -> None:
    owner_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    secret = "handler-private-api-key"
    private_value = ApiConnectionPrivateForm(
        source_id="sourceopaque0001",
        profile_name="Production",
        environment="production",
        base_url="https://api.example.com/v1",
        authentication_method=ApiAuthenticationMethod.API_KEY,
        credential_name="X-API-Key",
        credential_value=secret,
    )
    private_forms = RecordingPrivateForms(private_value)
    service = RecordingConnectionService()
    handler = SaveApiConnectionHandler(
        service=service,  # type: ignore[arg-type]
        owner_scope=FixedOwnerScope(owner_id),  # type: ignore[arg-type]
        private_forms=private_forms,  # type: ignore[arg-type]
    )
    context = SimpleNamespace(
        session_id="source-session",
        attempt_id="source-attempt",
        request_id="source-request",
    )

    rejected = await handler(
        {"credential_value": secret},
        context,  # type: ignore[arg-type]
    )
    assert rejected.failure is not None
    assert rejected.failure.code == "invalid_api_connection_save"
    assert private_forms.calls == []
    assert service.saved == []
    assert secret not in json.dumps(rejected.model_dump(mode="json"))

    saved = await handler({}, context)  # type: ignore[arg-type]

    assert saved.outcome == "saved"
    assert saved.failure is None
    assert saved.effects.remove_private_form_ids == (API_CONNECTION_FORM_ID,)
    assert private_forms.calls == [
        (
            "source-session",
            API_CONNECTION_FORM_ID,
            ApiConnectionPrivateForm,
        )
    ]
    assert service.saved == [(owner_id, private_value)]
    assert secret not in json.dumps(saved.model_dump(mode="json"))


async def _exercise_connection(tmp_path: Path) -> None:
    database = CorpusDatabase(
        f"sqlite+aiosqlite:///{(tmp_path / 'domain.sqlite3').as_posix()}"
    )
    await database.create_schema_for_tests()
    try:
        owner_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
        async with database.session() as session:
            async with session.begin():
                session.add(
                    Organization(
                        id=owner_id,
                        name="Connection Owner",
                        slug="connection-owner",
                        created_at=datetime.now(UTC),
                    )
                )
        sources = LocalSourceRepository(tmp_path / "sources")
        prepared = sources.begin_source(
            owner_key=str(owner_id),
            connector_key="api",
            display_name="Catalog",
            original_filename="catalog.yaml",
            content=b"openapi: 3.0.3\npaths: {}\n",
        )
        profiles = ApiConnectionProfileRepository(sources)
        vault = SecretBoxCredentialVault(database, b"k" * 32)
        service = ApiConnectionService(profiles, vault)
        secret = "corpus-test-secret-value"

        created = await service.save(
            owner_id=owner_id,
            value=ApiConnectionPrivateForm(
                source_id=prepared.source.source_id,
                profile_name="Production",
                environment="production",
                base_url="https://api.example.com/v1",
                authentication_method=ApiAuthenticationMethod.API_KEY,
                credential_name="X-API-Key",
                credential_value=secret,
            ),
        )

        assert created.revision_id == prepared.revision.revision_id
        assert created.base_url == "https://api.example.com/v1"
        assert created.credential_reference_id is not None
        resolved = await vault.resolve(
            owner_id=owner_id,
            credential_id=created.credential_reference_id,
        )
        assert resolved.values == {
            "header_name": "X-API-Key",
            "value": secret,
        }
        public_json = created.model_dump_json()
        stored_json = (
            prepared.input_path.parents[1] / "connections.json"
        ).read_text(encoding="utf-8")
        assert secret not in public_json
        assert secret not in stored_json
        assert "credential_reference_id" in stored_json

        try:
            await service.save(
                owner_id=owner_id,
                value=ApiConnectionPrivateForm(
                    source_id=prepared.source.source_id,
                    profile_name="Production",
                    environment="production",
                    base_url="https://api.example.com/v1",
                    authentication_method=ApiAuthenticationMethod.NONE,
                ),
            )
        except ApiConnectionConflict:
            pass
        else:
            raise AssertionError("Duplicate connection profile must fail.")
        assert len(profiles.list(owner_key=str(owner_id), source_id=prepared.source.source_id)) == 1
    finally:
        await database.close()
