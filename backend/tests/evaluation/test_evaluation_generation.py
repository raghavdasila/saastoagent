from __future__ import annotations

import uuid
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from corpus.features.builder.domain import BuilderRecord
from corpus.features.evaluation.domain import EvaluationSetRecord
from corpus.features.evaluation.generation import EvaluationGenerationProcessor
from corpus.integrations.toolrouter import IngestRequest, ToolRouterAdapter, ToolRouterSettings

from backend.tests.integrations.toolrouter.conftest import KeywordEmbeddingProvider, write_openapi_fixture


class Jobs:
    def __init__(self, owner, payload):
        self.owner, self.payload, self.succeeded, self.failed = owner, payload, None, None

    async def mark_running(self, *, job_id):
        return SimpleNamespace(
            id=job_id, owner_id=self.owner,
            job_type="evaluation.generate_build_evalset", payload=self.payload,
        )

    async def mark_succeeded(self, *, job_id, result): self.succeeded = result
    async def mark_failed(self, **values): self.failed = values


class Evaluations:
    def __init__(self, record):
        self.record, self.cases, self.status = record, [], "queued"
        self.eligibility = None
    async def get_set(self, *_): return self.record
    async def mark_generation_running(self, *_): self.status = "running"
    async def mark_generation_ready(self, _owner, _set, summary): self.status = "ready"; self.summary = summary
    async def mark_generation_failed(self, *_args, **_kwargs): self.status = "failed"
    async def add_generated_case(self, _owner, _set, **values): self.cases.append(values)
    async def add_eligibility(self, owner, agent, build, build_hash, runtime):
        self.eligibility = (owner, agent, build, build_hash, runtime)


class Builds:
    def __init__(self, value): self.value = value
    async def get(self, *_): return self.value


class Engine:
    def __init__(self): self.allowed = None
    def generate_evalset(self, **values):
        self.allowed = values["allowed_endpoint_ids"]
        return SimpleNamespace(
            status="ready", accepted_count=1, expected_count=1,
            generator_model="generator", generator_model_digest="g" * 64,
            reviewer_model="reviewer", reviewer_model_digest="r" * 64,
            accepted_tasks=({
                "id": "generated-case-1",
                "query": "List every widget",
                "expected_endpoint_sequence": [self.allowed[0]],
                "evalset": {"query_category": "paraphrase"},
            },),
        )


@pytest.mark.asyncio
async def test_generation_uses_only_the_exact_build_curation_and_persists_draft_cases(tmp_path):
    artifacts = tmp_path / "artifacts"
    ToolRouterAdapter(
        ToolRouterSettings(), embedding_provider=KeywordEmbeddingProvider()
    ).ingest(IngestRequest(
        source_path=write_openapi_fixture(tmp_path / "widget-api.json"),
        artifact_dir=artifacts,
    ))
    owner, agent, build_id, set_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    now = datetime.now(UTC)
    evaluation_set = EvaluationSetRecord(
        set_id, owner, agent, build_id, "Generated coverage",
        uuid.uuid4(), "queued", None, None, None, now, now,
    )
    build = BuilderRecord(
        build_id, owner, agent, uuid.uuid4(), uuid.uuid4(), 1,
        "ready", "stopped", "b" * 64, "model", "m" * 64,
        ({
            "source_id": "source-1", "source_revision_id": "revision-1",
            "curation_id": "curation-1", "artifact_dir": str(artifacts),
            "included_operation_ids": ["listWidgets"],
        },),
        ("listWidgets",), "n" * 64, {}, {}, None, None, now, now,
    )
    payload = {
        "evaluation_set_id": str(set_id), "agent_id": str(agent),
        "build_id": str(build_id), "categories": ["paraphrase"],
    }
    jobs, evaluations, engine = Jobs(owner, payload), Evaluations(evaluation_set), Engine()

    result = await EvaluationGenerationProcessor(
        jobs, evaluations, Builds(build), engine
    ).process(uuid.uuid4())

    assert evaluations.status == "ready"
    assert engine.allowed is not None and len(engine.allowed) == 1
    assert evaluations.cases == [{
        "task_id": "generated-case-1", "title": "List every widget",
        "message": "List every widget", "category": "paraphrase",
        "difficulty": "easy", "expected_operation_ids": ("listWidgets",),
        "mandatory": True,
    }]
    assert result["build_id"] == str(build_id)
    assert jobs.succeeded == result
    assert jobs.failed is None
    assert evaluations.eligibility is not None
    assert evaluations.eligibility[4].eligible is False
    assert evaluations.eligibility[4].reasons == (
        "generated_evaluation_cases_pending",
    )
