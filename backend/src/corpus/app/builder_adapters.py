from __future__ import annotations

import hashlib
import json
import uuid
from collections.abc import Mapping
from pathlib import Path

from sqlalchemy import select

from corpus.features.agents.models import Agent, AgentVersion
from corpus.features.builder.domain import BuilderInputSnapshot, BuilderSourceBinding
from corpus.features.builder.ports import BuilderConflict, BuilderUnavailable
from corpus.features.designer.models import AgentBuildRequest, AgentDesign, AgentDesignRevision
from corpus.features.designer.schemas import DesignContent
from corpus.features.sources.models import SourceState
from corpus.features.sources.repository import LocalSourceRepository, SourceNotFound, SourceNotReady
from corpus.features.sources.connectors.api.connections import ApiConnectionError, ApiConnectionProfileRepository
from corpus.features.sources.connectors.api.operation_curation import ApiOperationCurationError, ApiOperationCurationService
from corpus.features.sources.connectors.api.toolrouter import load_api_contract_documents
from corpus.integrations.api_execution._snapshot.contract_revision import openapi_document_hash
from corpus.persistence import CorpusDatabase


class CorpusBuilderInputGateway:
    def __init__(self, database: CorpusDatabase, sources: LocalSourceRepository, profiles: ApiConnectionProfileRepository, curations: ApiOperationCurationService) -> None:
        self.database, self.sources, self.profiles, self.curations = database, sources, profiles, curations

    async def current_build_request_id(
        self,
        organization_id: uuid.UUID,
        agent_id: uuid.UUID,
    ) -> uuid.UUID:
        async with self.database.session() as session:
            design = await session.scalar(select(AgentDesign).where(
                AgentDesign.organization_id == organization_id,
                AgentDesign.agent_id == agent_id,
            ))
            if design is None or design.accepted_revision_id is None:
                raise BuilderUnavailable("The selected Agent has no accepted design to build.")
            values = tuple((await session.scalars(select(AgentBuildRequest).where(
                AgentBuildRequest.organization_id == organization_id,
                AgentBuildRequest.agent_id == agent_id,
                AgentBuildRequest.design_revision_id == design.accepted_revision_id,
            ))).all())
        if len(values) != 1:
            raise BuilderUnavailable(
                "The selected Agent does not have one exact current build request."
            )
        return values[0].id

    async def snapshot(self, organization_id: uuid.UUID, record) -> BuilderInputSnapshot:
        async with self.database.session() as session:
            request = await session.get(AgentBuildRequest, record.build_request_id)
            revision = await session.get(AgentDesignRevision, record.design_revision_id)
            design = await session.scalar(select(AgentDesign).where(
                AgentDesign.organization_id == organization_id,
                AgentDesign.agent_id == record.agent_id,
                AgentDesign.accepted_revision_id == record.design_revision_id,
            ))
            agent_version = await session.scalar(select(AgentVersion).where(
                AgentVersion.agent_id == record.agent_id,
                AgentVersion.version == record.agent_version,
            ))
            agent = await session.get(Agent, record.agent_id)
        if request is None or revision is None or design is None or agent_version is None or agent is None:
            raise BuilderUnavailable("The exact accepted build inputs are unavailable.")
        if request.design_revision_id != revision.id or revision.design_id != design.id:
            raise BuilderConflict("The build request no longer matches the exact accepted design.")
        source_bindings = tuple(self._source_binding(organization_id, item) for item in revision.source_inputs)
        if not source_bindings:
            raise BuilderUnavailable("The accepted design has no runnable Source inputs.")
        operations = [operation for item in source_bindings for operation in item.included_operation_ids]
        if len(operations) != len(set(operations)):
            raise BuilderConflict("The accepted Source inputs contain duplicate operation identities.")
        content = DesignContent.model_validate(revision.content)
        return BuilderInputSnapshot(
            build_id=record.id, build_request_id=request.id, organization_id=organization_id,
            agent_id=record.agent_id, agent_version=record.agent_version,
            design_revision_id=revision.id, input_fingerprint=revision.input_fingerprint,
            name=agent_version.name, goal=content.goal, instructions=content.instructions,
            features=content.features, behaviors=content.behaviors, policies=content.policies,
            capabilities=content.capabilities, tools=content.tools,
            runtime_areas=tuple(item.model_dump(mode="json") for item in content.runtime_areas),
            source_bindings=source_bindings,
        )

    def _source_binding(self, organization_id: uuid.UUID, raw: dict[str, object]) -> BuilderSourceBinding:
        try:
            source_id, revision_id, curation_id = str(raw["source_id"]), str(raw["source_revision_id"]), str(raw["curation_id"])
            fingerprint = str(raw["inventory_fingerprint"])
            included = tuple(map(str, raw["included_operation_ids"]))
            view = self.curations.inspect(owner_id=organization_id, source_id=source_id, source_revision_id=revision_id)
            curation = next((item for item in view.history if item.id == curation_id), None)
            if curation is None or curation.inventory_fingerprint != fingerprint or curation.included_operation_ids != included:
                raise BuilderConflict("The accepted operation curation is unavailable or inconsistent.")
            profiles = self.profiles.list_exact(owner_key=str(organization_id), source_id=source_id, revision_id=revision_id)
            if len(profiles) != 1:
                raise BuilderUnavailable("Each accepted API Source revision must have exactly one saved connection profile before it can be built.")
            profile = profiles[0]
            source = self.sources.get_revision(owner_key=str(organization_id), source_id=source_id, revision_id=revision_id)
            if source.connector_key != "api" or source.revision.state is not SourceState.READY:
                raise BuilderUnavailable("The accepted API Source revision is not ready.")
            with self.sources.locked_revision(
                owner_key=str(organization_id), source_id=source_id, revision_id=revision_id
            ) as (locked_source, revision_dir):
                input_path = revision_dir / "i" / locked_source.revision.original_filename
                input_bytes = input_path.read_bytes()
                if hashlib.sha256(input_bytes).hexdigest() != locked_source.revision.content_sha256:
                    raise BuilderConflict("The accepted API definition changed after design acceptance.")
                artifact_revision_id = locked_source.revision.artifact_revision_id or revision_id
                artifact_dir = revision_dir.parent.parent / "r" / artifact_revision_id / "a"
                document_path, document = _runtime_document(
                    input_path=input_path,
                    artifact_revision_id=locked_source.revision.artifact_revision_id,
                )
                document_hash = openapi_document_hash(document)
            return BuilderSourceBinding(
                source_id, revision_id, curation_id, fingerprint, included, artifact_dir,
                document_path, document_hash, profile.id, profile.base_url,
                profile.authentication_method.value, profile.credential_name,
                profile.credential_reference_id, profile.credential_version,
            )
        except (KeyError, TypeError, ValueError, OSError, json.JSONDecodeError, SourceNotFound, SourceNotReady, ApiConnectionError, ApiOperationCurationError) as error:
            raise BuilderUnavailable("The accepted runnable Source binding is unavailable.") from error


def _runtime_document(
    *,
    input_path: Path,
    artifact_revision_id: str | None,
) -> tuple[Path, Mapping[str, object]]:
    """Bind execution to the exact document that produced the accepted graph.

    Initial API uploads may be YAML. They remain directly buildable when the
    ToolRouter normalization required no semantic repair. If analysis repaired
    the definition, the owner must first accept those API changes and the
    Designer must pin that reviewed derived revision. Derived revisions already
    persist their exact effective API document as JSON.
    """
    if artifact_revision_id is not None:
        try:
            value = json.loads(input_path.read_bytes())
        except (OSError, json.JSONDecodeError) as error:
            raise BuilderUnavailable(
                "The exact reviewed API definition for this build is unavailable."
            ) from error
        if not isinstance(value, Mapping):
            raise BuilderUnavailable(
                "The exact reviewed API definition for this build is invalid."
            )
        return input_path, value

    try:
        bundle = load_api_contract_documents(input_path)
    except (OSError, TypeError, ValueError) as error:
        raise BuilderUnavailable(
            "The analyzed API definition for this build is unavailable."
        ) from error
    if len(bundle.raw_specs) != 1 or len(bundle.repaired_specs) != 1:
        raise BuilderUnavailable(
            "The analyzed API definition for this build is invalid."
        )
    source_name = next(iter(bundle.raw_specs))
    raw = bundle.raw_specs[source_name]
    repaired = bundle.repaired_specs[source_name]
    if openapi_document_hash(raw) != openapi_document_hash(repaired):
        raise BuilderUnavailable(
            "Review the analyzed API changes for this Source, then update and accept the Agent design before building."
        )
    return input_path, raw


__all__ = ["CorpusBuilderInputGateway"]
