# Deployed Agent Orchestration

## Purpose

This component owns the public visitor chat path for deployed SaaS Agents. It
connects public chat to generated OpenAPI actions, execution-frame variables,
domain policy checks, learning candidates, and public-safe response shaping.

## Owner Files

- `backend/routes/deployed_agents.py`
- `backend/services/deployed_agents.py`
- `backend/services/deployed_agent_events.py`
- `backend/services/agent/api_orchestration.py`
- `backend/services/agent/chat_service.py`
- `backend/services/agent/execution_frames.py`
- `backend/services/agent/state_variables.py`
- `backend/services/agent/learning_service.py`
- `backend/services/agent/anonymous_rate_limiter.py`
- `frontend/src/pages/DeployedAgentChatPage.tsx`

## Public Interfaces

- `/a/{slug}`
- `/api/deployed-agents/{slug}`
- Public chat requests and streaming responses for deployed agents.
- Execution-frame variable persistence for generated API chains.

## Dependent Flows

- Visitor product questions.
- Generated OpenAPI action selection and execution.
- Public-safe handling of missing inputs.
- Learning policy gaps for write chains.
- Continuity from prior product results into follow-up turns.

## Tests And Evidence

- `backend/tests/test_api_orchestration.py`
- `backend/tests/test_execution_frames.py`
- `backend/tests/test_state_variables.py`
- `backend/tests/test_learning_service.py`
- `backend/tests/test_deployed_agent_access.py`
- `test_index/deployed-agent-orchestration-contract.md`
- `frontend/scripts/e2e-medusa-docker.mjs`

## Update Triggers

Update this component doc and the code map when changing:

- Public deployed-agent route shape.
- Public chat response shaping or safety filtering.
- Execution-frame variable storage.
- Generated API orchestration.
- Learning policy-gap behavior.
- Anonymous access or rate limiting.
- Browser E2E acceptance criteria for the public fixture.
