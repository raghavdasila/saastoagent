# Context Pipeline

Each fact has one primary owner:

| Information | Owner |
| --- | --- |
| North star and non-negotiables | `critical_prompt.md` |
| Current restart state and next step | `context.md` |
| Product behavior and feature design | `docs/` |
| Maintained folder map | `structure.md` |
| Runtime and owner-journey indexes | `SYSTEM_FLOW_INDEX.md` |
| Source ownership and validation anchors | `architecture/code-map.md` |
| Subsystem contracts and invariants | `architecture/components/` |
| Durable architecture decisions | `decisions/` |
| Active implementation work | `plans/` |
| Validation commands and meaning | `test_index/` |
| Session evidence | `logs/` and `context_checkpoints/` |
| Historical application evidence | `benchmark/` |

Do not turn `context.md` into architecture or repeat detailed feature contracts
across multiple documents. Link to the owner instead.
