from __future__ import annotations

import json
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import timedelta
from pathlib import Path
from typing import Any, Mapping
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from routedeck_fastapi import SameOriginMutationPolicy

from corpus.features.sources.connectors.api.connections import (
    ApiAuthenticationMethod,
    ApiConnectionProfileRepository,
)
from corpus.features.sources.connectors.api.operation_curation import (
    ApiOperationCurationService,
)
from corpus.features.sources.connectors.api.route_plans import (
    ApiRoutePlanConflict,
    ApiRoutePlanError,
    ApiRoutePlanService,
)
from corpus.features.sources.connectors.api.engine import SourceManagedParameter
from corpus.features.sources.connectors.api.http import create_api_source_router
from corpus.features.sources.http import SourceHttpProblem, source_problem_response
from corpus.features.sources.contracts import (
    SourceRankedItem,
    SourceRetrievalResult,
    SourceRetrievalStep,
)
from corpus.features.sources.repository import LocalSourceRepository, SourceNotFound
from backend.tests.sources.test_http import OwnerResolver, _auth_settings


OWNER = uuid.UUID("00000000-0000-0000-0000-000000000001")
OTHER_OWNER = uuid.UUID("00000000-0000-0000-0000-000000000002")
CONVERSATION = "conversation-owner-a"
ROUTE_SESSION = "route-session-owner-a"


class FakePlanningEngine:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def retrieve(
        self,
        *,
        artifact_dir: Path,
        query: str,
        top_k: int,
        trace_mode: str,
        provided_params: Mapping[str, Any] | None,
        allowed_endpoint_ids: tuple[str, ...] | None = None,
        managed_parameters: tuple[SourceManagedParameter, ...] = (),
    ) -> SourceRetrievalResult:
        self.calls.append(
            {
                "artifact_dir": artifact_dir,
                "query": query,
                "provided_params": dict(provided_params or {}),
                "allowed_endpoint_ids": allowed_endpoint_ids,
                "managed_parameters": managed_parameters,
            }
        )
        endpoint_id = "widgets:listWidgets"
        missing = () if provided_params and provided_params.get("customer_id") else ("customer_id",)
        decision = "ROUTE" if not missing else "ASK_PARAM"
        steps = (
            SourceRetrievalStep(
                query=query,
                ranked_items=(
                    SourceRankedItem(
                        item_id=endpoint_id,
                        item_kind="api_operation",
                        score=0.93,
                    ),
                ),
                trace={"trace_mode": "bounded"},
            ),
        )
        if "then" in query.casefold():
            steps = (*steps, SourceRetrievalStep(
                query="confirm the same included operation",
                ranked_items=(
                    SourceRankedItem(
                        item_id=endpoint_id,
                        item_kind="api_operation",
                        score=0.81,
                    ),
                ),
                trace={"trace_mode": "bounded"},
            ))
        return SourceRetrievalResult(
            query=query,
            decision_type=decision,
            decision_reason="fixture decision",
            decomposed=False,
            steps=steps,
            missing_inputs=missing,
        )


class AmbiguousPlanningEngine(FakePlanningEngine):
    def retrieve(
        self,
        *,
        artifact_dir: Path,
        query: str,
        top_k: int,
        trace_mode: str,
        provided_params: Mapping[str, Any] | None,
        allowed_endpoint_ids: tuple[str, ...] | None = None,
        managed_parameters: tuple[SourceManagedParameter, ...] = (),
    ) -> SourceRetrievalResult:
        del top_k, trace_mode
        allowed = tuple(allowed_endpoint_ids or ())
        self.calls.append(
            {
                "artifact_dir": artifact_dir,
                "query": query,
                "provided_params": dict(provided_params or {}),
                "allowed_endpoint_ids": allowed,
                "managed_parameters": managed_parameters,
            }
        )
        ranked = tuple(
            SourceRankedItem(item_id=item, item_kind="api_operation", score=0.9 - index / 10)
            for index, item in enumerate(allowed)
        )
        return SourceRetrievalResult(
            query=query,
            decision_type="ASK_DISAMBIGUATE" if len(allowed) > 1 else "ROUTE",
            decision_reason="fixture ambiguity",
            decomposed=False,
            steps=(
                SourceRetrievalStep(
                    query=query,
                    ranked_items=ranked,
                    trace={"trace_mode": "bounded"},
                ),
            ),
            missing_inputs=(),
        )


def test_plan_waits_then_clarifies_same_immutable_lineage_without_execution(
    tmp_path: Path,
) -> None:
    service, engine, source_id, revision_id, profile_id, curation_id = _service(tmp_path)

    waiting = service.create(
        owner_id=OWNER,
        conversation_id=CONVERSATION,
        route_session_id=ROUTE_SESSION,
        source_id=source_id,
        source_revision_id=revision_id,
        profile_id=profile_id,
        curation_id=curation_id,
        request_text="List orders for the selected customer",
    )
    assert waiting.state == "needs_input"
    assert waiting.missing_inputs == ("customer_id",)
    assert waiting.clarification_prompt == "What should Corpus use for customer_id?"
    assert waiting.api_call_count == 0

    ready = service.clarify(
        owner_id=OWNER,
        conversation_id=CONVERSATION,
        route_session_id=ROUTE_SESSION,
        source_id=source_id,
        source_revision_id=revision_id,
        plan_id=waiting.plan_id,
        expected_record_id=waiting.record_id,
        answers={"customer_id": "cus_123"},
    )
    assert ready.plan_id == waiting.plan_id
    assert ready.record_id != waiting.record_id
    assert ready.previous_record_id == waiting.record_id
    assert ready.state == "ready"
    assert ready.api_call_count == 0
    assert ready.steps[0].selected_operation_id == "listWidgets"
    assert ready.steps[0].ranked_operations[0].operation_label == "GET /widgets"
    assert ready.steps[0].method == "GET"
    assert ready.steps[0].http_safety == "read"
    assert ready.input_provenance[0].source == "user_clarification"
    assert [call["allowed_endpoint_ids"] for call in engine.calls] == [
        ("widgets:listWidgets",),
        ("widgets:listWidgets",),
    ]

    reloaded_repository = LocalSourceRepository(tmp_path / "sources")
    reloaded = ApiRoutePlanService(
        sources=reloaded_repository,
        curations=ApiOperationCurationService(reloaded_repository),
        profiles=ApiConnectionProfileRepository(reloaded_repository),
        engine=engine,  # type: ignore[arg-type]
    ).current(
        owner_id=OWNER,
        conversation_id=CONVERSATION,
        route_session_id=ROUTE_SESSION,
        source_id=source_id,
        source_revision_id=revision_id,
    )
    assert reloaded == ready
    records = list(
        (
                reloaded_repository.revision_dir(
                    owner_key=str(OWNER), source_id=source_id
                )
            / "api-route-plans"
            / "records"
        ).glob("*.json")
    )
    assert len(records) == 2


def test_explicit_safe_current_request_input_is_persisted_with_exact_provenance(
    tmp_path: Path,
) -> None:
    service, engine, source_id, revision_id, profile_id, curation_id = _service(tmp_path)

    ready = service.create(
        owner_id=OWNER,
        conversation_id=CONVERSATION,
        route_session_id=ROUTE_SESSION,
        source_id=source_id,
        source_revision_id=revision_id,
        profile_id=profile_id,
        curation_id=curation_id,
        request_text="List orders for the selected customer",
        provided_inputs={"customer_id": "cus_123"},
    )

    assert ready.state == "ready"
    assert ready.input_provenance[0].name == "customer_id"
    assert ready.input_provenance[0].value == "cus_123"
    assert ready.input_provenance[0].source == "current_request"
    assert engine.calls[0]["provided_params"] == {"customer_id": "cus_123"}


def test_operation_choice_clarification_narrows_toolrouter_before_rerouting(
    tmp_path: Path,
) -> None:
    service, engine, source_id, revision_id, profile_id, curation_id = _service(tmp_path)
    inventory = service.curations.inspect(
        owner_id=OWNER,
        source_id=source_id,
        source_revision_id=revision_id,
    )
    curation = service.curations.save(
        owner_id=OWNER,
        source_id=source_id,
        source_revision_id=revision_id,
        inventory_fingerprint=inventory.inventory_fingerprint,
        included_operation_ids=("createWidget", "listWidgets"),
        excluded_operation_ids=(),
        expected_current_curation_id=curation_id,
    )
    engine = AmbiguousPlanningEngine()
    service = replace(service, engine=engine)  # type: ignore[arg-type]

    waiting = service.create(
        owner_id=OWNER,
        conversation_id=CONVERSATION,
        route_session_id=ROUTE_SESSION,
        source_id=source_id,
        source_revision_id=revision_id,
        profile_id=profile_id,
        curation_id=curation.id,
        request_text="Use the widgets API",
    )
    assert waiting.state == "needs_operation_choice"
    assert waiting.steps[0].selected_operation_id is None
    assert waiting.steps[0].method is None
    assert waiting.operation_choice is None

    ready = service.clarify(
        owner_id=OWNER,
        conversation_id=CONVERSATION,
        route_session_id=ROUTE_SESSION,
        source_id=source_id,
        source_revision_id=revision_id,
        plan_id=waiting.plan_id,
        expected_record_id=waiting.record_id,
        answers={"operation_id": "createWidget"},
    )

    assert ready.plan_id == waiting.plan_id
    assert ready.previous_record_id == waiting.record_id
    assert ready.state == "ready"
    assert ready.steps[0].selected_operation_id == "createWidget"
    assert ready.operation_choice is not None
    assert ready.operation_choice.operation_id == "createWidget"
    assert ready.operation_choice.source == "user_clarification"
    assert [call["allowed_endpoint_ids"] for call in engine.calls] == [
        ("widgets:createWidget", "widgets:listWidgets"),
        ("widgets:createWidget",),
    ]
    assert engine.calls[1]["provided_params"] == {}


@pytest.mark.parametrize(
    "name",
    (
        "client_secret",
        "x-api-key",
        "x-publishable-api-key",
        "access_token",
        "refreshToken",
        "Authorization",
        "cookie_header",
        "privateKey",
    ),
)
def test_secret_like_input_names_fail_before_routing_or_persistence(
    tmp_path: Path,
    name: str,
) -> None:
    service, engine, source_id, revision_id, profile_id, curation_id = _service(tmp_path)

    with pytest.raises(ApiRoutePlanConflict, match="input name is invalid"):
        service.create(
            owner_id=OWNER,
            conversation_id=CONVERSATION,
            route_session_id=ROUTE_SESSION,
            source_id=source_id,
            source_revision_id=revision_id,
            profile_id=profile_id,
            curation_id=curation_id,
            request_text="List widgets",
            provided_inputs={name: "credential-canary"},
        )

    assert engine.calls == []
    revision_dir = service.sources.revision_dir(owner_key=str(OWNER), source_id=source_id)
    assert not (revision_dir / "api-route-plans").exists()


@pytest.mark.parametrize(
    ("request_text", "provided_inputs"),
    (
        ("List widgets", {"customer_id": "Bearer abcdefghijklmnop"}),
        ("List widgets with authorization: Basic abcdefghijklmnop", {}),
        ("List widgets", {"customer_id": "eyJabcdefgh.eyJijklmnop.abcdefghijklmno"}),
    ),
)
def test_secret_like_values_fail_before_routing_or_persistence(
    tmp_path: Path,
    request_text: str,
    provided_inputs: Mapping[str, Any],
) -> None:
    service, engine, source_id, revision_id, profile_id, curation_id = _service(tmp_path)

    with pytest.raises(ApiRoutePlanConflict):
        service.create(
            owner_id=OWNER,
            conversation_id=CONVERSATION,
            route_session_id=ROUTE_SESSION,
            source_id=source_id,
            source_revision_id=revision_id,
            profile_id=profile_id,
            curation_id=curation_id,
            request_text=request_text,
            provided_inputs=provided_inputs,
        )

    assert engine.calls == []
    revision_dir = service.sources.revision_dir(owner_key=str(OWNER), source_id=source_id)
    assert not (revision_dir / "api-route-plans").exists()


def test_plan_is_exact_owner_conversation_session_and_current_record_scoped(
    tmp_path: Path,
) -> None:
    service, _engine, source_id, revision_id, profile_id, curation_id = _service(tmp_path)
    waiting = service.create(
        owner_id=OWNER,
        conversation_id=CONVERSATION,
        route_session_id=ROUTE_SESSION,
        source_id=source_id,
        source_revision_id=revision_id,
        profile_id=profile_id,
        curation_id=curation_id,
        request_text="List orders",
    )

    with pytest.raises(ApiRoutePlanConflict):
        service.clarify(
            owner_id=OWNER,
            conversation_id=CONVERSATION,
            route_session_id=ROUTE_SESSION,
            source_id=source_id,
            source_revision_id=revision_id,
            plan_id=waiting.plan_id,
            expected_record_id="stale-record-id!",
            answers={"customer_id": "cus_123"},
        )
    assert service.current(
        owner_id=OWNER,
        conversation_id=CONVERSATION,
        route_session_id="route-session-other",
        source_id=source_id,
        source_revision_id=revision_id,
    ) is None
    with pytest.raises(SourceNotFound):
        service.current(
            owner_id=OTHER_OWNER,
            conversation_id=CONVERSATION,
            route_session_id=ROUTE_SESSION,
            source_id=source_id,
            source_revision_id=revision_id,
        )
    replacement = service.create(
        owner_id=OWNER,
        conversation_id=CONVERSATION,
        route_session_id="route-session-other",
        source_id=source_id,
        source_revision_id=revision_id,
        profile_id=profile_id,
        curation_id=curation_id,
        request_text="List orders in the recovered session",
    )
    assert replacement.plan_id != waiting.plan_id
    records = list(
        (
            service.sources.revision_dir(owner_key=str(OWNER), source_id=source_id)
            / "api-route-plans"
            / "records"
        ).glob("*.json")
    )
    assert len(records) == 2


def test_public_plan_excludes_router_internal_names_and_credential_identity(
    tmp_path: Path,
) -> None:
    service, engine, source_id, revision_id, profile_id, curation_id = _service(tmp_path)
    plan = service.create(
        owner_id=OWNER,
        conversation_id=CONVERSATION,
        route_session_id=ROUTE_SESSION,
        source_id=source_id,
        source_revision_id=revision_id,
        profile_id=profile_id,
        curation_id=curation_id,
        request_text="List orders",
    )
    encoded = plan.model_dump_json()
    assert "ASK_PARAM" not in encoded
    assert "router_decision" not in encoded
    assert "router_evidence" not in encoded
    assert "credential_reference" not in encoded
    assert "api_call_count\":0" in encoded
    assert plan.managed_parameters[0].model_dump() == {
        "name": "x-publishable-api-key",
        "location": "header",
        "authentication_method": "api_key",
        "source": "managed_by_profile",
    }
    revision_dir = service.sources.revision_dir(owner_key=str(OWNER), source_id=source_id)
    persisted = json.loads(
        (
            revision_dir
            / "api-route-plans"
            / "records"
            / f"{plan.record_id}.json"
        ).read_text(encoding="utf-8")
    )
    assert persisted["router_evidence"] == [{"trace_mode": "bounded"}]
    assert persisted["credential_reference_id"] == "00000000-0000-0000-0000-000000000003"
    assert persisted["managed_parameters"] == [{
        "name": "x-publishable-api-key",
        "location": "header",
        "authentication_method": "api_key",
        "source": "managed_by_profile",
    }]
    assert "credential_value" not in json.dumps(persisted)
    assert engine.calls[0]["provided_params"] == {}
    assert engine.calls[0]["managed_parameters"] == (
        SourceManagedParameter(name="x-publishable-api-key", location="header"),
    )


def test_route_plan_http_derives_owner_conversation_and_route_session(
    tmp_path: Path,
) -> None:
    service, _engine, source_id, revision_id, profile_id, curation_id = _service(tmp_path)

    class ConversationOwnerResolver(OwnerResolver):
        async def resolve_conversation(
            self, *, access_token: str, conversation_id: str, touch: bool
        ):
            del touch
            expected = {
                "owner-a": ("conversation-owner-a", "route-session-owner-a"),
                "owner-b": ("conversation-owner-b", "route-session-owner-b"),
            }
            if expected.get(access_token, (None, None))[0] != conversation_id:
                from corpus.auth.service import ConversationUnavailable

                raise ConversationUnavailable
            return SimpleNamespace(
                public_id=conversation_id,
                route_session_id=expected[access_token][1],
            )

    app = FastAPI()
    app.add_exception_handler(SourceHttpProblem, source_problem_response)
    app.include_router(
        create_api_source_router(
            service=object(),
            auth_service=ConversationOwnerResolver(),  # type: ignore[arg-type]
            mutation_policy=SameOriginMutationPolicy(
                trusted_origins=frozenset({"http://127.0.0.1:5199"})
            ),
            max_upload_bytes=1024,
            graph_presenter=object(),
            connection_profiles=object(),
            contract_revision_service=object(),
            connection_check_service=object(),
            operation_curation_service=object(),
            route_plan_service=service,
        )
    )
    with TestClient(app) as client:
        headers = {
            "Authorization": "Bearer owner-a",
            "X-Corpus-Conversation-ID": CONVERSATION,
            "Origin": "http://127.0.0.1:5199",
        }
        created = client.post(
            f"/api/sources/{source_id}/route-plans",
            headers=headers,
            json={
                "source_revision_id": revision_id,
                "profile_id": profile_id,
                "curation_id": curation_id,
                "request_text": "List orders",
                "provided_inputs": {},
            },
        )
        assert created.status_code == 201
        assert created.json()["state"] == "needs_input"
        assert created.json()["api_call_count"] == 0
        assert "router_decision" not in created.json()
        current = client.get(
            f"/api/sources/{source_id}/route-plans/current",
            headers=headers,
            params={"revision_id": revision_id},
        )
        assert current.status_code == 200
        clarified = client.post(
            f"/api/sources/{source_id}/route-plans/{created.json()['plan_id']}/clarifications",
            headers=headers,
            json={
                "source_revision_id": revision_id,
                "expected_record_id": created.json()["record_id"],
                "answers": {"customer_id": "cus_123"},
            },
        )
        assert clarified.status_code == 200
        assert clarified.json()["state"] == "ready"
        hidden = client.get(
            f"/api/sources/{source_id}/route-plans/current",
            headers={
                "Authorization": "Bearer owner-b",
                "X-Corpus-Conversation-ID": "conversation-owner-b",
            },
            params={"revision_id": revision_id},
        )
        assert hidden.status_code == 404


def test_concurrent_create_and_clarify_use_exact_current_record_cas(
    tmp_path: Path,
) -> None:
    service, _engine, source_id, revision_id, profile_id, curation_id = _service(tmp_path)

    def create():
        return service.create(
            owner_id=OWNER,
            conversation_id=CONVERSATION,
            route_session_id=ROUTE_SESSION,
            source_id=source_id,
            source_revision_id=revision_id,
            profile_id=profile_id,
            curation_id=curation_id,
            request_text="List orders",
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(create), executor.submit(create)]
    created = [future.result() for future in futures if future.exception() is None]
    rejected = [future.exception() for future in futures if future.exception() is not None]
    assert len(created) == 1
    assert len(rejected) == 1
    assert isinstance(rejected[0], ApiRoutePlanConflict)

    waiting = created[0]
    def clarify():
        return service.clarify(
            owner_id=OWNER,
            conversation_id=CONVERSATION,
            route_session_id=ROUTE_SESSION,
            source_id=source_id,
            source_revision_id=revision_id,
            plan_id=waiting.plan_id,
            expected_record_id=waiting.record_id,
            answers={"customer_id": "cus_123"},
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(clarify), executor.submit(clarify)]
    clarified = [future.result() for future in futures if future.exception() is None]
    rejected = [future.exception() for future in futures if future.exception() is not None]
    assert len(clarified) == 1
    assert len(rejected) == 1
    assert isinstance(rejected[0], ApiRoutePlanConflict)


def test_stale_curation_fails_without_rerouting(
    tmp_path: Path,
) -> None:
    service, engine, source_id, revision_id, profile_id, curation_id = _service(tmp_path)
    waiting = service.create(
        owner_id=OWNER,
        conversation_id=CONVERSATION,
        route_session_id=ROUTE_SESSION,
        source_id=source_id,
        source_revision_id=revision_id,
        profile_id=profile_id,
        curation_id=curation_id,
        request_text="List orders",
    )
    inventory = service.curations.inspect(
        owner_id=OWNER,
        source_id=source_id,
        source_revision_id=revision_id,
    )
    service.curations.save(
        owner_id=OWNER,
        source_id=source_id,
        source_revision_id=revision_id,
        inventory_fingerprint=inventory.inventory_fingerprint,
        included_operation_ids=("createWidget",),
        excluded_operation_ids=("listWidgets",),
        expected_current_curation_id=curation_id,
    )
    with pytest.raises(ApiRoutePlanConflict, match="curation.*current"):
        service.current(
            owner_id=OWNER,
            conversation_id=CONVERSATION,
            route_session_id=ROUTE_SESSION,
            source_id=source_id,
            source_revision_id=revision_id,
        )
    assert len(engine.calls) == 1



def test_expired_plan_can_be_explicitly_replaced_without_deleting_history(
    tmp_path: Path,
) -> None:
    expired_service, engine, sid, rid, pid, cid = _service(tmp_path)
    expired_service = replace(expired_service, ttl=timedelta(seconds=-1))
    expired = expired_service.create(
        owner_id=OWNER,
        conversation_id=CONVERSATION,
        route_session_id=ROUTE_SESSION,
        source_id=sid,
        source_revision_id=rid,
        profile_id=pid,
        curation_id=cid,
        request_text="List orders",
    )
    assert expired_service.current(
        owner_id=OWNER,
        conversation_id=CONVERSATION,
        route_session_id=ROUTE_SESSION,
        source_id=sid,
        source_revision_id=rid,
    ) is None
    active_service = replace(expired_service, ttl=timedelta(minutes=30))
    replacement = active_service.create(
        owner_id=OWNER,
        conversation_id=CONVERSATION,
        route_session_id=ROUTE_SESSION,
        source_id=sid,
        source_revision_id=rid,
        profile_id=pid,
        curation_id=cid,
        request_text="List orders after expiry",
    )
    assert replacement.plan_id != expired.plan_id
    assert len(engine.calls) == 2
    records = list(
        (
            active_service.sources.revision_dir(owner_key=str(OWNER), source_id=sid)
            / "api-route-plans"
            / "records"
        ).glob("*.json")
    )
    assert len(records) == 2


def test_corrupt_record_fails_without_rerouting(tmp_path: Path) -> None:
    corrupt_service, _engine, sid, rid, pid, cid = _service(tmp_path)
    saved = corrupt_service.create(
        owner_id=OWNER,
        conversation_id=CONVERSATION,
        route_session_id=ROUTE_SESSION,
        source_id=sid,
        source_revision_id=rid,
        profile_id=pid,
        curation_id=cid,
        request_text="List orders",
    )
    path = (
        corrupt_service.sources.revision_dir(owner_key=str(OWNER), source_id=sid)
        / "api-route-plans"
        / "records"
        / f"{saved.record_id}.json"
    )
    document = json.loads(path.read_text(encoding="utf-8"))
    document["request_text"] = "tampered request"
    path.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(ApiRoutePlanError, match="inconsistent"):
        corrupt_service.current(
            owner_id=OWNER,
            conversation_id=CONVERSATION,
            route_session_id=ROUTE_SESSION,
            source_id=sid,
            source_revision_id=rid,
        )


def test_unresolved_multi_step_plan_is_atomic_and_never_executes(
    tmp_path: Path,
) -> None:
    service, engine, source_id, revision_id, profile_id, curation_id = _service(tmp_path)
    plan = service.create(
        owner_id=OWNER,
        conversation_id=CONVERSATION,
        route_session_id=ROUTE_SESSION,
        source_id=source_id,
        source_revision_id=revision_id,
        profile_id=profile_id,
        curation_id=curation_id,
        request_text="List orders then confirm",
    )
    assert plan.state == "needs_input"
    assert len(plan.steps) == 2
    assert plan.api_call_count == 0
    assert len(engine.calls) == 1
    assert not hasattr(service, "credentials")
    assert not hasattr(service, "transport")


def _service(
    tmp_path: Path,
) -> tuple[ApiRoutePlanService, FakePlanningEngine, str, str, str, str]:
    repository = LocalSourceRepository(tmp_path / "sources")
    prepared = repository.begin_source(
        owner_key=str(OWNER),
        connector_key="api",
        display_name="Widgets",
        original_filename="widgets.yaml",
        content=b"openapi: 3.0.3\npaths: {}\n",
    )
    repository.mark_running(
        owner_key=str(OWNER),
        source_id=prepared.source.source_id,
        revision_id=prepared.revision.revision_id,
    )
    ready = repository.mark_ready(
        owner_key=str(OWNER),
        source_id=prepared.source.source_id,
        revision_id=prepared.revision.revision_id,
        summary={
            "endpoint_count": 2,
            "revision_kind": "reviewed_api_contract",
            "final_canonical_sha256": "6fca793be700dfb8bf511c2217d72cf97abf2f6cba08fbc2cd26ef0369b8f3f6",
            "approved_by_owner_id": str(OWNER),
        },
    )
    graph_dir = prepared.artifact_dir / "graph"
    graph_dir.mkdir(parents=True)
    (graph_dir / "semantic_graph.json").write_text(
        json.dumps(
            {
                "nodes": [
                    _operation("listWidgets", "GET", "/widgets", "list"),
                    _operation("createWidget", "POST", "/widgets", "create"),
                ],
                "edges": [],
                "cards": [],
                "metadata": {},
            }
        ),
        encoding="utf-8",
    )
    curations = ApiOperationCurationService(repository)
    inventory = curations.inspect(
        owner_id=OWNER,
        source_id=ready.source_id,
        source_revision_id=ready.revision.revision_id,
    )
    curation = curations.save(
        owner_id=OWNER,
        source_id=ready.source_id,
        source_revision_id=ready.revision.revision_id,
        inventory_fingerprint=inventory.inventory_fingerprint,
        included_operation_ids=("listWidgets",),
        excluded_operation_ids=("createWidget",),
        expected_current_curation_id=None,
    )
    profiles = ApiConnectionProfileRepository(repository)
    profile = profiles.create(
        owner_key=str(OWNER),
        source_id=ready.source_id,
        profile_name="Local",
        environment="development",
        base_url="http://127.0.0.1:9100",
        authentication_method=ApiAuthenticationMethod.API_KEY,
        credential_name="x-publishable-api-key",
        credential_reference_id=uuid.UUID("00000000-0000-0000-0000-000000000003"),
        credential_version=1,
    )
    engine = FakePlanningEngine()
    return (
        ApiRoutePlanService(
            sources=repository,
            curations=curations,
            profiles=profiles,
            engine=engine,  # type: ignore[arg-type]
        ),
        engine,
        ready.source_id,
        ready.revision.revision_id,
        profile.id,
        curation.id,
    )


def _operation(operation_id: str, method: str, path: str, operation_class: str):
    return {
        "id": f"api_operation:widgets:{operation_id}",
        "node_type": "api_operation",
        "label": f"{method} {path}",
        "endpoint_id": f"widgets:{operation_id}",
        "facets": {
            "method": method,
            "operation_class": operation_class,
            "operation_id": operation_id,
            "path": path,
        },
    }
