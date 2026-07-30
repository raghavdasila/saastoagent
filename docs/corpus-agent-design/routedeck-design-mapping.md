# Agent Design Studio to RouteDeck mapping

This document defines where each design object is implemented in RouteDeck.
The Studio owns product-design text; RouteDeck owns the executable contracts
that scope that text to the current interaction context.

The Studio does not contain or author RouteDeck identifiers. Technical IDs live
only in the implementation-owned manifest at
`contracts/corpus-agent-design-routedeck-manifest.json`.

## Feature prompts

| Design Studio path | RouteDeck destination | Corpus declaration |
| --- | --- | --- |
| `feature.prompt` | `Feature.agent_prompt` | `backend/src/corpus/features/<feature>/prompt.py`, referenced by that feature's `Feature(...)` declaration |

The application-wide Corpus identity remains the LangChain base system prompt
in `backend/src/corpus/runtime/prompt.py`. RouteDeck composes the model request
in this order:

1. application base prompt;
2. prompt from the `Feature` that owns the current `Node`;
3. resolved AgentPolicies;
4. current RouteDeck JSON context.

## AgentPolicies

Every non-empty Studio policy instruction becomes one product-authored
`AgentPolicy(id=..., instruction=...)`. RouteDeck requires the stable ID for
compilation and references; the Studio intentionally authors only the policy
text. Conversion assigns the implementation ID without adding it to the design
UI.

All AgentPolicy definitions for a feature are registered once through
`Feature.agent_policies`. Activation is then declared at the exact designed
scope:

| Design Studio path | RouteDeck activation field | Resolved when |
| --- | --- | --- |
| `feature.policies[]` | `Feature.policy_refs` | The current Node belongs to the feature. |
| `feature.stories[].nodePolicies[]` | `Node.policy_refs` | That behavior's Node is current. |
| `feature.stories[].capabilities[].policies[]` | `Capability.policy_refs` | The Capability belongs to the current Node. |
| `feature.stories[].surfaces[].policies[]` | `Surface.policy_refs` | That Surface is the active Surface, not merely declared in another slot. |
| `feature.stories[].operations[].policies[]` | `Operation.policy_refs` | That Operation is currently legal. |

There is no RouteDeck `Behavior` policy scope. A Studio behavior is the design
view of a RouteDeck `Node`, so its policies map to `Node.policy_refs`.
Suggested Actions do not own AgentPolicies; they reference Operations, whose
policies are resolved when those Operations are legal.

## Policy definition and activation are separate

The implementation has two necessary layers:

```text
Studio instruction
  -> AgentPolicy definition in the owning feature
  -> stable AgentPolicyRef on the designed Feature/Node/Capability/Surface/Operation
  -> RouteDeck resolves only refs active for the current session
  -> middleware injects the resolved instructions into the model request
```

Registering a policy in `Feature.agent_policies` does not activate it. A
matching `policy_refs` entry at its designed scope is required. Conversely, a
reference to an unregistered policy fails RouteDeck compilation.

## Corpus implementation destinations

| Concern | Destination |
| --- | --- |
| Corpus application prompt | `backend/src/corpus/runtime/prompt.py` |
| Lounge feature prompt | `backend/src/corpus/features/lounge/prompt.py` |
| Lounge AgentPolicy definitions | `backend/src/corpus/features/lounge/policies.py` |
| Lounge Feature, Node, Capability, and Surface policy references | `backend/src/corpus/features/lounge/feature.py` |
| Lounge Operation declarations and Operation policy references | `backend/src/corpus/features/lounge/declarations.py`; every designed Operation policy must be added to the corresponding `Operation.policy_refs` during conversion |
| RouteDeck scope resolution | `routedeck_core/context/agent.py` |
| RouteDeck prompt composition | `routedeck_langgraph/prompt.py` and `routedeck_langgraph/middleware.py` |

## Conversion rule

Conversion must preserve the Studio instruction verbatim and preserve its
scope. It may deduplicate the same instruction into one AgentPolicy definition,
but every designed activation site must retain its own reference. It must not
promote a narrow policy to a broader scope, collapse an Operation policy into a
Node policy, or treat policy registration as activation.

## Parity enforcement

Run:

```powershell
.\.venv\Scripts\python.exe scripts\check_agent_design_parity.py
```

The checker loads the saved Studio state, the implementation-owned mapping
manifest, and the compiled Corpus RouteDeck application. It compares only
product shape and boundaries:

- application feature coverage;
- one behavior to one RouteDeck Node;
- feature prompts;
- Feature, Node, Capability, Surface, and Operation policy text and scope;
- Capability membership;
- Node-owned Capabilities, Surfaces, and Operations;
- SuggestedAction labels and Operation targets.

It does not prescribe source files, framework adapters, handlers, transports,
databases, or other technical implementation choices. RouteDeck IDs appear in
the manifest because they are needed to inspect the compiled application; they
never become Studio fields.

Missing mappings, missing implementation objects, extra compiled shape, moved
or consolidated policies, and altered prompt/policy text return a non-zero exit
code. The default report groups those mismatches by root-cause category and
shows policy drift direction separately; pass `--verbose` to append every
scope-level mismatch. Invalid checker inputs return exit code 2.
