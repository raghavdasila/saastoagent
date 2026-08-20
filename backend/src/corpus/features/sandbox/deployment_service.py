from __future__ import annotations

import asyncio
import hashlib
import json
import uuid
from dataclasses import asdict

from agent_delivery_runtime.domain import DeliveryError

from corpus.features.deployment.contracts import DeploymentConflict, DeploymentUnavailable
from corpus.shared.agent_delivery import DeployableBundleSpec

from .deployment_schemas import (
    PlaygroundInteractionView,
    PlaygroundSessionView,
    SandboxDeploymentCollectionView,
    SandboxDeploymentView,
    SandboxDiagnosticsView,
)


_SANDBOX_ELIGIBILITY_NOT_REQUIRED = hashlib.sha256(
    b"corpus:sandbox:eligibility-not-required:v1"
).hexdigest()


class SandboxDeploymentService:
    def __init__(self, repository, builds, delivery, bindings) -> None:
        self.repository = repository
        self.builds = builds
        self.delivery = delivery
        self.bindings = bindings

    async def deploy(
        self,
        organization_id: uuid.UUID,
        agent_id: uuid.UUID,
        *,
        build_id: uuid.UUID,
        request_key: str,
        retry_of_deployment_id: uuid.UUID | None = None,
    ) -> SandboxDeploymentView:
        build = await self.builds.require_immutable_built(
            organization_id, agent_id, build_id
        )
        if build.navgraph_hash is None or not build.compiled_navgraph or not build.frontend_contract:
            raise DeploymentConflict(
                "The selected build has no immutable RouteDeck application contract."
            )
        target = await self.repository.ensure_sandbox_target(
            organization_id, agent_id
        )
        neutral_target_id = _neutral_target_id(target.id)
        await asyncio.to_thread(
            self.delivery.ensure_sandbox_target,
            target_id=neutral_target_id,
            owner_scope=str(organization_id),
            name=f"Agent {agent_id} Sandbox",
        )
        record = await self.repository.reserve_sandbox(
            organization_id,
            agent_id,
            target_id=target.id,
            build_id=build.id,
            bundle_hash=build.runtime_build_hash,
            request_key=request_key.strip(),
            retry_of_deployment_id=retry_of_deployment_id,
        )
        if record.status != "queued":
            return _deployment_view(record)
        record = await self.repository.mark_running_inline(
            organization_id, record.id
        )
        surface_contract_hash = hashlib.sha256(
            json.dumps(
                build.frontend_contract,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        try:
            self.bindings.bind(build)
            spec = DeployableBundleSpec(
                bundle_id=str(record.id),
                name=f"Agent {agent_id} Sandbox",
                version=str(build.agent_version),
                content_hash=build.runtime_build_hash,
                routedeck_app_hash=build.navgraph_hash,
                surface_contract_hash=surface_contract_hash,
                eligibility_hash=_SANDBOX_ELIGIBILITY_NOT_REQUIRED,
                runtime_kind="corpus-agent-execution-v1",
                runtime_config={
                    "runtime_build_hash": build.runtime_build_hash,
                    "organization_id": str(organization_id),
                    "agent_id": str(agent_id),
                    "build_id": str(build.id),
                    "model": build.model or "pinned",
                    "navgraph_hash": build.navgraph_hash,
                    "surface_contract_hash": surface_contract_hash,
                    "deployment_mode": "sandbox",
                    "evaluation_eligibility_required": False,
                },
            )
            result = await asyncio.to_thread(
                self.delivery.request_sandbox_deployment,
                neutral_target_id,
                spec,
                request_key=request_key.strip(),
            )
            saved = await self.repository.complete(
                organization_id,
                record.id,
                runtime_deployment_id=result.deployment_id,
                status=result.status,
                failure_code=result.failure_code,
                failure_message=result.failure_message,
            )
            return _deployment_view(saved)
        except Exception as error:
            failed = await self.repository.complete(
                organization_id,
                record.id,
                runtime_deployment_id=None,
                status="failed",
                failure_code=(error.code if isinstance(error, DeliveryError) else type(error).__name__),
                failure_message="Sandbox deployment verification failed.",
            )
            return _deployment_view(failed)

    async def retry(
        self,
        organization_id: uuid.UUID,
        agent_id: uuid.UUID,
        deployment_id: uuid.UUID,
        *,
        request_key: str,
    ) -> SandboxDeploymentView:
        failed = await self.repository.get(
            organization_id, agent_id, deployment_id
        )
        if failed.mode != "sandbox" or failed.status != "failed":
            raise DeploymentConflict(
                "Only the exact failed Sandbox deployment can be retried."
            )
        return await self.deploy(
            organization_id,
            agent_id,
            build_id=failed.build_id,
            request_key=request_key,
            retry_of_deployment_id=failed.id,
        )

    async def list(
        self, organization_id: uuid.UUID, agent_id: uuid.UUID
    ) -> SandboxDeploymentCollectionView:
        await self.builds.list(organization_id, agent_id)
        target = await self.repository.sandbox_target(organization_id, agent_id)
        records = tuple(
            value
            for value in await self.repository.list(organization_id, agent_id)
            if value.mode == "sandbox"
        )
        if target is None:
            return SandboxDeploymentCollectionView(
                agent_id=agent_id,
                target_id=None,
                active_deployment_id=None,
                deployments=(),
                playground_sessions=(),
            )
        sessions = await self._sessions(
            organization_id, agent_id, target.id, purpose="playground"
        )
        return SandboxDeploymentCollectionView(
            agent_id=agent_id,
            target_id=target.id,
            active_deployment_id=target.active_deployment_id,
            deployments=tuple(_deployment_view(value) for value in records),
            playground_sessions=sessions,
        )

    async def create_session(
        self,
        organization_id: uuid.UUID,
        agent_id: uuid.UUID,
        *,
        purpose: str = "playground",
    ) -> PlaygroundInteractionView:
        target = await self._sandbox_target(organization_id, agent_id)
        session, projection = await asyncio.to_thread(
            self.delivery.create_agent_session,
            _neutral_target_id(target.id),
            purpose,
            owner_scope=str(organization_id),
        )
        view = await self._session_view(
            organization_id, agent_id, target.id, session, projection=projection
        )
        return PlaygroundInteractionView(
            session=view,
            projection=_projection_dict(projection),
        )

    async def create_evaluation_session(
        self,
        organization_id: uuid.UUID,
        agent_id: uuid.UUID,
        deployment_id: uuid.UUID,
    ) -> PlaygroundInteractionView:
        target = await self._sandbox_target(organization_id, agent_id)
        deployment = await self.repository.get(
            organization_id, agent_id, deployment_id
        )
        if (
            deployment.mode != "sandbox"
            or deployment.status != "ready"
            or deployment.target_id != target.id
            or target.active_deployment_id != deployment.id
            or not deployment.runtime_deployment_id
        ):
            raise DeploymentConflict(
                "Evaluation requires the exact active ready Sandbox deployment."
            )
        session, projection = await asyncio.to_thread(
            self.delivery.create_agent_session,
            _neutral_target_id(target.id),
            "evaluation_case",
            owner_scope=str(organization_id),
            expected_deployment_id=deployment.runtime_deployment_id,
        )
        view = await self._session_view(
            organization_id, agent_id, target.id, session, projection=projection
        )
        return PlaygroundInteractionView(
            session=view,
            projection=_projection_dict(projection),
        )

    async def execute_evaluation_message(
        self,
        organization_id: uuid.UUID,
        agent_id: uuid.UUID,
        deployment_id: uuid.UUID,
        session_id: str,
        *,
        text: str,
        request_id: str,
    ) -> PlaygroundInteractionView:
        target = await self._sandbox_target(organization_id, agent_id)
        deployment = await self.repository.get(
            organization_id, agent_id, deployment_id
        )
        if (
            deployment.mode != "sandbox"
            or deployment.status != "ready"
            or deployment.target_id != target.id
            or target.active_deployment_id != deployment.id
        ):
            raise DeploymentConflict(
                "The selected Sandbox deployment is no longer active."
            )
        session = await self._require_session(
            target.id, session_id, purpose="evaluation_case"
        )
        projection, interaction = await asyncio.to_thread(
            self.delivery.invoke_agent_session,
            _neutral_target_id(target.id),
            session_id,
            text,
            request_id,
            owner_scope=str(organization_id),
        )
        return PlaygroundInteractionView(
            session=await self._session_view(
                organization_id, agent_id, target.id, session,
                projection=projection,
            ),
            projection=_projection_dict(projection),
            interaction_id=interaction.interaction_id,
        )

    async def session(
        self,
        organization_id: uuid.UUID,
        agent_id: uuid.UUID,
        session_id: str,
    ) -> PlaygroundInteractionView:
        target = await self._sandbox_target(organization_id, agent_id)
        session = await self._require_session(target.id, session_id, purpose="playground")
        projection = await asyncio.to_thread(
            self.delivery.agent_projection,
            _neutral_target_id(target.id),
            session_id,
            owner_scope=str(organization_id),
        )
        return PlaygroundInteractionView(
            session=await self._session_view(
                organization_id, agent_id, target.id, session,
                projection=projection,
            ),
            projection=_projection_dict(projection),
        )

    async def send_message(
        self,
        organization_id: uuid.UUID,
        agent_id: uuid.UUID,
        session_id: str,
        *,
        text: str,
        request_id: str,
    ) -> PlaygroundInteractionView:
        target = await self._sandbox_target(organization_id, agent_id)
        session = await self._require_session(target.id, session_id, purpose="playground")
        projection, interaction = await asyncio.to_thread(
            self.delivery.invoke_agent_session,
            _neutral_target_id(target.id),
            session_id,
            text,
            request_id,
            owner_scope=str(organization_id),
        )
        return PlaygroundInteractionView(
            session=await self._session_view(
                organization_id, agent_id, target.id, session,
                projection=projection,
            ),
            projection=_projection_dict(projection),
            interaction_id=interaction.interaction_id,
        )

    async def resolve_review(
        self,
        organization_id: uuid.UUID,
        agent_id: uuid.UUID,
        session_id: str,
        *,
        review_id: str,
        accepted: bool,
        request_id: str,
    ) -> PlaygroundInteractionView:
        target = await self._sandbox_target(organization_id, agent_id)
        session = await self._require_session(target.id, session_id, purpose="playground")
        projection = await asyncio.to_thread(
            self.delivery.resolve_agent_review,
            _neutral_target_id(target.id),
            session_id,
            review_id,
            accepted,
            request_id,
            owner_scope=str(organization_id),
        )
        return PlaygroundInteractionView(
            session=await self._session_view(
                organization_id, agent_id, target.id, session,
                projection=projection,
            ),
            projection=_projection_dict(projection),
        )

    async def diagnostics(
        self,
        organization_id: uuid.UUID,
        agent_id: uuid.UUID,
        session_id: str,
    ) -> SandboxDiagnosticsView:
        current = await self.session(
            organization_id, agent_id, session_id
        )
        interactions = await asyncio.to_thread(
            self.delivery.session_interactions, session_id
        )
        return SandboxDiagnosticsView(
            session=current.session,
            projection=current.projection,
            interactions=tuple(asdict(value) for value in interactions),
        )

    async def _sandbox_target(self, organization_id, agent_id):
        target = await self.repository.sandbox_target(organization_id, agent_id)
        if target is None or target.active_deployment_id is None:
            raise DeploymentUnavailable(
                "Deploy a ready build to Sandbox before starting a session."
            )
        return target

    async def _sessions(self, organization_id, agent_id, target_id, *, purpose):
        values = await asyncio.to_thread(
            self.delivery.agent_sessions,
            _neutral_target_id(target_id),
            purpose=purpose,
        )
        return tuple(await asyncio.gather(*(
            self._session_view(
                organization_id, agent_id, target_id, value, projection=None
            )
            for value in values
        )))

    async def _require_session(self, target_id, session_id, *, purpose):
        values = await asyncio.to_thread(
            self.delivery.agent_sessions,
            _neutral_target_id(target_id),
            purpose=purpose,
        )
        value = next((item for item in values if item.session_id == session_id), None)
        if value is None:
            raise DeploymentUnavailable("The Sandbox session is unavailable.")
        return value

    async def _session_view(
        self, organization_id, agent_id, target_id, session, *, projection
    ):
        deployment = await self.repository.get_by_runtime(
            organization_id, agent_id, session.deployment_id
        )
        if deployment.target_id != target_id or deployment.mode != "sandbox":
            raise DeploymentUnavailable("The Sandbox session deployment is unavailable.")
        return PlaygroundSessionView(
            session_id=session.session_id,
            target_id=target_id,
            deployment_id=deployment.id,
            runtime_deployment_id=session.deployment_id,
            build_id=deployment.build_id,
            purpose=session.purpose,
            created_at=session.created_at,
            projection=(
                _projection_dict(projection) if projection is not None else None
            ),
        )


def _neutral_target_id(target_id: uuid.UUID) -> str:
    return f"sbx_{target_id.hex}"


def _deployment_view(value) -> SandboxDeploymentView:
    if value.target_id is None:
        raise DeploymentUnavailable("The Sandbox deployment target is unavailable.")
    return SandboxDeploymentView(
        id=value.id,
        target_id=value.target_id,
        agent_id=value.agent_id,
        build_id=value.build_id,
        mode=value.mode,
        status=value.status,
        request_key=value.request_key,
        runtime_deployment_id=value.runtime_deployment_id,
        failure_code=value.failure_code,
        failure_message=value.failure_message,
        created_at=value.created_at,
        updated_at=value.updated_at,
    )


def _projection_dict(value) -> dict[str, object]:
    return {
        "revision": value.revision,
        "messages": [dict(item) for item in value.messages],
        "surfaces": [dict(item) for item in value.surfaces],
        "suggested_actions": [dict(item) for item in value.suggested_actions],
    }


__all__ = ["SandboxDeploymentService"]
