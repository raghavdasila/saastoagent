# Corpus RouteDeck/Medusa Boundary Audit

Date: 2026-07-22  
Comparison source: `D:\Dev\AI Projects\routedeck\examples\medusa-agent`

## Result

Pass for the implemented Workspace/Lounge scope after remediation. Corpus
preserves the same core split as RouteDeck's Medusa example and does not
reimplement RouteDeck state, legality, dispatch, projection, or transport.

## File-Level Comparison

| Responsibility | Medusa example | Corpus | Result |
| --- | --- | --- | --- |
| Feature selection and entry node | `backend/medusa_agent/composition.py` | `backend/src/corpus/composition.py` | Same boundary |
| Feature binding aggregation | `backend/medusa_agent/bindings.py` | `backend/src/corpus/bindings.py` | Same boundary |
| Product declarations and handlers | `backend/medusa_agent/features/**` | `backend/src/corpus/features/workspace/**` | Same boundary; Corpus scope is intentionally smaller |
| Host transport and lifecycle | `backend/main.py` plus example composition | `backend/src/corpus/app/**`, `main.py` | Corpus host is thinner and product-free |
| Model/runtime adapters | `backend/medusa_agent/agent.py` and live composition | `backend/src/corpus/runtime/**` | Same dependency direction; Corpus uses native Ollama |
| RouteDeck client/registry bridge | `frontend/src/routedeck/**` | `frontend/src/routedeck/**` | Same boundary |
| Product surfaces | `frontend/src/features/**` | `frontend/src/features/workspace/**` | Same boundary |
| React host | `frontend/src/app/**`, `ui/**` | `frontend/src/app/**` | Corpus generic host has no product literals/imports |
| Product composition | `frontend/src/main.tsx` | `frontend/src/main.tsx` | Same boundary |

## Remediated Findings

1. Workspace/Corpus selectors were moved from generic `src/styles.css` to
   feature-owned `features/workspace/workspace.css`.
2. Lounge/Corpus wording and the product greeting request ID were removed from
   generic `src/app/**`; the composition root now supplies the product ID.
3. The Ollama OpenAI-compatibility adapter and manual `/api/tags` parsing were
   replaced by native, pinned provider integrations.

## Remaining Boundary

Authentication submission and principal/session rotation remain deliberately
unimplemented until the RouteDeck middleware contract is ready. The visible
failure is feature UI; authentication truth stays host/middleware-owned.

When a second product feature is added, the current Workspace prompt injection
into the Corpus agent factory must evolve into node-scoped prompt selection.
That is a future extension seam, not a current Workspace-only violation.
