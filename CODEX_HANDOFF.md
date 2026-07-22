# Corpus Restart Handoff

Copy this prompt into a new session:

```text
Work in D:\Dev\AI Projects\saastoagent-v0.1. Start by following
AGENTIC_CODING_GUIDE.md and reading critical_prompt.md, context.md, the latest
checkpoint, instructions.md, context_pipeline.md, structure.md,
architecture/code-map.md, architecture/components/corpus-routedeck-boundary.md,
docs/corpus-product-definition.md, and
audits/2026-07-22-failed-minimum-corpus-implementation.md.

The repo is restored to the feature-free scaffold at commit f683bf2. Do not use
or restore the discarded implementation. benchmark/saastoagent-v0.1 is
read-only visual/behavior reference only.

First phase is READ-ONLY. Inspect the current GitHub repository
https://github.com/saastoagent/routedeck and its actual
examples/medusa-agent implementation. Do not infer Medusa from memory and do
not approximate its shell.

Produce, before any code:
1. the exact current Medusa backend and frontend trees relevant to composition;
2. an ASCII mapping from Medusa feature/declaration/binding/runtime/surface/UI
   ownership to the agreed Corpus scaffold and fifteen-feature product map;
3. the smallest feature-owned vertical proof that includes Lounge and auth
   inside the Navgraph, Corpus as the primary node-scoped chat agent, one real
   Corpus feature, Sandbox, and one RouteDeck-first deployed agent;
4. the exact files that would be added or changed, dependency/import method,
   runtime commands, and an E2E evidence matrix for chat-driven,
   surface-driven, and hybrid paths plus desktop/mobile Navgraph behavior.

Non-negotiables:
- features are code ownership boundaries; do not create a catch-all Corpus
  feature or monolithic applications.py/surfaces.tsx;
- Corpus is the agentic app and permanent chat interface; deployed outputs are
  agents, not “agentic apps”;
- nothing is outside the Navgraph, including Lounge and authentication;
- use the Medusa shell/composition pattern directly; Corpus colors and legacy
  behavior come only from the benchmark;
- RouteDeck owns interaction/session state; Corpus owns product meaning;
- do not change RouteDeck core without an explicit, separately approved need;
- do not write implementation until I approve the mapping and file plan;
- do not claim completion from unit/build checks; record the real running
  product and exercise every reachable path.

Stop after presenting the read-only mapping and plan for approval.
```
