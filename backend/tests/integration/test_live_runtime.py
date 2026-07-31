from __future__ import annotations

from pathlib import Path

import pytest
from cryptography.fernet import Fernet

from corpus.app.config import RouteDeckHostSettings
from corpus.auth.config import AuthSettings
from corpus.auth.operation_http import HttpCredentialTransition
from corpus.runtime.application import open_live_corpus_application
from corpus.runtime.config import CorpusRuntimeSettings
from corpus.features.sources.config import SourceSettings
from corpus.auth.service import OwnerRouteContext


class OwnerContextProbe:
    async def owner_context_for_route(self, route_session_id: str):
        del route_session_id
        return OwnerRouteContext(
            display_name="Owner",
            organization_name="Owner's Workspace",
            organization_slug="owner-workspace",
            role="owner",
            is_verified=False,
        )


@pytest.mark.asyncio
async def test_live_runtime_opens_workspace_and_proves_ollama_readiness(
    tmp_path: Path,
) -> None:
    settings = CorpusRuntimeSettings(
        host=RouteDeckHostSettings(
            routedeck_database_url=(
                f"sqlite+pysqlite:///{(tmp_path / 'corpus.sqlite3').as_posix()}"
            ),
            routedeck_state_encryption_key=Fernet.generate_key().decode("ascii"),
            routedeck_instance_id="corpus-integration-test",
            routedeck_review_ttl_seconds=300,
            routedeck_resume_capability_ttl_seconds=600,
            routedeck_worker_count=1,
            routedeck_browser_origins=("http://127.0.0.1:5199",),
        ),
        auth=AuthSettings(
            database_url=f"sqlite+aiosqlite:///{(tmp_path / 'auth.sqlite3').as_posix()}",
            migration_revision="0001_owner_auth",
            reset_secret="r" * 40,
            verification_secret="v" * 40,
            public_frontend_url="http://127.0.0.1:5199",
        ),
        sources=SourceSettings(data_root=tmp_path / "sources"),
        ollama_base_url="http://127.0.0.1:11434",
        ollama_model="gemma4:latest",
    )

    live = await open_live_corpus_application(
        settings,
        owner_context_resolver=OwnerContextProbe(),
        auth_service=object(),
        auth_limiter=object(),
        auth_mail=object(),
        credential_transition=HttpCredentialTransition(),
    )
    try:
        assert live.runtime.services.app.app.frontend_contract.entry_node_id == (
            "lounge.home"
        )
        assert await live.readiness.ready() is True
    finally:
        await live.close()
