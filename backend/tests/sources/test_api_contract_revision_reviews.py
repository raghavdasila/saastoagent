from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
import uuid

import pytest
from cryptography.fernet import Fernet
from pydantic import BaseModel
from routedeck_core.contracts.operations import (
    OperationDisposition,
    OperationRequest,
    OperationSource,
)
from routedeck_core.contracts.projection import FrozenJsonObject
from routedeck_sqlalchemy import open_sqlalchemy_routedeck_runtime

from corpus.auth.contracts import OwnerRouteContext
from corpus.bindings import bind_corpus_app
from corpus.composition import compile_corpus_app
from corpus.features.sources.connectors.api.contract_revisions import proposal_public_ref
from corpus.integrations.medusa_acceptance import MedusaContractAcceptanceAdapter
from corpus.session import create_guest_session, create_owner_session, initialize_guest_session

from backend.tests.sources.test_api_contract_revisions import OWNER, _ready_fixture


@dataclass
class RuntimeOwnerProbe:
    organization_id: uuid.UUID

    async def organization_id_for_route(self, route_session_id: str) -> uuid.UUID:
        if not route_session_id.startswith("source-review-"):
            raise RuntimeError("unexpected route session")
        return self.organization_id

    async def owner_context_for_route(self, route_session_id: str) -> OwnerRouteContext:
        await self.organization_id_for_route(route_session_id)
        return OwnerRouteContext(
            display_name="Owner",
            organization_name="Review Workspace",
            organization_slug="review-workspace",
            role="owner",
            is_verified=True,
        )


class WorkspaceProjection(BaseModel):
    active_agent_count: int = 0
    source_count: int = 1


class WorkspaceProbe:
    async def for_route(self, route_session_id: str) -> WorkspaceProjection:
        if not route_session_id.startswith("source-review-"):
            raise RuntimeError("unexpected route session")
        return WorkspaceProjection()


class SequentialIds:
    def __init__(self) -> None:
        self.value = 0

    def __call__(self, kind: str) -> str:
        self.value += 1
        return f"{kind}-source-contract-{self.value}"


@pytest.mark.asyncio
async def test_contract_revision_review_is_durable_rejects_without_mutation_and_rechecks(
    tmp_path: Path,
) -> None:
    repository, source, plan = _ready_fixture(tmp_path)
    service = MedusaContractAcceptanceAdapter(repository, plan=plan)
    owner = RuntimeOwnerProbe(OWNER)
    compiled = compile_corpus_app()
    database_url = f"sqlite+pysqlite:///{(tmp_path / 'routedeck.sqlite3').as_posix()}"
    encryption_key = Fernet.generate_key().decode("ascii")
    ids = SequentialIds()

    async def open_runtime(instance_id: str):
        return await open_sqlalchemy_routedeck_runtime(
            compiled_app=compiled,
            application_factory=lambda resources: bind_corpus_app(
                compiled,
                owner,
                auth_service=owner,
                auth_limiter=object(),
                auth_mail=object(),
                auth_settings=SimpleNamespace(
                    public_frontend_url="http://127.0.0.1:5199"
                ),
                private_form_store=resources.store,
                private_form_codec=resources.codec,
                credential_transition=object(),
                agent_service=object(),
                designer_service=object(),
                builder_service=object(),
                sandbox_service=object(),
                evaluation_service=object(),
                channel_service=object(),
                deployment_service=object(),
                operations_service=object(),
                workspace_service=WorkspaceProbe(),
                source_service=SimpleNamespace(
                    repository=repository,
                    get_source=lambda *, owner_key, source_id, revision_id=None: (
                        repository.get(owner_key=owner_key, source_id=source_id)
                        if revision_id is None
                        else repository.get_revision(
                            owner_key=owner_key,
                            source_id=source_id,
                            revision_id=revision_id,
                        )
                    ),
                ),
                source_graph_presenter=object(),
                source_connection_service=object(),
                    source_contract_revision_service=service,
                    source_connection_check_service=object(),
                    source_operation_curation_service=object(),
            ),
            session_factory=create_guest_session,
            session_initializer=initialize_guest_session,
            public_key_validator_factory=lambda _session: None,
            agent_driver_factory=None,
            database_url=database_url,
            encryption_key=encryption_key,
            instance_id=instance_id,
            review_ttl=timedelta(minutes=15),
            resume_capability_ttl=timedelta(hours=1),
            worker_count=1,
            id_factory=ids,
        )

    runtime = await open_runtime("source-contract-first")
    try:
        session_id = "source-review-reject-accept"
        await _create_sources_session(
            runtime,
            compiled,
            session_id,
            source.source_id,
            source.revision.revision_id,
        )
        proposed = await _propose(runtime, session_id, source.source_id, source.revision.revision_id)
        assert proposed.disposition is OperationDisposition.COMPLETED, (
            proposed.failure.code if proposed.failure else None,
            proposed.failure.public_message if proposed.failure else None,
        )
        assert proposed.observation.to_python() == {
            "proposal_state": "proposal_prepared",
            "review_staged": False,
            "next_owner_decision": "request_owner_review",
        }
        proposal = service.list(owner_id=OWNER, source_id=source.source_id)[0]
        review = await _stage_review(runtime, session_id, proposal_public_ref(proposal.proposal_id))
        assert review.disposition is OperationDisposition.REQUIRES_REVIEW
        assert review.review is not None
        before_revision_id = source.revision.revision_id
        await runtime.close()

        runtime = await open_runtime("source-contract-reopened")
        reopened = await runtime.services.store.load(session_id)
        projection = runtime.services.projector.project(reopened.state)
        review_surfaces = {
            item.surface_id: item for item in projection.surfaces.review
        }
        detail_surfaces = {
            item.surface_id: item for item in projection.surfaces.detail
        }
        assert set(review_surfaces) == {
            "sources.contract_revision_review",
            "sources.routed_api_write_review",
            "sources.delete_review",
        }
        assert dict(review_surfaces["sources.contract_revision_review"].props)
        assert dict(review_surfaces["sources.routed_api_write_review"].props) == {}
        assert dict(review_surfaces["sources.delete_review"].props) == {}
        assert set(detail_surfaces) == {
            "sources.contract_revision_proposal",
            "sources.api_operation_test",
        }
        assert detail_surfaces["sources.api_operation_test"].props == ()
        proposal_props = {
            item.name: item.value.to_python()
            for item in detail_surfaces["sources.contract_revision_proposal"].props
        }
        pending_props = {
            item.name: item.value.to_python()
            for item in review_surfaces["sources.contract_revision_review"].props
        }
        assert proposal_props == {
            "source_id": source.source_id,
            "proposal_ref": proposal_public_ref(proposal.proposal_id),
        }
        assert pending_props["state"] == "pending"
        rejected = await runtime.services.runner.reject_review(
            review.review.id,
            request_id="contract-review-rejected",
            expected_session_version=reopened.session_version,
            session_id=session_id,
        )
        assert rejected.disposition is OperationDisposition.FAILED
        assert rejected.failure is not None
        assert rejected.failure.code == "review_rejected"
        assert repository.get(
            owner_key=str(OWNER), source_id=source.source_id
        ).revision.revision_id == before_revision_id

        restaged = await _stage_review(
            runtime, session_id, proposal_public_ref(proposal.proposal_id)
        )
        accept_snapshot = await runtime.services.store.load(session_id)
        accepted = await runtime.services.runner.accept_review(
            restaged.review.id,
            request_id="contract-review-accepted",
            expected_session_version=accept_snapshot.session_version,
            session_id=session_id,
        )
        assert accepted.disposition is OperationDisposition.COMPLETED, (
            accepted.failure.code if accepted.failure else None,
            accepted.failure.public_message if accepted.failure else None,
        )
        assert accepted.outcome == "approved"
        approved = repository.get(owner_key=str(OWNER), source_id=source.source_id)
        assert approved.revision.revision_id != before_revision_id
        accepted_snapshot = await runtime.services.store.load(session_id)
        accepted_projection = runtime.services.projector.project(
            accepted_snapshot.state
        )
        active_source = accepted_projection.surfaces.active
        assert active_source is not None
        assert active_source.surface_id == "sources.api"
        active_source_props = {
            item.name: item.value.to_python() for item in active_source.props
        }
        assert active_source_props["selected_source_id"] == source.source_id
        assert (
            active_source_props["selected_source_revision_id"]
            == approved.revision.revision_id
        )
        assert repository.get_revision(
            owner_key=str(OWNER),
            source_id=source.source_id,
            revision_id=before_revision_id,
        ).revision.revision_id == before_revision_id

        _, race_source, _ = _ready_fixture(tmp_path)
        race_session = "source-review-accept-race"
        await _create_sources_session(
            runtime,
            compiled,
            race_session,
            race_source.source_id,
            race_source.revision.revision_id,
        )
        await _propose(
            runtime,
            race_session,
            race_source.source_id,
            race_source.revision.revision_id,
        )
        race_proposal = service.list(
            owner_id=OWNER, source_id=race_source.source_id
        )[0]
        race_review = await _stage_review(
            runtime,
            race_session,
            proposal_public_ref(race_proposal.proposal_id),
        )
        service.approve(
            owner_id=OWNER,
            source_id=race_source.source_id,
            proposal_id=race_proposal.proposal_id,
        )
        race_snapshot = await runtime.services.store.load(race_session)
        stale = await runtime.services.runner.accept_review(
            race_review.review.id,
            request_id="contract-review-stale-accept",
            expected_session_version=race_snapshot.session_version,
            session_id=race_session,
        )
        assert stale.disposition is OperationDisposition.FAILED
        assert stale.failure is not None
        assert stale.failure.code == "review_stale"
        assert repository.get_revision(
            owner_key=str(OWNER),
            source_id=race_source.source_id,
            revision_id=race_source.revision.revision_id,
        ).revision.revision_id == race_source.revision.revision_id
    finally:
        await runtime.close()


async def _create_sources_session(
    runtime,
    compiled,
    session_id: str,
    source_id: str,
    revision_id: str,
) -> None:
    initial = create_owner_session(
        compiled,
        session_id,
        now=datetime.now(UTC),
        resume_handle=f"resume-{session_id}",
        resume_ttl=timedelta(hours=1),
    )
    snapshot = await runtime.services.store.create(initial)
    opened = await runtime.services.runner.run(
        OperationRequest(
            session_id=session_id,
            request_id=f"open-{session_id}",
            expected_session_version=snapshot.session_version,
            operation_id="workspace.open_sources",
            source=OperationSource.SURFACE,
            arguments=FrozenJsonObject({}),
        )
    )
    assert opened.disposition is OperationDisposition.COMPLETED
    hub = await runtime.services.store.load(session_id)
    api_opened = await runtime.services.runner.run(
        OperationRequest(
            session_id=session_id,
            request_id=f"open-api-{session_id}",
            expected_session_version=hub.session_version,
            operation_id="sources.open_api_source",
            source=OperationSource.SURFACE,
            arguments=FrozenJsonObject(
                {
                    "source_id": source_id,
                    "source_revision_id": revision_id,
                }
            ),
        )
    )
    assert api_opened.disposition is OperationDisposition.COMPLETED


async def _propose(runtime, session_id: str, source_id: str, revision_id: str):
    snapshot = await runtime.services.store.load(session_id)
    return await runtime.services.runner.run(
        OperationRequest(
            session_id=session_id,
            request_id="contract-proposal",
            expected_session_version=snapshot.session_version,
            operation_id="sources.propose_contract_revision",
            source=OperationSource.SURFACE,
            arguments=FrozenJsonObject(
                {"source_id": source_id, "revision_id": revision_id}
            ),
        )
    )


async def _stage_review(runtime, session_id: str, proposal_ref: str):
    snapshot = await runtime.services.store.load(session_id)
    result = await runtime.services.runner.run(
        OperationRequest(
            session_id=session_id,
            request_id=f"stage-{snapshot.session_version}",
            expected_session_version=snapshot.session_version,
            operation_id="sources.approve_contract_revision",
            source=OperationSource.SURFACE,
            arguments=FrozenJsonObject({"proposal_ref": proposal_ref}),
        )
    )
    assert result.review is not None
    return result
