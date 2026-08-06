from __future__ import annotations

import json
import re
import secrets
import string
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol
from uuid import uuid4

import httpx

from .action_plan import EvaluationPlanError


class EvaluationConversationRunner(Protocol):
    def _send(self, client: httpx.Client, message: str) -> None: ...

    def _transcript(self, client: httpx.Client) -> list[dict[str, str]]: ...

    def _tester_turn(
        self,
        scenario: dict[str, Any],
        transcript: list[dict[str, str]],
    ) -> Any: ...

    def _await_run(
        self,
        client: httpx.Client,
        request_id: str,
    ) -> dict[str, Any]: ...


class HttpEvaluationActionRuntime:
    """Bind a generic Studio action plan to the real Corpus HTTP product path."""

    _SETUP_ADAPTERS = {
        "lounge.public",
        "lounge.public_unique_owner",
        "lounge.unknown_owner_email",
        "lounge.existing_verified_owner_signed_out",
        "lounge.existing_owner_signed_out",
        "lounge.valid_reset_link_with_active_session",
        "lounge.expired_reset_link",
        "lounge.authenticated_unverified_owner",
        "lounge.verification_limit_exhausted",
        "lounge.valid_verification_link",
        "lounge.invalid_verification_link",
        "workspace.authenticated_owner",
        "agents.empty_workspace",
        "agents.one_agent",
    }
    _PAYLOAD_ADAPTERS = {
        "lounge.valid_unique_owner",
        "lounge.valid_existing_owner_credentials",
        "lounge.existing_owner_email",
        "lounge.unknown_owner_email",
        "lounge.valid_new_password",
        "lounge.valid_verification_token",
        "lounge.invalid_verification_token",
        "agents.valid_new_agent",
        "agents.valid_edit",
    }

    @classmethod
    def registered_setup_adapters(cls) -> frozenset[str]:
        return frozenset(cls._SETUP_ADAPTERS)

    @classmethod
    def registered_payload_adapters(cls) -> frozenset[str]:
        return frozenset(cls._PAYLOAD_ADAPTERS)

    def __init__(
        self,
        *,
        runner: EvaluationConversationRunner,
        client: httpx.Client,
        definition: dict[str, Any],
        manifest_behaviors: list[dict[str, Any]],
    ) -> None:
        self.runner = runner
        self.client = client
        self.definition = definition
        self.manifest_behaviors = manifest_behaviors
        self.state: dict[str, Any] = {}
        self.conversation_id = ""
        self.starting_projection: dict[str, Any] = {}
        self.starting_authentication = ""
        self.starting_event_cursor = 0
        self.observed_surface_ids: set[str] = set()
        self.observed_suggested_action_labels: set[str] = set()

    def setup(self, adapter_id: str) -> dict[str, Any]:
        if adapter_id not in self._SETUP_ADAPTERS:
            raise EvaluationPlanError(
                f"Setup adapter {adapter_id!r} is not registered with a real product setup"
            )
        if adapter_id in {
            "lounge.public",
            "lounge.public_unique_owner",
            "lounge.unknown_owner_email",
        }:
            self._fresh_public_conversation()
        if adapter_id == "lounge.public_unique_owner":
            self.state.update(
                email=f"corpus-eval-{secrets.token_hex(10)}@example.com",
                password=_evaluation_password(),
                display_name="Corpus Evaluation Owner",
            )
        elif adapter_id == "lounge.unknown_owner_email":
            self.state["email"] = (
                f"corpus-eval-unknown-{secrets.token_hex(10)}@example.com"
            )
        elif adapter_id == "lounge.existing_owner_signed_out":
            self._prepare_existing_owner_signed_out(verified=False)
        elif adapter_id == "lounge.existing_verified_owner_signed_out":
            self._prepare_existing_owner_signed_out(verified=True)
        elif adapter_id == "lounge.authenticated_unverified_owner":
            self._prepare_authenticated_unverified_owner()
        elif adapter_id == "lounge.verification_limit_exhausted":
            self._prepare_verification_limit_exhausted()
        elif adapter_id == "lounge.valid_verification_link":
            self._prepare_verification_link(valid=True)
        elif adapter_id == "lounge.invalid_verification_link":
            self._prepare_verification_link(valid=False)
        elif adapter_id == "lounge.valid_reset_link_with_active_session":
            self._prepare_reset_link(consumed=False)
        elif adapter_id == "lounge.expired_reset_link":
            self._prepare_reset_link(consumed=True)
        elif adapter_id == "workspace.authenticated_owner":
            self._prepare_authenticated_workspace()
        elif adapter_id == "agents.empty_workspace":
            self._prepare_authenticated_workspace()
            self._dispatch(
                "workspace.open_agents",
                purpose="prepare-empty-agents",
                require_completed=True,
            )
        elif adapter_id == "agents.one_agent":
            self._prepare_one_agent()
        starting_behavior = self.definition.get("expectations", {}).get(
            "startingBehavior"
        )
        if isinstance(starting_behavior, str):
            setup_operations = _behavior_setup_operation_ids(
                starting_behavior,
                self.manifest_behaviors,
            )
            if setup_operations is None:
                observed_node = self._projection()["current"]["node_id"]
                expected_node = _behavior_node(
                    starting_behavior,
                    self.manifest_behaviors,
                )
                if observed_node == expected_node:
                    setup_operations = []
                else:
                    raise EvaluationPlanError(
                        f"{adapter_id!r} established {observed_node!r}, not "
                        f"{starting_behavior!r} ({expected_node!r})"
                    )
            for operation_id in setup_operations:
                self._dispatch(operation_id, purpose="setup", require_completed=True)
        self.starting_projection = self._projection()
        self.starting_authentication = self._authentication_state()
        self.starting_event_cursor = self._inspection_cursor()
        return {
            "adapter": adapter_id,
            "conversationId": self.conversation_id,
            "authentication": self.starting_authentication,
            "nodeId": self.starting_projection["current"]["node_id"],
            "preparedValues": sorted(self.state),
        }

    def send_authored_message(self, message: str) -> dict[str, Any]:
        self.runner._send(self.client, message)
        projection = self._projection()
        return {
            "sent": True,
            "nodeId": projection["current"]["node_id"],
            "sessionVersion": projection["session_version"],
        }

    def send_adaptive_message(self) -> dict[str, Any]:
        transcript = self.runner._transcript(self.client)
        tester = self.runner._tester_turn(self.definition, transcript)
        if tester.stop:
            return {"sent": False, "reason": tester.reason}
        self.runner._send(self.client, tester.message)
        projection = self._projection()
        return {
            "sent": True,
            "reason": tester.reason,
            "nodeId": projection["current"]["node_id"],
            "sessionVersion": projection["session_version"],
        }

    def invoke_suggested_action(
        self,
        *,
        step: dict[str, Any],
        binding: dict[str, Any],
    ) -> dict[str, Any]:
        operation_id = _required_binding_string(binding, "operation")
        projection = self._projection()
        suggested = {
            item.get("operation_id"): item.get("label")
            for item in projection.get("suggested_actions", [])
            if isinstance(item, dict)
        }
        if operation_id not in suggested:
            raise EvaluationPlanError(
                f"Suggested action {step.get('action')!r} is not projected for operation "
                f"{operation_id!r}; observed {sorted(value for value in suggested if value)}"
            )
        result = self._dispatch(
            operation_id,
            purpose=f"action-{step['id']}",
            require_completed=False,
        )
        expected_outcome = binding.get("expectedOutcome")
        return {
            "operationId": operation_id,
            "projectedLabel": suggested[operation_id],
            "disposition": result.get("disposition"),
            "failure": result.get("failure"),
            "outcome": result.get("outcome"),
            "expectedOutcome": expected_outcome,
            "outcomeMatched": (
                expected_outcome is None
                or result.get("outcome") == expected_outcome
            ),
        }

    def submit_surface(
        self,
        *,
        step: dict[str, Any],
        binding: dict[str, Any],
    ) -> dict[str, Any]:
        operation_id = _required_binding_string(binding, "operation")
        surface_id = _required_binding_string(binding, "surface")
        payload_adapter = _required_binding_string(binding, "payloadAdapter")
        projection = self._projection()
        surface = _projected_surface(projection, surface_id)
        payload = self._payload(payload_adapter)
        form_handle = _optional_surface_prop(surface, "form_handle")
        private_form_revision = None
        dispatch_arguments: dict[str, Any] = payload
        submission_mode = "public_arguments"
        if form_handle is not None:
            if not isinstance(form_handle, str) or not form_handle:
                raise EvaluationPlanError(
                    f"Projected surface {surface_id!r} has an invalid private form handle"
                )
            saved = self.client.put(
                f"/api/routedeck/private-forms/{form_handle}",
                json={
                    "request_id": f"eval-form-{uuid4().hex}",
                    "expected_session_version": projection["session_version"],
                    "value": payload,
                    "complete": True,
                },
            )
            _expect(saved, 200)
            private_form_revision = saved.json().get("revision")
            dispatch_arguments = {}
            submission_mode = "private_form"
        result = self._dispatch(
            operation_id,
            purpose=f"surface-{step['id']}",
            require_completed=False,
            arguments=dispatch_arguments,
        )
        expected_outcome = binding.get("expectedOutcome")
        return {
            "surfaceId": surface_id,
            "formHandle": form_handle,
            "payloadAdapter": payload_adapter,
            "payloadFields": sorted(payload),
            "privateFormRevision": private_form_revision,
            "submissionMode": submission_mode,
            "operationId": operation_id,
            "disposition": result.get("disposition"),
            "failure": result.get("failure"),
            "outcome": result.get("outcome"),
            "expectedOutcome": expected_outcome,
            "outcomeMatched": (
                expected_outcome is None
                or result.get("outcome") == expected_outcome
            ),
        }

    def checkpoint(
        self,
        *,
        label: str,
        state_assertions: list[str],
        binding: dict[str, Any],
    ) -> dict[str, Any]:
        projection = self._projection()
        inspection = _expect(
            self.client.get("/api/routedeck/inspect"), 200
        ).json()
        observed_state = self._observed_checkpoint_state()
        machine_assertions = _checkpoint_assertions(
            binding,
            node_id=projection["current"]["node_id"],
            authentication=self._authentication_state(),
            observed_state=observed_state,
        )
        return {
            "label": label,
            "authoredStateAssertions": state_assertions,
            "machineAssertions": machine_assertions,
            "machineAssertionsPassed": all(
                item["passed"] for item in machine_assertions
            ),
            "observedDomainState": observed_state,
            "authentication": self._authentication_state(),
            "nodeId": projection["current"]["node_id"],
            "sessionVersion": projection["session_version"],
            "projectionVersion": projection["projection_version"],
            "eventCursor": inspection.get("diagnostics", {}).get(
                "event_cursor", 0
            ),
            "surfaceIds": sorted(_projection_surface_ids(projection)),
            "suggestedActions": [
                {
                    "label": item.get("label"),
                    "operationId": item.get("operation_id"),
                }
                for item in projection.get("suggested_actions", [])
                if isinstance(item, dict)
            ],
        }

    def _prepare_authenticated_workspace(self) -> None:
        self._fresh_public_conversation()
        self._create_owner(
            email=f"corpus-eval-owner-{secrets.token_hex(10)}@example.com"
        )

    def _prepare_one_agent(self) -> None:
        self._prepare_authenticated_workspace()
        self._dispatch(
            "workspace.open_agents",
            purpose="prepare-one-agent-home",
            require_completed=True,
        )
        self._dispatch(
            "agents.open_create",
            purpose="prepare-one-agent-create",
            require_completed=True,
        )
        self.state["agent_name"] = "Evaluation Agent"
        self._dispatch(
            "agents.create_agent",
            purpose="prepare-one-agent-submit",
            require_completed=True,
            arguments={
                "name": self.state["agent_name"],
                "description": "Agent prepared by the live evaluator.",
                "instructions": "Complete the prepared evaluation task.",
            },
        )
        agents = _expect(self.client.get("/api/agents"), 200).json()["agents"]
        if len(agents) != 1:
            raise EvaluationPlanError(
                f"One-agent setup produced {len(agents)} agents"
            )
        self.state["agent_id"] = agents[0]["id"]
        self.state["agent_version"] = agents[0]["current_version"]

    def _observed_checkpoint_state(self) -> dict[str, Any]:
        observed: dict[str, Any] = {}
        if self._authentication_state() == "authenticated":
            agents_response = self.client.get("/api/agents")
            if agents_response.status_code == 200:
                agents = agents_response.json().get("agents", [])
                observed["agents.count"] = len(agents)
                if agents:
                    observed["agents.latest.id"] = agents[0].get("id")
                    observed["agents.latest.name"] = agents[0].get("name")
                    observed["agents.latest.current_version"] = agents[0].get(
                        "current_version"
                    )
                    observed["agents.latest.instructions"] = agents[0].get(
                        "instructions"
                    )
            workspace_response = self.client.get("/api/workspace/overview")
            if workspace_response.status_code == 200:
                workspace = workspace_response.json()
                observed["workspace.agent_count"] = workspace.get("agent_count")
                observed["workspace.agents.status"] = workspace.get(
                    "agents", {}
                ).get("status")
                observed["workspace.sources.status"] = workspace.get(
                    "sources", {}
                ).get("status")
                observed["workspace.recent_activity.status"] = workspace.get(
                    "recent_activity", {}
                ).get("status")
        return observed

    def _fresh_public_conversation(self) -> None:
        self.client.headers.pop("X-Corpus-Conversation-ID", None)
        anonymous = _expect(self.client.post("/api/auth/anonymous"), 201).json()
        self.client.headers["Authorization"] = (
            f"Bearer {anonymous['access_token']}"
        )
        created = _expect(self.client.post("/api/conversations", json={}), 201).json()
        self.conversation_id = created["id"]
        self.client.headers["X-Corpus-Conversation-ID"] = self.conversation_id
        active_run = created.get("active_run")
        if active_run is not None:
            self.runner._await_run(self.client, active_run["request_id"])

    def _prepare_existing_owner_signed_out(self, *, verified: bool) -> None:
        mailbox = SyncEvaluationMailbox.create() if verified else None
        try:
            self._fresh_public_conversation()
            self._create_owner(
                email=(
                    mailbox.address
                    if mailbox is not None
                    else f"corpus-eval-owner-{secrets.token_hex(10)}@example.com"
                )
            )
            if mailbox is not None:
                self._verify_current_owner(mailbox)
            _expect(self.client.post("/api/auth/sign-out"), 204)
            self._fresh_public_conversation()
        finally:
            if mailbox is not None:
                mailbox.close()

    def _prepare_authenticated_unverified_owner(self) -> None:
        self._fresh_public_conversation()
        self._create_owner(
            email=f"corpus-eval-owner-{secrets.token_hex(10)}@example.com"
        )
        self._open_verification_pending()

    def _prepare_verification_limit_exhausted(self) -> None:
        mailbox = SyncEvaluationMailbox.create()
        try:
            self._fresh_public_conversation()
            self._create_owner(email=mailbox.address)
            self._open_verification_pending()
            for index in range(3):
                result = self._dispatch(
                    "lounge.request_verification_delivery",
                    purpose=f"prepare-verification-limit-{index}",
                    require_completed=False,
                )
                if result.get("disposition") != "completed":
                    raise EvaluationPlanError(
                        "Could not exhaust the verification limit through accepted "
                        f"product requests: {result}"
                    )
        finally:
            mailbox.close()

    def _prepare_verification_link(self, *, valid: bool) -> None:
        mailbox = SyncEvaluationMailbox.create()
        try:
            self._fresh_public_conversation()
            self._create_owner(email=mailbox.address)
            if valid:
                sent_after = time.time()
                self._open_verification_pending()
                result = self._dispatch(
                    "lounge.request_verification_delivery",
                    purpose="prepare-verification-link",
                    require_completed=False,
                )
                if result.get("disposition") != "completed":
                    raise EvaluationPlanError(
                        f"Verification setup request failed: {result}"
                    )
                message = mailbox.wait_for_message(
                    subject="Verify your Corpus email",
                    after=sent_after,
                )
                self.state["verification_token"] = message.token_for("/verify")
            else:
                self.state["verification_token"] = (
                    f"invalid-evaluation-token-{secrets.token_hex(12)}"
                )
            self._navigate("/verify")
        finally:
            mailbox.close()

    def _prepare_reset_link(self, *, consumed: bool) -> None:
        mailbox = SyncEvaluationMailbox.create()
        try:
            self._fresh_public_conversation()
            self._create_owner(email=mailbox.address)
            # Switch principals without signing out so the valid-reset case proves
            # revocation of a genuinely active owner session.
            self._fresh_public_conversation()
            self._navigate("/forgot-password")
            sent_after = time.time()
            self._save_private_form(
                surface_id="lounge.forgot_password",
                payload={"email": mailbox.address},
            )
            result = self._dispatch(
                "lounge.request_password_reset",
                purpose="prepare-reset-link",
                require_completed=False,
            )
            if result.get("disposition") != "completed":
                raise EvaluationPlanError(f"Password-reset setup failed: {result}")
            message = mailbox.wait_for_message(
                subject="Reset your Corpus password",
                after=sent_after,
            )
            token = message.token_for("/reset-password")
            if consumed:
                self._navigate("/reset-password")
                self._save_private_form(
                    surface_id="lounge.reset_password",
                    payload={
                        "token": token,
                        "new_password": _evaluation_password(),
                    },
                )
                consumed_result = self._dispatch(
                    "lounge.change_owner_password",
                    purpose="consume-reset-link",
                    require_completed=False,
                )
                if consumed_result.get("disposition") != "completed":
                    raise EvaluationPlanError(
                        f"Could not consume reset link during setup: {consumed_result}"
                    )
                self._fresh_public_conversation()
                self.state["reset_token_state"] = "already_used"
            self.state["reset_token"] = token
            self.state["new_password"] = _evaluation_password()
            self._navigate("/reset-password")
        finally:
            mailbox.close()

    def _create_owner(self, *, email: str) -> None:
        self.state.update(
            email=email,
            password=_evaluation_password(),
            display_name="Corpus Evaluation Owner",
        )
        self._dispatch(
            "lounge.arrival.open_registration",
            purpose="prepare-owner-registration",
            require_completed=True,
        )
        self._save_private_form(
            surface_id="lounge.register",
            payload={
                "email": self.state["email"],
                "password": self.state["password"],
                "display_name": self.state["display_name"],
            },
        )
        result = self._dispatch(
            "lounge.create_owner_account",
            purpose="prepare-owner-create",
            require_completed=False,
        )
        if result.get("disposition") != "completed":
            raise EvaluationPlanError(f"Owner setup failed: {result}")

    def _verify_current_owner(self, mailbox: SyncEvaluationMailbox) -> None:
        sent_after = time.time()
        self._open_verification_pending()
        result = self._dispatch(
            "lounge.request_verification_delivery",
            purpose="prepare-owner-verification",
            require_completed=False,
        )
        if result.get("disposition") != "completed":
            raise EvaluationPlanError(f"Owner verification request failed: {result}")
        message = mailbox.wait_for_message(
            subject="Verify your Corpus email",
            after=sent_after,
        )
        self._navigate("/verify")
        self._save_private_form(
            surface_id="lounge.verify_email",
            payload={"token": message.token_for("/verify")},
        )
        confirmed = self._dispatch(
            "lounge.confirm_owner_email",
            purpose="prepare-owner-verification-confirm",
            require_completed=False,
        )
        if confirmed.get("disposition") != "completed":
            raise EvaluationPlanError(f"Owner verification failed: {confirmed}")

    def _navigate(self, path: str) -> dict[str, Any]:
        projection = self._projection()
        response = self.client.post(
            "/api/routedeck/navigation",
            json={
                "request_id": f"eval-navigation-{uuid4().hex}",
                "expected_session_version": projection["session_version"],
                "intent": {"kind": "open_path", "path": path},
            },
        )
        return _expect(response, 200).json()["projection"]

    def _open_verification_pending(self) -> None:
        result = self._dispatch(
            "workspace.open_verification",
            purpose="prepare-open-verification",
            require_completed=False,
        )
        if result.get("disposition") != "completed":
            raise EvaluationPlanError(
                f"Could not open verification through Workspace: {result}"
            )

    def _save_private_form(
        self,
        *,
        surface_id: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        projection = self._projection()
        surface = _projected_surface(projection, surface_id)
        form_handle = _surface_prop(surface, "form_handle")
        if not isinstance(form_handle, str) or not form_handle:
            raise EvaluationPlanError(
                f"Projected surface {surface_id!r} has no private form handle"
            )
        response = self.client.put(
            f"/api/routedeck/private-forms/{form_handle}",
            json={
                "request_id": f"eval-form-{uuid4().hex}",
                "expected_session_version": projection["session_version"],
                "value": payload,
                "complete": True,
            },
        )
        return _expect(response, 200).json()

    def _projection(self) -> dict[str, Any]:
        projection = _expect(
            self.client.get("/api/routedeck/session"), 200
        ).json()["projection"]
        self.observed_surface_ids.update(_projection_surface_ids(projection))
        self.observed_suggested_action_labels.update(
            item["label"]
            for item in projection.get("suggested_actions", [])
            if isinstance(item, dict) and isinstance(item.get("label"), str)
        )
        return projection

    def _inspection_cursor(self) -> int:
        return int(
            _expect(self.client.get("/api/routedeck/inspect"), 200)
            .json()
            .get("diagnostics", {})
            .get("event_cursor", 0)
        )

    def _authentication_state(self) -> str:
        payload = _expect(self.client.get("/api/auth/session"), 200).json()
        return "public" if payload.get("type") == "anonymous" else "authenticated"

    def _payload(self, adapter_id: str) -> dict[str, Any]:
        if adapter_id not in self._PAYLOAD_ADAPTERS:
            raise EvaluationPlanError(
                f"Payload adapter {adapter_id!r} is not registered with real values"
            )
        if adapter_id == "lounge.valid_unique_owner":
            return {
                "email": self.state["email"],
                "password": self.state["password"],
                "display_name": self.state["display_name"],
            }
        if adapter_id == "lounge.unknown_owner_email":
            return {"email": self.state["email"]}
        if adapter_id == "lounge.valid_existing_owner_credentials":
            return {
                "email": self.state["email"],
                "password": self.state["password"],
            }
        if adapter_id == "lounge.existing_owner_email":
            return {"email": self.state["email"]}
        if adapter_id == "lounge.valid_new_password":
            return {
                "token": self.state["reset_token"],
                "new_password": self.state["new_password"],
            }
        if adapter_id == "lounge.valid_verification_token":
            return {"token": self.state["verification_token"]}
        if adapter_id == "lounge.invalid_verification_token":
            return {"token": self.state["verification_token"]}
        if adapter_id == "agents.valid_new_agent":
            return {
                "name": "Evaluation Created Agent",
                "description": "Created through the live feature evaluator.",
                "instructions": "Complete the owner task and report evidence.",
            }
        if adapter_id == "agents.valid_edit":
            return {
                "agent_id": self.state["agent_id"],
                "expected_version": self.state["agent_version"],
                "name": self.state["agent_name"],
                "description": "Agent prepared by the live evaluator.",
                "instructions": "Complete the owner task and retain evidence.",
            }
        raise AssertionError(f"Unhandled registered payload adapter: {adapter_id}")

    def _dispatch(
        self,
        operation_id: str,
        *,
        purpose: str,
        require_completed: bool,
        arguments: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        projection = self._projection()
        response = self.client.post(
            "/api/routedeck/dispatch",
            json={
                "request_id": f"eval-{purpose}-{uuid4().hex}",
                "expected_session_version": projection["session_version"],
                "operation_id": operation_id,
                "arguments": arguments or {},
            },
        )
        result = _operation_result(response)
        self._apply_credential_transition(response)
        if require_completed and result.get("disposition") != "completed":
            raise EvaluationPlanError(
                f"Setup operation {operation_id!r} did not complete: {result}"
            )
        return result

    def _apply_credential_transition(self, response: httpx.Response) -> None:
        serialized = response.headers.get("X-Corpus-Auth-Tokens")
        if serialized is not None:
            credentials = json.loads(serialized)
            self.client.headers["Authorization"] = (
                f"Bearer {credentials['access_token']}"
            )
            self.state["issuedCredentials"] = True
        if response.headers.get("X-Corpus-Auth-Revoked") == "true":
            self.client.headers.pop("Authorization", None)
            self.state["credentialsRevoked"] = True


def _projected_surface(
    projection: dict[str, Any], surface_id: str
) -> dict[str, Any]:
    for value in projection.get("surfaces", {}).values():
        items = value if isinstance(value, list) else [value]
        for item in items:
            if isinstance(item, dict) and item.get("surface_id") == surface_id:
                return item
    raise EvaluationPlanError(
        f"Surface {surface_id!r} is not projected; observed "
        f"{sorted(_projection_surface_ids(projection))}"
    )


def _projection_surface_ids(projection: dict[str, Any]) -> set[str]:
    observed: set[str] = set()
    for value in projection.get("surfaces", {}).values():
        items = value if isinstance(value, list) else [value]
        for item in items:
            if isinstance(item, dict) and isinstance(item.get("surface_id"), str):
                observed.add(item["surface_id"])
    return observed


def _surface_prop(surface: dict[str, Any], name: str) -> Any:
    value = _optional_surface_prop(surface, name)
    if value is None:
        raise EvaluationPlanError(
            f"Projected surface requires exactly one {name!r} prop"
        )
    return value


def _optional_surface_prop(surface: dict[str, Any], name: str) -> Any:
    props = surface.get("props", [])
    if not isinstance(props, list):
        raise EvaluationPlanError("Projected surface props must be a list")
    matches = [
        item.get("value")
        for item in props
        if isinstance(item, dict) and item.get("name") == name
    ]
    if len(matches) > 1:
        raise EvaluationPlanError(
            f"Projected surface has multiple {name!r} props"
        )
    return matches[0] if matches else None


def _checkpoint_assertions(
    binding: dict[str, Any],
    *,
    node_id: str,
    authentication: str,
    observed_state: dict[str, Any],
) -> list[dict[str, Any]]:
    assertions: list[dict[str, Any]] = []
    expected_node = binding.get("node")
    if expected_node is not None:
        if not isinstance(expected_node, str) or not expected_node:
            raise EvaluationPlanError("Checkpoint node must be a non-empty string")
        assertions.append(
            {
                "path": "projection.current.node_id",
                "expected": expected_node,
                "observed": node_id,
                "passed": node_id == expected_node,
            }
        )
    expected_authentication = binding.get("authentication")
    if expected_authentication is not None:
        if expected_authentication not in {"public", "authenticated"}:
            raise EvaluationPlanError(
                "Checkpoint authentication must be public or authenticated"
            )
        assertions.append(
            {
                "path": "authentication",
                "expected": expected_authentication,
                "observed": authentication,
                "passed": authentication == expected_authentication,
            }
        )
    expected_state = binding.get("state", {})
    if not isinstance(expected_state, dict):
        raise EvaluationPlanError("Checkpoint state must be an object")
    for path, expected in expected_state.items():
        if not isinstance(path, str) or not path:
            raise EvaluationPlanError(
                "Checkpoint state paths must be non-empty strings"
            )
        observed = observed_state.get(path)
        assertions.append(
            {
                "path": path,
                "expected": expected,
                "observed": observed,
                "passed": path in observed_state and observed == expected,
            }
        )
    if binding and not assertions:
        raise EvaluationPlanError(
            "Checkpoint binding must declare node, authentication, or state"
        )
    return assertions


_PUBLIC_BEHAVIOR_SETUP: dict[str, tuple[tuple[str, str], ...] | None] = {
    "Arrive in the Lounge": (),
    "Ask Lounge for product help": (
        ("Arrive in the Lounge", "Start product help"),
    ),
    "Create an owner account": (
        ("Arrive in the Lounge", "Open owner registration"),
    ),
    "Sign in": (("Arrive in the Lounge", "Open owner sign-in"),),
    "Request password recovery": (
        ("Arrive in the Lounge", "Open owner sign-in"),
        ("Sign in", "Open password recovery"),
    ),
    "Set a new password": None,
    "Resend email verification": None,
    "Confirm email verification": None,
}


def _behavior_setup_operation_ids(
    design_behavior: str,
    manifest_behaviors: list[dict[str, Any]],
) -> list[str] | None:
    path = _PUBLIC_BEHAVIOR_SETUP.get(design_behavior)
    if path is None:
        return None
    by_behavior = {item["designBehavior"]: item for item in manifest_behaviors}
    return [
        by_behavior[behavior]["operations"][operation]
        for behavior, operation in path
    ]


def _behavior_node(
    design_behavior: str,
    manifest_behaviors: list[dict[str, Any]],
) -> str:
    for behavior in manifest_behaviors:
        if behavior.get("designBehavior") == design_behavior:
            node = behavior.get("node")
            if isinstance(node, str) and node:
                return node
    raise EvaluationPlanError(
        f"No manifest node is mapped for behavior {design_behavior!r}"
    )


def _required_binding_string(binding: dict[str, Any], name: str) -> str:
    value = binding.get(name)
    if not isinstance(value, str) or not value:
        raise EvaluationPlanError(f"Evaluation binding requires {name!r}")
    return value


def _evaluation_password() -> str:
    return f"Corpus-Eval-{secrets.token_hex(12)}!7a"


def _expect(response: httpx.Response, status: int) -> httpx.Response:
    if response.status_code != status:
        raise RuntimeError(
            f"{response.request.method} {response.request.url} returned "
            f"{response.status_code}: {response.text[:500]}"
        )
    return response


def _operation_result(response: httpx.Response) -> dict[str, Any]:
    try:
        payload = response.json()
    except ValueError:
        payload = None
    if (
        not isinstance(payload, dict)
        or not isinstance(payload.get("disposition"), str)
        or not isinstance(payload.get("operation_id"), str)
    ):
        raise RuntimeError(
            f"{response.request.method} {response.request.url} returned "
            f"{response.status_code} without an operation result: {response.text[:500]}"
        )
    return payload


@dataclass(frozen=True)
class EvaluationMailboxMessage:
    text: str

    def token_for(self, path: str) -> str:
        match = re.search(
            rf"https?://[^\s<>]+{re.escape(path)}#token=([^\s<>]+)",
            self.text,
        )
        if match is None:
            raise EvaluationPlanError(
                f"Evaluation mailbox message contained no {path!r} token link"
            )
        return match.group(1).rstrip(".,)")


class SyncEvaluationMailbox:
    """Synchronous Mail.tm adapter used only for explicit live evaluations."""

    api_url = "https://api.mail.tm"

    def __init__(
        self,
        *,
        client: httpx.Client,
        address: str,
        account_id: str,
        token: str,
    ) -> None:
        self.client = client
        self.address = address
        self.account_id = account_id
        self.token = token

    @classmethod
    def create(cls) -> SyncEvaluationMailbox:
        client = httpx.Client(
            timeout=20.0,
            headers={"User-Agent": "Corpus-Action-Evaluation/1.0"},
        )
        try:
            domains = _expect(client.get(f"{cls.api_url}/domains?page=1"), 200)
            values = domains.json().get("hydra:member", [])
            if not values:
                raise EvaluationPlanError("Mail.tm returned no available domains")
            local = "corpus-eval-" + "".join(
                secrets.choice(string.ascii_lowercase + string.digits)
                for _ in range(14)
            )
            address = f"{local}@{values[0]['domain']}"
            password = _evaluation_password()
            created: httpx.Response | None = None
            for attempt in range(4):
                created = client.post(
                    f"{cls.api_url}/accounts",
                    json={"address": address, "password": password},
                )
                if created.status_code != 429:
                    break
                time.sleep(5.0 * (attempt + 1))
            assert created is not None
            _expect(created, 201)
            authenticated = _expect(
                client.post(
                    f"{cls.api_url}/token",
                    json={"address": address, "password": password},
                ),
                200,
            )
            return cls(
                client=client,
                address=address,
                account_id=created.json()["id"],
                token=authenticated.json()["token"],
            )
        except Exception:
            client.close()
            raise

    def wait_for_message(
        self,
        *,
        subject: str,
        after: float,
        timeout_seconds: float = 90.0,
    ) -> EvaluationMailboxMessage:
        deadline = time.monotonic() + timeout_seconds
        headers = {"Authorization": f"Bearer {self.token}"}
        while time.monotonic() < deadline:
            listing = _expect(
                self.client.get(f"{self.api_url}/messages?page=1", headers=headers),
                200,
            )
            for item in listing.json().get("hydra:member", []):
                if item.get("subject") != subject:
                    continue
                created_at = item.get("createdAt")
                if (
                    isinstance(created_at, str)
                    and datetime.fromisoformat(
                        created_at.replace("Z", "+00:00")
                    ).timestamp()
                    < after
                ):
                    continue
                detail = _expect(
                    self.client.get(
                        f"{self.api_url}/messages/{item['id']}",
                        headers=headers,
                    ),
                    200,
                ).json()
                return EvaluationMailboxMessage(text=detail.get("text") or "")
            time.sleep(1.0)
        raise EvaluationPlanError(
            f"Mail.tm did not receive {subject!r} within {timeout_seconds:.0f} seconds"
        )

    def close(self) -> None:
        try:
            response = self.client.delete(
                f"{self.api_url}/accounts/{self.account_id}",
                headers={"Authorization": f"Bearer {self.token}"},
            )
            if response.status_code != 204:
                raise EvaluationPlanError(
                    f"Mail.tm cleanup returned HTTP {response.status_code}"
                )
        finally:
            self.client.close()


__all__ = ["HttpEvaluationActionRuntime"]
