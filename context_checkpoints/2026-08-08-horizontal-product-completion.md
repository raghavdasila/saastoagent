# Horizontal Product Completion Checkpoint

> Superseded as a completion claim on 2026-08-09. The implementation remains a
> useful horizontal baseline, but architecture-visible Designer/NavGraph work,
> behavior-note reconciliation, and independent chat-only, surface-only, and
> hybrid evidence are active again. See `context.md` and
> `plans/2026-08-09-designer-navgraph-alignment.md`.

The approved behavior-led horizontal plan is implemented across Sources,
Agents, Designer, Builder, Sandbox, Evaluation, Channels/Deployment, public
sessions, and Operations.

Passing joined run: `20260808T100957Z-f63809ea83` (13/13).

Evidence root:
`artifacts/horizontal-product/20260808T100957Z-f63809ea83/`.

Final gates: backend 338 passed; frontend 105 passed before the final
Operations-navigation regression plus focused Agent surfaces 14 passed;
Studio 49 passed; frontend/Studio typecheck, frontend build, generated
contract, Studio parity, and architecture boundaries passed.

Runtime must include the Ollama override:
`docker compose -f compose.yaml -f .runtime/horizontal-ollama.compose.yaml up -d backend frontend source-worker`.

Next work is individual depth and defects, especially the real Medusa
`GetProductsId` response-contract mismatch and public Markdown presentation.
Do not reopen horizontal feature scaffolding.

Boundaries retained: no Git, no RouteDeck edits, no user behavior-note edits.
