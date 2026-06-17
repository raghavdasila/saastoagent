# Medusa Manual E2E Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the manually tested Medusa public-agent flow pass as a user would experience it: persistent visitor checkout state, evidence-first owner approvals, dynamic endpoint selection for shipping/checkout continuations, clean policy candidates, and screenshot-backed browser proof.

**Architecture:** Preserve the ADR boundary: RouteDeck exposes state and legal capabilities, Corpus decides product intent from normal chat, and AppGraph validates/commits. Do not add Medusa-specific endpoint maps, phrase routers, alias tables, or deterministic public-chat navigation shortcuts. Fix the generic session, policy, ranking, and result-formatting primitives that failed during the Medusa acceptance fixture.

**Tech Stack:** FastAPI, SQLAlchemy async sessions, PostgreSQL/pgvector container, React/Vite, TanStack Query, RouteDeck React store, Playwright only for owner-side helper browser or screenshot capture when the in-app browser cannot keep two sessions mounted.

---

## Acceptance Criteria

- Public deployed chat at `/a/{slug}` survives a browser refresh or owner-workbench navigation by restoring the latest visitor session id and transcript from backend state.
- The visitor can complete this sequence without internal ids or endpoint names appearing in the transcript:
  - `what products do we have`
  - `i want to buy medusa tshirt`
  - `add the L size to cart`
  - owner approves the policy candidate
  - repeat add-to-cart
  - `checkout`
  - choose Express Shipping
  - owner approves required checkout policies
  - complete checkout
- Owner Sandbox Learning list does not show a dead quick-approve control. Proposed policy candidates must be opened into the review surface before approval or rejection.
- Natural shipping phrasing such as `use Express Shipping` selects the generated shipping-method action when that action is dynamically present and the selected option can satisfy its required input.
- The router fix is dynamic: it works from generated `ActionNode` and `GeneratedTool` metadata, frame variables, pending choices, path structure, method, request schema, and token overlap. It must not contain Medusa-only paths, operation ids, product names, or fixture-specific literals.
- Policy learning does not create duplicate proposed candidates with blank or missing `allowed_action_paths`.
- Public read responses summarize useful product/choice information and keep raw payloads collapsed behind technical details.
- Verification includes backend tests, frontend type-check, and one manual browser E2E run with screenshot proof.

---

## File Structure

- Modify `backend/routes/deployed_agents.py`
  - Add a public-session transcript endpoint for deployed chat restoration.
  - Reuse existing profile/deployment/session ownership checks.
- Modify `frontend/src/pages/DeployedAgentChatPage.tsx`
  - Persist the public visitor session id per slug.
  - Hydrate the transcript on page load.
  - Clear persisted session state when the user resets chat.
- Modify `frontend/src/hooks/useSSEChat.ts`
  - Accept optional initial session state or expose stable setters already returned by the hook.
  - Call a session-change callback when `stream_start` yields a session id.
- Modify `frontend/src/components/agent/LearningPanel.tsx`
  - Remove list-level approve/reject buttons for proposed candidates.
  - Keep approve/reject only on detail review surfaces.
- Modify `backend/services/agent/rest_operator.py`
  - Strengthen frame-aware reranking for pending choices and child workflow actions.
  - Add a generic public read-result formatter.
  - Keep policy/missing-input gates outside the ranker.
- Modify `backend/services/agent/state_variables.py`
  - Add tests or helpers only if pending choice matching needs alias normalization.
- Modify `backend/services/agent/learning_service.py`
  - Normalize/dedupe policy-gap candidates and reject empty policy evidence before insert.
- Modify `backend/services/agent/api_orchestration.py`
  - Add pure helper validation for policy gap payload paths if useful.
- Modify tests:
  - `backend/tests/test_deployed_agents.py` or a new `backend/tests/test_deployed_public_sessions.py`
  - `backend/tests/test_app_graph_contract.py`
  - `backend/tests/test_execution_frames.py`
  - `backend/tests/test_rest_catalog.py`
  - `backend/tests/test_api_orchestration.py`
  - `backend/tests/test_toolrouter_fusion_ranker.py`
- Modify docs:
  - `docs/medusa-api-agent-test-guide.md`

---

## Task 1: Public Deployed Chat Session Restoration

**Files:**
- Modify: `backend/routes/deployed_agents.py`
- Modify: `frontend/src/pages/DeployedAgentChatPage.tsx`
- Modify: `frontend/src/hooks/useSSEChat.ts`
- Test: `backend/tests/test_deployed_public_sessions.py`
- Test: `backend/tests/test_app_graph_contract.py`

- [ ] **Step 1: Add failing backend route test for transcript restore**

Create `backend/tests/test_deployed_public_sessions.py` with a focused source-contract test if route integration fixtures are too heavy:

```python
from pathlib import Path


def test_deployed_agents_exposes_session_messages_restore_endpoint():
    source = (Path(__file__).parents[1] / "routes" / "deployed_agents.py").read_text(encoding="utf-8")

    assert '@router.get("/{slug}/sessions/{session_id}/messages"' in source
    assert "AgentMessageRead" in source
    assert "session.user_id != (user.id if user else None)" in source
    assert "AgentMessage.session_id == session_id" in source
    assert ".order_by(AgentMessage.created_at.asc())" in source
```

- [ ] **Step 2: Run the failing backend route test**

Run:

```powershell
cd "D:\Dev\AI Projects\agent-core\agent-lab-powered-projects\saastoagent-v0.1"
python -m pytest backend/tests/test_deployed_public_sessions.py -q
```

Expected: FAIL because the deployed public messages endpoint does not exist yet.

- [ ] **Step 3: Implement deployed public transcript endpoint**

In `backend/routes/deployed_agents.py`, add `AgentMessage` and `AgentMessageRead` imports:

```python
from sqlalchemy import select

from backend.core.models import AgentMessage, AgentSession, User
from backend.core.schemas import AgentMessageRead, ChatRequest, DeployedAgentProfile
```

Add this route below `deployed_agent_chat` and above the SSE events route:

```python
@router.get("/{slug}/sessions/{session_id}/messages", response_model=list[AgentMessageRead])
async def deployed_agent_session_messages(
    slug: str,
    session_id: uuid.UUID,
    user: User | None = Depends(current_optional_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    resolved = await deployment_profile_for_slug(slug=slug, db=db)
    if resolved is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deployed agent not found")
    _, deployment, profile = resolved
    if not deployment.enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deployed agent is not enabled")
    if profile.auth_required and user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sign in to chat with this agent")

    session = await db.get(AgentSession, session_id)
    if session is None or session.saas_agent_id != profile.saas_agent_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deployed chat session not found")
    if session.user_id != (user.id if user else None):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Session does not belong to this visitor")

    result = await db.execute(
        select(AgentMessage)
        .where(AgentMessage.session_id == session_id)
        .order_by(AgentMessage.created_at.asc())
    )
    return [AgentMessageRead.model_validate(message) for message in result.scalars().all()]
```

- [ ] **Step 4: Run the backend route test**

Run:

```powershell
python -m pytest backend/tests/test_deployed_public_sessions.py -q
```

Expected: PASS.

- [ ] **Step 5: Add failing frontend contract test for persisted public session**

Add to `backend/tests/test_app_graph_contract.py`:

```python
def test_public_deployed_chat_persists_and_restores_visitor_session():
    page_source = (
        Path(__file__).parents[2]
        / "frontend"
        / "src"
        / "pages"
        / "DeployedAgentChatPage.tsx"
    ).read_text(encoding="utf-8")
    hook_source = (
        Path(__file__).parents[2]
        / "frontend"
        / "src"
        / "hooks"
        / "useSSEChat.ts"
    ).read_text(encoding="utf-8")

    assert "public-agent-session:" in page_source
    assert "localStorage.getItem(publicSessionStorageKey)" in page_source
    assert "localStorage.setItem(publicSessionStorageKey, nextSessionId)" in page_source
    assert "localStorage.removeItem(publicSessionStorageKey)" in page_source
    assert "`/deployed-agents/${slug}/sessions/${storedSessionId}/messages`" in page_source
    assert "onSessionIdChange" in hook_source
```

- [ ] **Step 6: Run the failing frontend contract test**

Run:

```powershell
python -m pytest backend/tests/test_app_graph_contract.py::test_public_deployed_chat_persists_and_restores_visitor_session -q
```

Expected: FAIL until the page and hook persist/restore the public session.

- [ ] **Step 7: Add hook callback for session id changes**

In `frontend/src/hooks/useSSEChat.ts`, extend the options interface:

```ts
interface UseSSEChatOptions {
  saasAgentId: string | null
  chatPath?: string | null
  onError?: (message: string) => void
  onSessionIdChange?: (sessionId: string | null) => void
}
```

Change the function signature:

```ts
export function useSSEChat({
  saasAgentId,
  chatPath,
  onError,
  onSessionIdChange,
}: UseSSEChatOptions): UseSSEChatReturn {
```

In the reset effect, notify the caller:

```ts
setSessionId(null)
onSessionIdChange?.(null)
```

In `stream_start`, notify when the server assigns a session:

```ts
case 'stream_start': {
  const sid = data.session_id as string
  if (sid) {
    setSessionId(sid)
    onSessionIdChange?.(sid)
  }
  break
}
```

In `clearMessages`, notify:

```ts
setSessionId(null)
onSessionIdChange?.(null)
```

Update dependency arrays that use `onSessionIdChange`.

- [ ] **Step 8: Restore public session and transcript in deployed page**

In `frontend/src/pages/DeployedAgentChatPage.tsx`, destructure `setSessionId` from the hook:

```ts
const {
  messages,
  isStreaming,
  sessionId,
  sendMessage,
  clearMessages,
  setMessages,
  setSessionId,
} = useSSEChat({
  saasAgentId: profile?.saas_agent_id ?? null,
  chatPath,
  onError: setError,
  onSessionIdChange: (nextSessionId) => {
    if (!publicSessionStorageKey) return
    if (nextSessionId) {
      localStorage.setItem(publicSessionStorageKey, nextSessionId)
    } else {
      localStorage.removeItem(publicSessionStorageKey)
    }
  },
})
```

Add key and stored id state near the top:

```ts
const publicSessionStorageKey = slug ? `public-agent-session:${slug}` : null
const [storedSessionId, setStoredSessionId] = useState<string | null>(() => {
  if (!slug) return null
  return localStorage.getItem(`public-agent-session:${slug}`)
})
```

Reset stored id when slug changes:

```ts
useEffect(() => {
  if (!publicSessionStorageKey) {
    setStoredSessionId(null)
    return
  }
  setStoredSessionId(localStorage.getItem(publicSessionStorageKey))
}, [publicSessionStorageKey])
```

Add transcript query:

```ts
const restoredMessagesQuery = useQuery({
  queryKey: ['deployed-agent-session-messages', slug, storedSessionId],
  queryFn: () =>
    api.get<ChatUIMessage[]>(`/deployed-agents/${slug}/sessions/${storedSessionId}/messages`),
  enabled: Boolean(slug && storedSessionId && profile && !sessionId && !authBlocked),
  retry: false,
})
```

Map backend message fields into `ChatUIMessage` and hydrate once:

```ts
useEffect(() => {
  if (!storedSessionId || !restoredMessagesQuery.data || sessionId) return
  setSessionId(storedSessionId)
  setMessages(
    restoredMessagesQuery.data.map((message) => ({
      id: String(message.id),
      role: message.role === 'user' ? 'user' : 'assistant',
      content: message.content,
      timestamp: new Date(String(message.created_at)).getTime(),
      source: 'agent',
    })),
  )
}, [restoredMessagesQuery.data, sessionId, setMessages, setSessionId, storedSessionId])
```

Wrap reset:

```ts
const resetPublicChat = () => {
  clearMessages()
  if (publicSessionStorageKey) {
    localStorage.removeItem(publicSessionStorageKey)
  }
  setStoredSessionId(null)
}
```

Use `resetPublicChat` on the reset button.

- [ ] **Step 9: Run frontend type-check and focused tests**

Run:

```powershell
cd "D:\Dev\AI Projects\agent-core\agent-lab-powered-projects\saastoagent-v0.1\frontend"
npm run type-check

cd "D:\Dev\AI Projects\agent-core\agent-lab-powered-projects\saastoagent-v0.1"
python -m pytest backend/tests/test_deployed_public_sessions.py backend/tests/test_app_graph_contract.py::test_public_deployed_chat_persists_and_restores_visitor_session -q
```

Expected: both pass.

- [ ] **Step 10: Commit Task 1**

```powershell
git add backend/routes/deployed_agents.py frontend/src/hooks/useSSEChat.ts frontend/src/pages/DeployedAgentChatPage.tsx backend/tests/test_deployed_public_sessions.py backend/tests/test_app_graph_contract.py
git commit -m "fix: restore deployed chat visitor sessions"
```

---

## Task 2: Evidence-First Learning Approval UI

**Files:**
- Modify: `frontend/src/components/agent/LearningPanel.tsx`
- Modify: `backend/tests/test_app_graph_contract.py`

- [ ] **Step 1: Add failing contract test that list view cannot quick-approve**

Add to `backend/tests/test_app_graph_contract.py`:

```python
def test_learning_list_requires_opening_review_before_approve_or_reject():
    source = (
        Path(__file__).parents[2]
        / "frontend"
        / "src"
        / "components"
        / "agent"
        / "LearningPanel.tsx"
    ).read_text(encoding="utf-8")

    assert "candidateId && candidate.status === 'proposed'" in source
    assert "title=\"Open review\"" in source
    assert "title=\"Approve learning\"" in source
    assert "title=\"Reject learning\"" in source
```

- [ ] **Step 2: Run failing test**

```powershell
python -m pytest backend/tests/test_app_graph_contract.py::test_learning_list_requires_opening_review_before_approve_or_reject -q
```

Expected: FAIL because list-level approval is currently rendered for proposed candidates.

- [ ] **Step 3: Gate approve/reject controls to detail review**

In `frontend/src/components/agent/LearningPanel.tsx`, change:

```tsx
{candidate.status === 'proposed' && !readonly && (
```

to:

```tsx
{candidateId && candidate.status === 'proposed' && !readonly && (
```

Keep the `Open review` button visible in list mode.

- [ ] **Step 4: Run test and type-check**

```powershell
python -m pytest backend/tests/test_app_graph_contract.py::test_learning_list_requires_opening_review_before_approve_or_reject -q
cd "D:\Dev\AI Projects\agent-core\agent-lab-powered-projects\saastoagent-v0.1\frontend"
npm run type-check
```

Expected: PASS.

- [ ] **Step 5: Commit Task 2**

```powershell
git add frontend/src/components/agent/LearningPanel.tsx backend/tests/test_app_graph_contract.py
git commit -m "fix: require learning review before approval"
```

---

## Task 3: Dynamic Pending-Choice And Child Workflow Routing

**Files:**
- Modify: `backend/services/agent/rest_operator.py`
- Modify: `backend/services/agent/state_variables.py` only if alias normalization needs a helper
- Test: `backend/tests/test_rest_catalog.py`
- Test: `backend/tests/test_execution_frames.py`
- Test: `backend/tests/test_toolrouter_fusion_ranker.py`

- [ ] **Step 1: Add failing test for pending choice forcing target action**

Add to `backend/tests/test_execution_frames.py`:

```python
from backend.services.agent.state_variables import remember_choice_variable, pending_choice_target_path_for_message


def test_pending_choice_target_path_matches_natural_option_reply():
    frame = remember_choice_variable(
        {"kind": "result_context"},
        input_name="option_id",
        target_action_path="/store/carts/{id}/shipping-methods",
        items=[{"id": "so_express", "name": "Express Shipping"}],
        origin={"path": "/store/shipping-options"},
    )

    assert pending_choice_target_path_for_message(frame, "use Express Shipping") == "/store/carts/{id}/shipping-methods"
```

- [ ] **Step 2: Run pending-choice test**

```powershell
python -m pytest backend/tests/test_execution_frames.py::test_pending_choice_target_path_matches_natural_option_reply -q
```

Expected: PASS if existing choice matching is sufficient; FAIL if aliases miss Medusa-style option names. If it fails, implement Step 3.

- [ ] **Step 3: Normalize pending-choice aliases if needed**

In `backend/services/agent/state_variables.py`, update `_choice_item` to include common display fields without fixture-specific terms:

```python
def _choice_item(item: dict[str, Any]) -> dict[str, Any] | None:
    value = item.get("id")
    if not value:
        return None
    label = _first_string(
        item,
        ["title", "name", "label", "display_name", "handle", "code", "shipping_option_name"],
    ) or str(value)
    aliases = {_choice_match_text(label)}
    for key in ("title", "name", "label", "display_name", "handle", "code", "shipping_option_name"):
        raw = item.get(key)
        if isinstance(raw, str) and raw.strip():
            aliases.add(_choice_match_text(raw))
    return {"label": label, "value": str(value), "aliases": sorted(alias for alias in aliases if alias)}
```

If the Step 2 test already passes, skip this code change.

- [ ] **Step 4: Add failing rerank test for child workflow endpoint**

Add to `backend/tests/test_rest_catalog.py`:

```python
def test_frame_rerank_prefers_specific_child_workflow_action_over_parent_update():
    frame = {
        "kind": "result_context",
        "active_resource": {
            "collection_path": "/store/carts",
            "id": "cart_1",
            "source_action_path": "/store/carts/{id}/line-items",
            "reason": "internal_dependency_used_successfully",
        },
        "variables": {
            "resource./store/carts.id": {
                "name": "resource./store/carts.id",
                "value": "cart_1",
                "visibility": "private",
                "value_type": "string",
                "tags": ["resource_id"],
                "aliases": ["id", "cart_id"],
                "resource": {"collection_path": "/store/carts", "resource_id": "cart_1"},
                "origin": {},
            },
            "choice.option_id": {
                "name": "choice.option_id",
                "value": None,
                "visibility": "private",
                "value_type": "choice",
                "tags": ["pending_choice", "internal_input"],
                "aliases": ["option_id"],
                "resource": None,
                "origin": {},
                "choice": {
                    "target_action_path": "/store/carts/{id}/shipping-methods",
                    "input_name": "option_id",
                    "items": [{"label": "Express Shipping", "value": "so_1", "aliases": ["express shipping"]}],
                },
            },
        },
    }
    parent_update = SimpleNamespace(
        score=30,
        tool=SimpleNamespace(
            name="postcartsid",
            description="Update a cart.",
            function_schema={
                "parameters": {
                    "type": "object",
                    "properties": {"id": {"type": "string"}},
                    "required": ["id"],
                }
            },
        ),
        action=SimpleNamespace(method="POST", path="/store/carts/{id}", name="updateCart", description="Update a cart.", parameters=[]),
    )
    shipping_method = SimpleNamespace(
        score=20,
        tool=SimpleNamespace(
            name="postcartsidshippingmethods",
            description="Add a shipping method to a cart.",
            function_schema={
                "parameters": {
                    "type": "object",
                    "properties": {"id": {"type": "string"}, "option_id": {"type": "string"}},
                    "required": ["id", "option_id"],
                }
            },
        ),
        action=SimpleNamespace(
            method="POST",
            path="/store/carts/{id}/shipping-methods",
            name="addShippingMethod",
            description="Add a shipping method to a cart.",
            parameters=[],
        ),
    )

    ranked = _rerank_candidates_for_frame(
        message="use Express Shipping",
        candidates=[parent_update, shipping_method],
        frame=frame,
    )

    assert ranked[0].action.path == "/store/carts/{id}/shipping-methods"
```

- [ ] **Step 5: Run failing rerank test**

```powershell
python -m pytest backend/tests/test_rest_catalog.py::test_frame_rerank_prefers_specific_child_workflow_action_over_parent_update -q
```

Expected: FAIL if the parent update currently outranks the child endpoint.

- [ ] **Step 6: Implement generic child workflow and pending-choice scoring**

In `backend/services/agent/rest_operator.py`, add helpers near `_workflow_action_bonus`:

```python
def _pending_choice_target_bonus(message: str, candidate: ToolCandidate, frame: dict[str, Any]) -> int:
    target_path = pending_choice_target_path_for_message(frame, message)
    if not target_path:
        return 0
    candidate_path = str(getattr(candidate.action, "path", "") or "")
    return 80 if candidate_path == target_path else -20


def _child_resource_specificity_bonus(message: str, candidate: ToolCandidate, active_path: str) -> int:
    candidate_path = str(getattr(candidate.action, "path", "") or "").rstrip("/")
    if not active_path or not candidate_path.startswith(active_path.rstrip("/") + "/"):
        return 0
    trailing = candidate_path[len(active_path.rstrip("/")) :].strip("/")
    trailing_tokens = set(_tokens(trailing))
    message_tokens = set(_tokens(message))
    if not trailing_tokens:
        return 0
    overlap = trailing_tokens & message_tokens
    return 30 + (10 * len(overlap)) if overlap else 12


def _generic_parent_update_penalty(message: str, candidate: ToolCandidate, active_path: str) -> int:
    candidate_path = str(getattr(candidate.action, "path", "") or "").rstrip("/")
    method = str(getattr(candidate.action, "method", "") or "").upper()
    if method not in {"POST", "PUT", "PATCH"}:
        return 0
    if not active_path or candidate_path != f"{active_path.rstrip('/')}/{{id}}":
        return 0
    if _looks_like_workflow_message(message):
        return -28
    return 0
```

Then update `_context_candidate_score` inside the `active_resource is not None` block:

```python
if active_resource is not None:
    active_path = str(active_resource.get("collection_path") or "").rstrip("/")
    candidate_path = str(getattr(candidate.action, "path", "") or "")
    method = str(getattr(candidate.action, "method", "") or "").upper()
    if active_path and (candidate_path == active_path or candidate_path.startswith(active_path + "/")):
        score += 10
    score += _pending_choice_target_bonus(message, candidate, frame)
    score += _child_resource_specificity_bonus(message, candidate, active_path)
    score += _generic_parent_update_penalty(message, candidate, active_path)
    score += _workflow_action_bonus(message, candidate)
    if _looks_like_workflow_message(message) and method in {"GET", "HEAD", "OPTIONS"}:
        score -= 40
    if _looks_like_workflow_message(message) and _candidate_missing_after_frame(message, candidate, frame):
        score -= 12
```

This uses dynamic path structure and pending-choice metadata. It does not mention Medusa, carts, shipping, or operation names.

- [ ] **Step 7: Run routing tests**

```powershell
python -m pytest backend/tests/test_execution_frames.py::test_pending_choice_target_path_matches_natural_option_reply backend/tests/test_rest_catalog.py::test_frame_rerank_prefers_specific_child_workflow_action_over_parent_update backend/tests/test_rest_catalog.py::test_frame_rerank_prefers_action_with_entity_fillable_required_inputs -q
```

Expected: PASS.

- [ ] **Step 8: Add fusion-ranker regression for shipping phrase**

Add to `backend/tests/test_toolrouter_fusion_ranker.py`:

```python
def test_rank_endpoint_scores_prefers_shipping_method_child_endpoint_for_shipping_phrase():
    update_cart = _action(
        method="POST",
        path="/store/carts/{id}",
        name="updateCart",
        description="Update cart fields.",
        tags=["Carts"],
        parameters=[{"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}],
    )
    add_shipping = _action(
        method="POST",
        path="/store/carts/{id}/shipping-methods",
        name="addShippingMethod",
        description="Add a shipping method to a cart.",
        tags=["Carts"],
        parameters=[{"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}],
        request_body={
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "required": ["option_id"],
                        "properties": {"option_id": {"type": "string", "description": "Shipping option id"}},
                    }
                }
            }
        },
    )
    docs = build_router_documents(
        [
            (_tool(update_cart, name="postcartsid"), update_cart),
            (_tool(add_shipping, name="postcartsidshippingmethods"), add_shipping),
        ]
    )

    ranked = rank_endpoint_scores("use Express Shipping", docs, min_score=0)

    assert ranked[0].endpoint_key == str(add_shipping.id)
```

- [ ] **Step 9: Run fusion-ranker regression**

```powershell
python -m pytest backend/tests/test_toolrouter_fusion_ranker.py::test_rank_endpoint_scores_prefers_shipping_method_child_endpoint_for_shipping_phrase -q
```

Expected: PASS if document ranking already captures this; if not, adjust fusion weights by increasing `schema_param` and `graph_sparse` modestly while keeping `MIN_ENDPOINT_SCORE` unchanged.

- [ ] **Step 10: Commit Task 3**

```powershell
git add backend/services/agent/rest_operator.py backend/services/agent/state_variables.py backend/tests/test_execution_frames.py backend/tests/test_rest_catalog.py backend/tests/test_toolrouter_fusion_ranker.py
git commit -m "fix: prefer dynamic child workflow actions"
```

---

## Task 4: Policy Candidate Deduplication And Evidence Validation

**Files:**
- Modify: `backend/services/agent/learning_service.py`
- Modify: `backend/services/agent/api_orchestration.py`
- Test: `backend/tests/test_api_orchestration.py`

- [ ] **Step 1: Add pure tests for policy path normalization**

Add to `backend/tests/test_api_orchestration.py`:

```python
from backend.services.agent.learning_service import _candidate_matches_policy_gap, _normalized_policy_paths


def test_normalized_policy_paths_drop_empty_values_and_dedupe_order():
    assert _normalized_policy_paths(["", "/store/carts", "/store/carts", None]) == ["/store/carts"]


def test_candidate_matches_policy_gap_rejects_blank_existing_evidence():
    candidate = SimpleNamespace(
        trigger_type="domain_policy_gap",
        status="proposed",
        evidence={"allowed_action_paths": []},
    )

    assert _candidate_matches_policy_gap(candidate, ["/store/carts/{id}/complete"]) is False


def test_candidate_matches_policy_gap_reuses_same_single_action_candidate():
    candidate = SimpleNamespace(
        trigger_type="domain_policy_gap",
        status="approved",
        evidence={"allowed_action_paths": ["/store/carts/{id}/complete"]},
    )

    assert _candidate_matches_policy_gap(candidate, ["/store/carts/{id}/complete"]) is True
```

- [ ] **Step 2: Run failing policy tests**

```powershell
python -m pytest backend/tests/test_api_orchestration.py::test_normalized_policy_paths_drop_empty_values_and_dedupe_order backend/tests/test_api_orchestration.py::test_candidate_matches_policy_gap_rejects_blank_existing_evidence backend/tests/test_api_orchestration.py::test_candidate_matches_policy_gap_reuses_same_single_action_candidate -q
```

Expected: FAIL because `_normalized_policy_paths` does not exist.

- [ ] **Step 3: Implement normalizer and evidence guard**

In `backend/services/agent/learning_service.py`, add:

```python
def _normalized_policy_paths(action_paths: list[Any]) -> list[str]:
    normalized: list[str] = []
    for raw_path in action_paths:
        path = str(raw_path or "").strip()
        if not path:
            continue
        if path not in normalized:
            normalized.append(path)
    return normalized
```

In `propose_domain_policy_gap`, change:

```python
action_paths = payload["evidence"]["allowed_action_paths"]
```

to:

```python
action_paths = _normalized_policy_paths(payload.get("evidence", {}).get("allowed_action_paths", []))
if not action_paths:
    return await self._existing_candidate_for_trace_or_raise(trace=trace, db=db)
payload["evidence"]["allowed_action_paths"] = action_paths
```

If adding a private method feels too broad, use this safer local fallback instead of inserting a blank candidate:

```python
if not action_paths:
    existing = (
        await db.execute(
            select(AgentLearningCandidate).where(
                AgentLearningCandidate.saas_agent_id == trace.saas_agent_id,
                AgentLearningCandidate.source_trace_id == trace.id,
                AgentLearningCandidate.trigger_type == "domain_policy_gap",
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        return existing
    raise ValueError("Cannot propose domain policy gap without allowed action paths.")
```

Update `_candidate_matches_policy_gap`:

```python
def _candidate_matches_policy_gap(candidate: AgentLearningCandidate, action_paths: list[str]) -> bool:
    evidence = candidate.evidence or {}
    allowed = evidence.get("allowed_action_paths") if isinstance(evidence, dict) else None
    normalized_allowed = _normalized_policy_paths(allowed or [])
    normalized_requested = _normalized_policy_paths(action_paths)
    if not normalized_allowed or not normalized_requested:
        return False
    return set(normalized_allowed) == set(normalized_requested)
```

- [ ] **Step 4: Run policy tests**

```powershell
python -m pytest backend/tests/test_api_orchestration.py::test_normalized_policy_paths_drop_empty_values_and_dedupe_order backend/tests/test_api_orchestration.py::test_candidate_matches_policy_gap_rejects_blank_existing_evidence backend/tests/test_api_orchestration.py::test_candidate_matches_policy_gap_reuses_same_single_action_candidate -q
```

Expected: PASS.

- [ ] **Step 5: Run policy-adjacent suite**

```powershell
python -m pytest backend/tests/test_api_orchestration.py backend/tests/test_execution_frames.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit Task 4**

```powershell
git add backend/services/agent/learning_service.py backend/tests/test_api_orchestration.py
git commit -m "fix: dedupe policy learning candidates"
```

---

## Task 5: Public Read Result Summaries Without Internal Leakage

**Files:**
- Modify: `backend/services/agent/rest_operator.py`
- Test: `backend/tests/test_rest_catalog.py`

- [ ] **Step 1: Add failing test for product detail summary**

Add to `backend/tests/test_rest_catalog.py`:

```python
from backend.services.agent.rest_operator import _format_public_read_result


def test_public_read_result_summarizes_named_item_and_options_without_ids():
    result = {
        "status_code": 200,
        "duration_ms": 1,
        "error": None,
        "body": {
            "product": {
                "id": "prod_1",
                "title": "Medusa T-Shirt",
                "variants": [
                    {"id": "var_s", "title": "Small", "options": {"Size": "S"}},
                    {"id": "var_l", "title": "Large", "options": {"Size": "L"}},
                ],
            }
        },
    }

    content = _format_public_read_result(result)

    assert "Medusa T-Shirt" in content
    assert "S" in content
    assert "L" in content
    assert "prod_1" not in content
    assert "var_l" not in content
    assert "```json" in content
```

- [ ] **Step 2: Run failing summary test**

```powershell
python -m pytest backend/tests/test_rest_catalog.py::test_public_read_result_summarizes_named_item_and_options_without_ids -q
```

Expected: FAIL because `_format_public_read_result` does not exist.

- [ ] **Step 3: Implement bounded generic summary formatter**

In `backend/services/agent/rest_operator.py`, add near `_preview_body_json`:

```python
def _format_public_read_result(result: dict[str, Any]) -> str:
    summary_lines = _public_result_summary_lines(result.get("body"))
    summary = "\n".join(f"- {line}" for line in summary_lines[:6])
    if not summary:
        summary = "I found matching information from the connected API."
    return (
        f"{summary}\n\n"
        f"```json\n{_preview_body_json(result.get('body'))}\n```\n\n"
        "You can ask me to check another item or narrow the result."
    )


def _public_result_summary_lines(body: Any) -> list[str]:
    items = _public_summary_items(body)
    lines: list[str] = []
    for item in items[:6]:
        label = _public_label(item)
        if not label:
            continue
        option_text = _public_option_text(item)
        lines.append(f"{label}{f' ({option_text})' if option_text else ''}")
    return lines


def _public_summary_items(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, dict):
        for item in value.values():
            if isinstance(item, list):
                rows = [row for row in item if isinstance(row, dict)]
                if rows:
                    return rows
            if isinstance(item, dict) and _public_label(item):
                return [item]
        return [value] if _public_label(value) else []
    if isinstance(value, list):
        return [row for row in value if isinstance(row, dict)]
    return []


def _public_label(item: dict[str, Any]) -> str:
    for key in ("title", "name", "label", "display_name", "handle"):
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _public_option_text(item: dict[str, Any]) -> str:
    variants = item.get("variants")
    if not isinstance(variants, list):
        return ""
    labels: list[str] = []
    for variant in variants[:8]:
        if not isinstance(variant, dict):
            continue
        options = variant.get("options")
        if isinstance(options, dict):
            labels.extend(str(value) for value in options.values() if value)
        elif isinstance(options, list):
            for option in options:
                if isinstance(option, dict):
                    raw = option.get("value") or option.get("title") or option.get("name")
                    if raw:
                        labels.append(str(raw))
    labels = list(dict.fromkeys(label for label in labels if label))
    return "Options: " + ", ".join(labels[:8]) if labels else ""
```

Then replace the public read success block in `_route_and_maybe_execute`:

```python
if public_response:
    return _format_public_read_result(result)
```

Keep `MessageBubble` collapsing JSON on the frontend.

- [ ] **Step 4: Run summary and regression tests**

```powershell
python -m pytest backend/tests/test_rest_catalog.py::test_public_read_result_summarizes_named_item_and_options_without_ids backend/tests/test_rest_catalog.py::test_rest_operator_does_not_fill_optional_search_with_bare_list_request -q
```

Expected: PASS.

- [ ] **Step 5: Commit Task 5**

```powershell
git add backend/services/agent/rest_operator.py backend/tests/test_rest_catalog.py
git commit -m "fix: summarize public read results"
```

---

## Task 6: Guide Update And Manual Browser Proof

**Files:**
- Modify: `docs/medusa-api-agent-test-guide.md`

- [ ] **Step 1: Update the testing guide to remove ambiguity**

In `docs/medusa-api-agent-test-guide.md`, add a short note near the top:

```markdown
## Manual E2E Meaning

For Medusa acceptance, "E2E" means using the rendered app like a real owner and visitor:

- create the owner and agent through the UI
- connect and activate the API through the UI
- deploy the public chat through the UI
- chat from `/a/{slug}` through the UI
- approve Sandbox Learning candidates through the owner UI
- provide screenshot proof of every major state transition

The automated harness is a smoke/regression aid. It does not replace the manual browser acceptance pass.
```

- [ ] **Step 2: Add fixed-flow acceptance checklist**

Append to the guide after the checkout continuation section:

```markdown
### Fixed-flow regression checklist

- Refreshing `/a/{slug}` restores the current visitor transcript.
- Navigating to owner Sandbox Learning and returning to `/a/{slug}` does not require starting the checkout over.
- The Learning list requires opening review before approval.
- `use Express Shipping` selects the generated shipping-method action when the option was presented by the agent.
- The final trace includes successful shipping-method, payment-session, and complete-cart calls.
- Public transcript does not show cart ids, variant ids, option ids, payment collection ids, endpoint paths, trace ids, operation ids, or raw tool labels.
```

- [ ] **Step 3: Run backend and frontend validation**

```powershell
cd "D:\Dev\AI Projects\agent-core\agent-lab-powered-projects\saastoagent-v0.1"
python -m pytest backend/tests/test_deployed_public_sessions.py backend/tests/test_app_graph_contract.py backend/tests/test_execution_frames.py backend/tests/test_rest_catalog.py backend/tests/test_api_orchestration.py backend/tests/test_toolrouter_fusion_ranker.py -q

cd "D:\Dev\AI Projects\agent-core\agent-lab-powered-projects\saastoagent-v0.1\frontend"
npm run type-check
```

Expected: PASS.

- [ ] **Step 4: Restart app stack**

```powershell
cd "D:\Dev\AI Projects\agent-core\agent-lab-powered-projects\saastoagent-v0.1"
docker compose up -d --build backend frontend

cd "D:\Dev\AI Projects\agent-core\test_targets"
docker compose up -d --build
```

Expected:

- SaaStoAgent frontend at `http://localhost:3007`
- SaaStoAgent backend at `http://localhost:8085`
- Medusa backend at `http://localhost:9000`

- [ ] **Step 5: Manual browser E2E with screenshots**

Use the in-app browser as the visitor. If the owner approval flow needs a second mounted session, use a separate browser context only for the owner UI and state that explicitly in the closeout.

Capture screenshots for:

- API activation ready
- Deployment saved
- Public chat ready
- Product list
- Product detail/selection summary
- Add-to-cart blocked before approval
- Owner policy candidate detail review
- Add-to-cart success after approval
- Checkout shipping choices
- Shipping method approval if needed
- Final checkout success
- Refresh/restore of the public chat transcript

- [ ] **Step 6: Verify backend traces**

Run:

```powershell
cd "D:\Dev\AI Projects\agent-core\agent-lab-powered-projects\saastoagent-v0.1"
docker compose exec -T db psql -U postgres -d saastoagent_v0_1 -c "select tool_name, status, method, path, inputs, missing_inputs, approval_state, created_at from agent_execution_traces order by created_at desc limit 12;"
```

Expected latest successful chain includes:

```text
postcartsidshippingmethods | succeeded | POST | /store/carts/{id}/shipping-methods | ... option_id ... | [] | approved_by_policy
postpaymentcollectionsidpaymentsessions | succeeded | POST | /store/payment-collections/{id}/payment-sessions | ... provider_id ... | [] | approved_by_policy
postcartsidcomplete | succeeded | POST | /store/carts/{id}/complete | ... | [] | approved_by_policy
```

- [ ] **Step 7: Verify no duplicate blank policy candidates**

Run:

```powershell
docker compose exec -T db psql -U postgres -d saastoagent_v0_1 -c "select status, target_tool_name, target_action_path, evidence->'allowed_action_paths' as allowed_paths, created_at from agent_learning_candidates where trigger_type='domain_policy_gap' order by created_at desc limit 20;"
```

Expected:

- no new candidate has `allowed_paths` null or `[]`
- repeat failed/blocked attempts reuse matching proposed or approved candidates

- [ ] **Step 8: Commit Task 6**

```powershell
git add docs/medusa-api-agent-test-guide.md
git commit -m "docs: clarify manual Medusa E2E proof"
```

---

## Subagent Split

- Subagent A: Task 1 and Task 2. Owns frontend/public session restoration and Learning review UI. Reviews for RouteDeck boundary compliance and UI ergonomics.
- Subagent B: Task 3 and Task 4. Owns dynamic routing, pending-choice behavior, and policy dedupe. Reviews for no Medusa-specific hardcoding.
- Subagent C: Task 5 and Task 6. Owns public transcript polish, guide update, and manual screenshot evidence.
- Main agent: runs cross-suite validation, manually exercises the app, compares behavior against ADR/context, and writes the closeout.

---

## ADR/Product Guardrails

- Do not add phrase routers, alias tables, endpoint maps, or Medusa-specific special cases.
- Do not make RouteDeck decide product intent. RouteDeck remains the state/projection/dispatch boundary; Corpus remains the product agent.
- Do not expose endpoint paths, tool names, operation ids, trace ids, approval ids, cart ids, variant ids, option ids, payment ids, or credentials in public chat.
- Do not bypass owner approval for visitor write actions.
- Do not make the manual guide depend on scripts as proof. Scripts are supplemental.

---

## Final Verification Command Set

```powershell
cd "D:\Dev\AI Projects\agent-core\agent-lab-powered-projects\saastoagent-v0.1"
python -m pytest backend/tests/test_deployed_public_sessions.py backend/tests/test_app_graph_contract.py backend/tests/test_execution_frames.py backend/tests/test_rest_catalog.py backend/tests/test_api_orchestration.py backend/tests/test_toolrouter_fusion_ranker.py -q

cd "D:\Dev\AI Projects\agent-core\agent-lab-powered-projects\saastoagent-v0.1\frontend"
npm run type-check
```

Manual pass is not complete until screenshots prove the owner and visitor browser flows listed in Task 6.

