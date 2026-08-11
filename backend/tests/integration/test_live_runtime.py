from __future__ import annotations

from pathlib import Path
import base64

import pytest
from cryptography.fernet import Fernet

from corpus.app.config import RouteDeckHostSettings
from corpus.app.infrastructure import SharedInfrastructureSettings
from corpus.credentials import CredentialVaultSettings
from corpus.jobs import DurableJobSettings
from corpus.auth.config import AuthSettings
from corpus.auth.operation_http import HttpCredentialTransition
from corpus.runtime.application import open_live_corpus_application
from corpus.runtime.config import CorpusRuntimeSettings
from corpus.features.sources.config import SourceSettings
from corpus.persistence import CorpusDatabaseSettings
from corpus.auth.contracts import OwnerRouteContext


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
        database=CorpusDatabaseSettings(
            url=f"sqlite+aiosqlite:///{(tmp_path / 'corpus-domain.sqlite3').as_posix()}",
            migration_revision="0015_builder_retry_attempts",
        ),
        auth=AuthSettings(
            reset_secret="r" * 40,
            verification_secret="v" * 40,
            public_frontend_url="http://127.0.0.1:5199",
        ),
        sources=SourceSettings(data_root=tmp_path / "sources"),
        infrastructure=SharedInfrastructureSettings(
            jobs=DurableJobSettings(sqlite_path=tmp_path / "jobs.sqlite3"),
            credentials=CredentialVaultSettings(
                encoded_key=base64.urlsafe_b64encode(b"k" * 32).decode("ascii")
            ),
        ),
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
        agent_service=object(),
        designer_service=object(),
        builder_service=object(),
        sandbox_service=object(),
        evaluation_service=object(),
        channel_service=object(),
        deployment_service=object(),
        operations_service=object(),
        workspace_service=object(),
        source_service=object(),
        source_graph_presenter=object(),
        source_connection_service=object(),
        source_contract_revision_service=object(),
        source_connection_check_service=object(),
        source_operation_curation_service=object(),
        source_routed_execution_service=object(),
    )
    try:
        assert live.runtime.services.app.app.frontend_contract.entry_node_id == (
            "lounge.home"
        )
        assert await live.readiness.ready() is True
    finally:
        await live.close()
