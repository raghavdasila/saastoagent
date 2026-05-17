# SaaStoAgent v0.1 Workspace Agent Plan

This plan is superseded by
`plans/saastoagent_v0_1_saas_agent_foundation_plan.md`.

The workspace-as-agent model is no longer the active product contract. See
`decisions/ADR-010-saas-agent-domain-authority.md` for the accepted decision:
`SaaSAgent` replaces `Workspace` as the domain authority, and every SaaS Agent
owns its own RouteDeck runtime, connections, generated tools, RAG, memory,
sandbox learnings, QA evidence, and execution state.
