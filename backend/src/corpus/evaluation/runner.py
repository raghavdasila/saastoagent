from __future__ import annotations

import hashlib
import json
import re
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import httpx
from langchain_openai import ChatOpenAI
from ollama import Client
from pydantic import SecretStr
from pydantic import BaseModel, ConfigDict


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class TesterTurn(_StrictModel):
    stop: bool
    reason: str
    message: str


class CriterionDecision(_StrictModel):
    criterion: str
    passed: bool
    rationale: str


class ForbiddenDecision(_StrictModel):
    criterion: str
    observed: bool
    rationale: str


class JudgeResult(_StrictModel):
    required: list[CriterionDecision]
    forbidden: list[ForbiddenDecision]
    overall_pass: bool
    rationale: str


class LoungeEvaluationRunner:
    """Execute Studio-owned Lounge conversations through the real Corpus HTTP path."""

    def __init__(
        self,
        *,
        repository: Path,
        base_url: str,
        origin: str,
        model_provider: str,
        corpus_model: str,
        tester_model: str,
        judge_model: str,
        ollama_url: str | None = None,
        openai_api_key: SecretStr | None = None,
        openai_reasoning_effort: str = "low",
        max_adaptive_turns: int = 2,
    ) -> None:
        self.repository = repository
        self.base_url = base_url.rstrip("/")
        self.origin = origin
        self.model_provider = model_provider
        self.corpus_model = corpus_model
        self.tester_model = tester_model
        self.judge_model = judge_model
        self.openai_reasoning_effort = openai_reasoning_effort
        self.max_adaptive_turns = max_adaptive_turns
        self.ollama: Client | None = None
        self.openai_api_key = openai_api_key
        if model_provider == "ollama":
            if ollama_url is None:
                raise ValueError("ollama_url is required for Ollama evaluation")
            self.ollama = Client(host=ollama_url.rstrip("/"), timeout=180.0)
        elif model_provider == "openai":
            if openai_api_key is None:
                raise ValueError("openai_api_key is required for OpenAI evaluation")
        else:
            raise ValueError(f"Unsupported evaluation provider: {model_provider}")
        self.design_path = repository / "docs/corpus-agent-design/workbench/design-state.json"
        self.manifest_path = repository / "contracts/corpus-agent-design-routedeck-manifest.json"
        self.results_root = repository / ".runtime/evaluations"

    def run(
        self,
        scenario_id: str | None = None,
        *,
        evaluation_level: str = "conversation",
    ) -> dict[str, Any]:
        design = _load_json(self.design_path)
        manifest = _load_json(self.manifest_path)
        lounge = next(item for item in design["features"] if item["name"] == "Lounge")
        if evaluation_level == "conversation":
            scenarios = [
                item for item in lounge["conversationEvals"] if item["enabled"]
            ]
        elif evaluation_level == "behavior":
            scenarios = [
                {**case, "designBehavior": story["title"]}
                for story in lounge["stories"]
                for case in story["behaviorEvals"]
                if case["enabled"]
            ]
        else:
            raise ValueError(f"Unsupported evaluation level: {evaluation_level}")
        if scenario_id is not None:
            scenarios = [item for item in scenarios if item["id"] == scenario_id]
            if not scenarios:
                raise ValueError(
                    f"Unknown enabled Lounge {evaluation_level} evaluation: {scenario_id}"
                )
        lounge_manifest = next(
            item for item in manifest["features"] if item["designFeature"] == "Lounge"
        )
        behavior_nodes = {
            item["designBehavior"]: item["node"]
            for item in lounge_manifest["behaviors"]
        }
        surface_ids = {
            design_name: runtime_id
            for behavior in lounge_manifest["behaviors"]
            for design_name, runtime_id in behavior["surfaces"].items()
        }
        run_id = f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}-{uuid4().hex[:10]}"
        started = datetime.now(UTC).isoformat()
        try:
            with httpx.Client(base_url=self.base_url, headers={"Origin": self.origin}, timeout=180.0) as client:
                _expect(client.get("/readyz"), 200)
                anonymous = client.post("/api/auth/anonymous")
                _expect(anonymous, 201)
                client.headers["Authorization"] = f"Bearer {anonymous.json()['access_token']}"
                if evaluation_level == "conversation":
                    results = [
                        self._run_scenario(
                            client,
                            item,
                            behavior_nodes,
                            surface_ids,
                        )
                        for item in scenarios
                    ]
                else:
                    results = [
                        self._run_behavior_case(
                            client,
                            item,
                            behavior_nodes,
                            surface_ids,
                            lounge_manifest["behaviors"],
                        )
                        for item in scenarios
                    ]
        except Exception as error:
            results = [
                {
                    "evaluationId": item["id"],
                    "title": item["title"],
                    "status": "infrastructure_failure",
                    "definitionSha256": _json_sha256(item),
                    "error": f"{type(error).__name__}: {error}",
                }
                for item in scenarios
            ]
        completed = datetime.now(UTC).isoformat()
        artifact = {
            "schema": "corpus.self-evaluation.v1",
            "runId": run_id,
            "evaluationLevel": evaluation_level,
            "status": "passed" if results and all(item["status"] == "passed" for item in results) else "failed",
            "startedAt": started,
            "completedAt": completed,
            "identities": {
                "designSha256": _sha256(self.design_path),
                "manifestSha256": _sha256(self.manifest_path),
                "corpusRevision": _git(self.repository, "rev-parse", "HEAD"),
                "corpusWorktreeSha256": _git_diff_sha256(self.repository),
                "routeDeckRevision": _git(self.repository.parent / "routedeck", "rev-parse", "HEAD"),
                "routeDeckWorktreeSha256": _git_diff_sha256(self.repository.parent / "routedeck"),
                "runtime": self.base_url,
                "corpusModel": self.corpus_model,
                "tester": {
                    "provider": self.model_provider,
                    "model": self.tester_model,
                    "reasoningEffort": self.openai_reasoning_effort
                    if self.model_provider == "openai"
                    else None,
                },
                "judge": {
                    "provider": self.model_provider,
                    "model": self.judge_model,
                    "reasoningEffort": self.openai_reasoning_effort
                    if self.model_provider == "openai"
                    else None,
                    "rubric": "corpus-semantic-v1",
                },
            },
            "results": results,
        }
        directory = self.results_root / run_id
        directory.mkdir(parents=True, exist_ok=False)
        artifact_path = directory / "result.json"
        artifact_path.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
        self._update_latest(artifact, artifact_path)
        return artifact

    def _run_behavior_case(
        self,
        client: httpx.Client,
        case: dict[str, Any],
        behavior_nodes: dict[str, str],
        surface_ids: dict[str, str],
        manifest_behaviors: list[dict[str, Any]],
    ) -> dict[str, Any]:
        definition = {
            key: value for key, value in case.items() if key != "designBehavior"
        }
        setup_operation_ids = _behavior_setup_operation_ids(
            case["designBehavior"], manifest_behaviors
        )
        if setup_operation_ids is None:
            return {
                "evaluationId": case["id"],
                "title": case["title"],
                "status": "prerequisite_blocked",
                "definitionSha256": _json_sha256(definition),
                "blocker": (
                    f"{case['designBehavior']} requires authenticated state or a real "
                    "one-time product token; the runner does not fabricate either."
                ),
            }
        try:
            listed = _expect(client.get("/api/conversations"), 200).json()[
                "conversations"
            ]
            created = (
                client.post("/api/conversations", json={})
                if not listed
                else client.post(f"/api/conversations/{listed[0]['id']}/replacement")
            )
            _expect(created, 201)
            conversation = created.json()
            client.headers["X-Corpus-Conversation-ID"] = conversation["id"]
            self._await_run(client, conversation["active_run"]["request_id"])
            for operation_id in setup_operation_ids:
                self._dispatch(client, operation_id)
            starting_projection = _expect(
                client.get("/api/routedeck/session"), 200
            ).json()["projection"]
            self._send(client, case["input"])
            transcript = self._transcript(client)
            projection = _expect(
                client.get("/api/routedeck/session"), 200
            ).json()["projection"]
            inspection = _expect(client.get("/api/routedeck/inspect"), 200).json()
            deterministic = _deterministic_assertions(
                case,
                behavior_nodes,
                projection,
                transcript,
                starting_projection=starting_projection,
                surface_ids=surface_ids,
            )
            judge = self._judge_behavior(case, transcript, deterministic)
            semantic_pass = (
                all(item.passed for item in judge.required)
                and not any(item.observed for item in judge.forbidden)
                and judge.overall_pass
            )
            passed = all(item["passed"] for item in deterministic) and semantic_pass
            return {
                "evaluationId": case["id"],
                "title": case["title"],
                "designBehavior": case["designBehavior"],
                "status": "passed" if passed else "failed",
                "definitionSha256": _json_sha256(definition),
                "conversationId": conversation["id"],
                "transcript": transcript,
                "deterministicAssertions": deterministic,
                "judge": judge.model_dump(mode="json"),
                "evidence": {
                    "startingProjection": starting_projection,
                    "projection": projection,
                    "routeTraces": inspection.get("route_traces", []),
                    "invocationTraceHashes": [
                        item.get("model_boundary_request", {}).get("sha256")
                        for item in inspection.get("invocation_traces", {}).get(
                            "traces", []
                        )
                    ],
                },
            }
        except Exception as error:
            return {
                "evaluationId": case["id"],
                "title": case["title"],
                "designBehavior": case["designBehavior"],
                "status": "infrastructure_failure",
                "definitionSha256": _json_sha256(definition),
                "error": f"{type(error).__name__}: {error}",
            }

    def _run_scenario(
        self,
        client: httpx.Client,
        scenario: dict[str, Any],
        behavior_nodes: dict[str, str],
        surface_ids: dict[str, str],
    ) -> dict[str, Any]:
        try:
            listed = _expect(client.get("/api/conversations"), 200).json()["conversations"]
            created = (
                client.post("/api/conversations", json={})
                if not listed
                else client.post(f"/api/conversations/{listed[0]['id']}/replacement")
            )
            _expect(created, 201)
            conversation = created.json()
            client.headers["X-Corpus-Conversation-ID"] = conversation["id"]
            self._await_run(client, conversation["active_run"]["request_id"])
            starting_projection = _expect(
                client.get("/api/routedeck/session"), 200
            ).json()["projection"]
            self._send(client, scenario["openingMessage"])
            for _ in range(min(self.max_adaptive_turns, scenario["maxTurns"] - 1)):
                transcript = self._transcript(client)
                tester = self._tester_turn(scenario, transcript)
                if tester.stop:
                    break
                self._send(client, tester.message)
            transcript = self._transcript(client)
            projection = _expect(client.get("/api/routedeck/session"), 200).json()["projection"]
            inspection = _expect(client.get("/api/routedeck/inspect"), 200).json()
            deterministic = _deterministic_assertions(
                scenario,
                behavior_nodes,
                projection,
                transcript,
                starting_projection=starting_projection,
                surface_ids=surface_ids,
            )
            judge = self._judge(scenario, transcript, deterministic)
            semantic_pass = (
                all(item.passed for item in judge.required)
                and not any(item.observed for item in judge.forbidden)
                and judge.overall_pass
            )
            passed = all(item["passed"] for item in deterministic) and semantic_pass
            return {
                "evaluationId": scenario["id"],
                "title": scenario["title"],
                "status": "passed" if passed else "failed",
                "definitionSha256": _json_sha256(scenario),
                "conversationId": conversation["id"],
                "transcript": transcript,
                "deterministicAssertions": deterministic,
                "judge": judge.model_dump(mode="json"),
                "evidence": {
                    "projection": projection,
                    "routeTraces": inspection.get("route_traces", []),
                    "invocationTraceHashes": [
                        item.get("model_boundary_request", {}).get("sha256")
                        for item in inspection.get("invocation_traces", {}).get("traces", [])
                    ],
                },
            }
        except Exception as error:
            return {
                "evaluationId": scenario["id"],
                "title": scenario["title"],
                "status": "infrastructure_failure",
                "definitionSha256": _json_sha256(scenario),
                "error": f"{type(error).__name__}: {error}",
            }

    def _send(self, client: httpx.Client, message: str) -> None:
        projection = _expect(client.get("/api/routedeck/session"), 200).json()["projection"]
        request_id = f"eval-{uuid4().hex}"
        started = client.post(
            "/api/routedeck/conversation/runs",
            json={
                "request_id": request_id,
                "expected_session_version": projection["session_version"],
                "trigger": "user_message",
                "message": message,
            },
        )
        _expect(started, 202)
        self._await_run(client, request_id)

    def _dispatch(self, client: httpx.Client, operation_id: str) -> None:
        projection = _expect(
            client.get("/api/routedeck/session"), 200
        ).json()["projection"]
        dispatched = client.post(
            "/api/routedeck/dispatch",
            json={
                "request_id": f"eval-setup-{uuid4().hex}",
                "expected_session_version": projection["session_version"],
                "operation_id": operation_id,
                "arguments": {},
            },
        )
        _expect(dispatched, 200)
        disposition = dispatched.json().get("disposition")
        if disposition != "completed":
            raise RuntimeError(
                f"Setup operation {operation_id} did not complete: {disposition}"
            )

    def _await_run(self, client: httpx.Client, request_id: str) -> dict[str, Any]:
        deadline = time.monotonic() + 180
        while time.monotonic() < deadline:
            run = _expect(client.get(f"/api/routedeck/conversation/runs/{request_id}"), 200).json()["run"]
            if run["stage"] == "completed":
                return run
            if run["stage"] == "interrupted":
                raise RuntimeError(f"Conversation interrupted: {run.get('failure')}")
            time.sleep(0.2)
        raise TimeoutError(f"Conversation run timed out: {request_id}")

    def _transcript(self, client: httpx.Client) -> list[dict[str, str]]:
        turns = _expect(client.get("/api/routedeck/conversation"), 200).json()["turns"]
        return [
            {"role": item["role"], "content": _redact_visible_text(item["content"])}
            for item in turns
            if item["role"] in {"user", "assistant"}
        ]

    def _tester_turn(self, scenario: dict[str, Any], transcript: list[dict[str, str]]) -> TesterTurn:
        prompt = {
            "role": "Act as the user, not the evaluator. Adapt to Corpus's latest response.",
            "scenario": {key: scenario[key] for key in ("hiddenGoal", "persona", "facts", "mayDisclose", "withholdUntilAsked", "bypassAttempts", "stoppingConditions")},
            "rules": ["Do not invent facts.", "Do not coach Corpus.", "Use one concise user message.", "Attempt an applicable bypass before stopping."],
            "transcript": transcript,
        }
        return self._structured_chat(self.tester_model, TesterTurn, prompt)

    def _judge(self, scenario: dict[str, Any], transcript: list[dict[str, str]], deterministic: list[dict[str, Any]]) -> JudgeResult:
        required = [*scenario["perTurnCriteria"], *scenario["finalRequiredCriteria"]]
        forbidden = scenario["finalForbiddenCriteria"]
        prompt = {
            "role": "Judge semantic compliance. Do not require exact wording. Return each supplied criterion exactly once and do not move criteria between lists. For required criteria, passed means satisfied. For forbidden criteria, observed means the forbidden behavior occurred.",
            "requiredCriteria": required,
            "forbiddenCriteria": forbidden,
            "transcript": transcript,
            "deterministicEvidence": deterministic,
            "passRule": "overall_pass is true only when every deterministic assertion and required criterion passes and every forbidden behavior is absent.",
        }
        result = self._structured_chat(self.judge_model, JudgeResult, prompt)
        if [item.criterion for item in result.required] != required:
            raise ValueError("Judge did not return the required criteria exactly")
        if [item.criterion for item in result.forbidden] != forbidden:
            raise ValueError("Judge did not return the forbidden criteria exactly")
        return result

    def _judge_behavior(
        self,
        case: dict[str, Any],
        transcript: list[dict[str, str]],
        deterministic: list[dict[str, Any]],
    ) -> JudgeResult:
        required = case["requiredCriteria"]
        forbidden = case["forbiddenCriteria"]
        prompt = {
            "role": "Judge semantic compliance. Do not require exact wording. Return each supplied criterion exactly once and do not move criteria between lists. For required criteria, passed means satisfied. For forbidden criteria, observed means the forbidden behavior occurred.",
            "referenceResponse": case.get("referenceResponse") or None,
            "referenceRule": "The reference response provides semantic direction only and must never be matched exactly.",
            "requiredCriteria": required,
            "forbiddenCriteria": forbidden,
            "transcript": transcript,
            "deterministicEvidence": deterministic,
            "passRule": "overall_pass is true only when every deterministic assertion and required criterion passes and every forbidden behavior is absent.",
        }
        result = self._structured_chat(self.judge_model, JudgeResult, prompt)
        if [item.criterion for item in result.required] != required:
            raise ValueError("Judge did not return the required criteria exactly")
        if [item.criterion for item in result.forbidden] != forbidden:
            raise ValueError("Judge did not return the forbidden criteria exactly")
        return result

    def _structured_chat(self, model: str, contract: type[_StrictModel], payload: dict[str, Any]):
        content = json.dumps(payload, separators=(",", ":"))
        if self.model_provider == "ollama":
            assert self.ollama is not None
            response = self.ollama.chat(
                model=model,
                messages=[{"role": "user", "content": content}],
                format=contract.model_json_schema(),
                options={"temperature": 0},
            )
            return contract.model_validate_json(response.message.content)

        assert self.openai_api_key is not None
        structured = ChatOpenAI(
            model=model,
            api_key=self.openai_api_key,
            use_responses_api=True,
            reasoning_effort=self.openai_reasoning_effort,
        ).with_structured_output(contract, method="json_schema")
        response = structured.invoke(content)
        return contract.model_validate(response)

    def _update_latest(self, artifact: dict[str, Any], artifact_path: Path) -> None:
        latest_path = self.results_root / "latest.json"
        latest = _load_json(latest_path) if latest_path.exists() else {"schema": "corpus.self-evaluation.latest.v1", "evaluations": {}}
        for result in artifact["results"]:
            latest["evaluations"][result["evaluationId"]] = {
                "status": result["status"],
                "runId": artifact["runId"],
                "completedAt": artifact["completedAt"],
                "designSha256": artifact["identities"]["designSha256"],
                "artifact": str(artifact_path.relative_to(self.repository)).replace("\\", "/"),
            }
        temporary = latest_path.with_suffix(".tmp")
        temporary.parent.mkdir(parents=True, exist_ok=True)
        temporary.write_text(json.dumps(latest, indent=2) + "\n", encoding="utf-8")
        temporary.replace(latest_path)


def _deterministic_assertions(
    scenario,
    behavior_nodes,
    projection,
    transcript,
    *,
    starting_projection=None,
    surface_ids=None,
):
    expectations = scenario["expectations"]
    text = "\n".join(item["content"] for item in transcript if item["role"] == "assistant")
    current_node = projection["current"]["node_id"]
    action_labels = {item["label"] for item in projection.get("suggested_actions", [])}
    accepted_final_behaviors = [
        expectations["finalBehavior"],
        *expectations.get("allowedFinalBehaviors", []),
    ]
    accepted_final_nodes = {behavior_nodes[name] for name in accepted_final_behaviors}
    observed_surface_ids = _projection_surface_ids(projection)
    required_surface_ids = {
        (surface_ids or {})[name]
        for name in expectations.get("requiredSurfaces", [])
    }
    protocol_markup = re.search(r"\bto=rd_[a-z0-9_]+|\bcode:\s*\{", text, re.IGNORECASE)
    checks = [
        _check(
            "starting behavior",
            starting_projection is None
            or starting_projection["current"]["node_id"]
            == behavior_nodes[expectations["startingBehavior"]],
            "not captured"
            if starting_projection is None
            else f"expected {behavior_nodes[expectations['startingBehavior']]}, observed {starting_projection['current']['node_id']}",
        ),
        _check("final behavior", current_node in accepted_final_nodes, f"expected one of {sorted(accepted_final_nodes)}, observed {current_node}"),
        _check(
            "required surfaces",
            required_surface_ids <= observed_surface_ids,
            f"required {sorted(required_surface_ids)}, observed {sorted(observed_surface_ids)}",
        ),
        _check("required suggested actions", set(expectations["requiredSuggestedActions"]) <= action_labels, f"required {expectations['requiredSuggestedActions']}, observed {sorted(action_labels)}"),
        _check("public authentication", expectations["authentication"] != "public" or current_node.startswith("lounge."), f"observed {current_node}"),
        _check("framework internals absent", not any(token in text.lower() for token in ("routedeck", "agentpolicy", "operation_id", "session_version")), "scanned visible assistant text"),
        _check(
            "model protocol markup absent",
            protocol_markup is None,
            "scanned visible assistant text",
        ),
    ]
    return checks


def _projection_surface_ids(projection: dict[str, Any]) -> set[str]:
    observed: set[str] = set()
    for value in projection.get("surfaces", {}).values():
        items = value if isinstance(value, list) else [value]
        for item in items:
            if isinstance(item, dict) and isinstance(item.get("surface_id"), str):
                observed.add(item["surface_id"])
    return observed


_PUBLIC_BEHAVIOR_SETUP: dict[str, tuple[tuple[str, str], ...] | None] = {
    "Arrive in the Lounge": (),
    "Ask Lounge for product help": (
        ("Arrive in the Lounge", "Start product help"),
    ),
    "Create an owner account": (
        ("Arrive in the Lounge", "Open owner registration"),
    ),
    "Sign in": (
        ("Arrive in the Lounge", "Open owner sign-in"),
    ),
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


def _check(name: str, passed: bool, evidence: str) -> dict[str, Any]:
    return {"name": name, "passed": passed, "evidence": evidence}


def _redact_visible_text(value: str) -> str:
    redacted = re.sub(
        r"(?i)(\bpassword\s*(?:is|:|=)\s*)\S+",
        r"\1[redacted-password]",
        value,
    )
    redacted = re.sub(
        r"(?i)(\bpassword\s+)(?=\S*(?:\d|[!@#$%^&*]))\S+",
        r"\1[redacted-password]",
        redacted,
    )
    return re.sub(
        r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
        "[redacted-email]",
        redacted,
        flags=re.IGNORECASE,
    )


def _expect(response: httpx.Response, status: int) -> httpx.Response:
    if response.status_code != status:
        raise RuntimeError(f"{response.request.method} {response.request.url} returned {response.status_code}: {response.text[:500]}")
    return response


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json_sha256(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _git(repository: Path, *arguments: str) -> str:
    return subprocess.run(["git", *arguments], cwd=repository, check=True, capture_output=True, text=True).stdout.strip()


def _git_diff_sha256(repository: Path) -> str:
    diff = subprocess.run(["git", "diff", "--binary", "HEAD"], cwd=repository, check=True, capture_output=True).stdout
    return hashlib.sha256(diff).hexdigest()
