---
name: design-corpus-features
description: Design the locked Corpus product features bottom-up through atomic behavior inventories, behavior-based user stories, mock product chats, and mock surfaces. Use when Codex and the user are exploring, refining, or documenting how a Corpus feature should behave before cross-feature workflow design, RouteDeck contract extraction, specification, or implementation.
---

# Design Corpus Features

Work as the user's design collaborator. Keep brainstorming turns short, present
one behavior or decision at a time, and revise directly from the user's
corrections.

## Required context

Before starting feature design, read:

1. `../../../critical_prompt.md`
2. `../../../context.md`
3. `../corpus-agent-design-document.md`
4. `../feature-behavior-notes.md`
5. `../routedeck-design-glossary.md`

Treat the product definition and live implementation as supporting evidence
when a question requires them. Do not treat historical benchmark material as
current architecture or access an off-limits benchmark checkout.

## Boundaries

Keep these identities separate throughout the work:

- **Corpus** is the product being designed. The stories and mocks describe
  future observable Corpus behavior.
- **Codex** is the user's collaborator in the present design session. Analyze,
  question, draft, simulate, and revise. Do not insert Codex into Corpus as a
  product feature, runtime actor, or product persona unless the user explicitly
  decides that separately.
- **The user and Codex design together.** Their current conversation is not a
  mock product chat and must not be copied into a product story.
- **A mock product chat** simulates a future interaction inside Corpus. Name its
  future product actors according to the behavior being explored; do not call
  it an Owner-Codex conversation by default.
- **Agent Designer** is one locked Corpus feature. It helps a Corpus user shape
  a deployed agent; it is not Codex, the overall Corpus design process, or the
  whole Corpus application.
- **A deployed agent** is an output managed by Corpus. It is distinct from
  Codex, Corpus itself, and the Agent Designer feature.
- **A feature** is a locked product ownership boundary. It is not automatically
  a screen, a user story, a workflow step, or a RouteDeck node.
- **A behavior** is one observable thing a future user can accomplish or
  experience through a feature.
- **A user story** is a design lens for one behavior, not a complete feature
  specification.
- **A mock surface** is a disposable interaction sketch used to expose needed
  information, controls, state, and feedback. It is not an approved UI design
  or implementation contract.
- **RouteDeck** is the later interaction-state and execution authority. Do not
  begin with nodes or force early behavior ideas into RouteDeck vocabulary.
  Extract candidate nodes, operations, outcomes, providers, guards, surfaces,
  affordances, and transitions only after feature behavior is accepted.
- **ToolRouter** supplies API-processing and evaluation capabilities where the
  locked boundaries say it does. It does not own Corpus product behavior.
- **AutomationBench** is a Corpus-wide validation target, not a Corpus feature,
  source-upload pathway, or dependency of this design workflow.

Do not turn these sessions into implementation planning. Do not edit source,
write runtime contracts, or call behavior a specification unless the user
explicitly advances the work to that stage.

## Bottom-up workflow

### 1. Select one locked feature

Let the user choose the feature. Do not choose a convenient pilot or begin with
the complete launch journey.

Restate its current one-line boundary and identify only material ambiguities.
Do not expand its scope.

### 2. Inventory atomic behaviors

List small, observable user behaviors owned by that feature. Phrase each as a
user accomplishment or product response, not as a component, page, database
entity, RouteDeck node, or implementation task.

Keep cross-feature dependencies visible as questions or handoffs. Do not solve
them prematurely.

### 3. Explore one behavior

For one behavior at a time, draft:

- **Situation:** relevant starting state and trigger.
- **User need:** what the future user is trying to achieve.
- **Product behavior:** what Corpus visibly does.
- **Observable outcome:** what must be true when the behavior completes.
- **Ownership:** why this feature owns the behavior.

Avoid generic "As a user" wording when a concrete actor and situation are more
informative.

### 4. Create mock product interactions

Use only the artifacts that clarify the behavior:

- Write a short mock product chat when conversation is materially involved.
- Sketch a mock surface when the user must inspect state, compare information,
  provide structured input, or invoke an action.
- Combine chat and surface when one guides or updates the other.
- Do not force a chat into behavior that is clearer as a direct surface action.
- Do not force complex state into prose when a surface should carry it.

For every mocked moment, make clear:

- who initiated it;
- what information Corpus already knows;
- what Corpus asks for or presents;
- what the user can decide or change;
- whether an approval is meaningful;
- what action Corpus performs; and
- what visible state or result follows.

Use compact text wireframes unless the user requests a higher-fidelity artifact.

### 5. Explore meaningful variations

Cover only variations that reveal product behavior:

- edit or correction;
- approve or reject;
- cancel or defer;
- missing or ambiguous information;
- dependency or operation failure;
- recovery; and
- leave and return later.

Keep failures as failures. Do not invent mock, cached, heuristic, or alternate
success paths.

### 6. Review with the user

Present a small draft, decision, or question. Let the user correct the product
intent. Revise before expanding.

Mark a behavior accepted only when the user explicitly approves it. Preserve
unresolved questions without converting assumptions into decisions.

### 7. Consolidate the feature

After its individual behaviors are accepted, summarize:

- accepted behavior stories;
- shared product state and vocabulary;
- recurring surface patterns;
- internal behavior relationships;
- explicit exclusions;
- unresolved questions; and
- cross-feature handoffs that need later design.

This is the feature behavior model, not yet a RouteDeck design or product spec.

### 8. Repeat across features

Apply the same workflow independently to the other locked features. Do not let
an assumed end-to-end journey dictate behaviors top-down.

### 9. Connect feature handoffs

Only after the relevant features have accepted behavior models, explore their
handoffs and validate that they can form the minimal launch pathway. Revise the
owning feature behavior when a handoff exposes a genuine gap.

### 10. Extract RouteDeck candidates

Only after behavior approval, translate observed requirements into candidate:

- nodes and routes;
- operations and outcomes;
- outgoing transitions;
- context and entity providers;
- guards and review gates;
- capabilities and policies;
- surfaces, slots, and affordances;
- public projection and private bindings; and
- recovery behavior.

Use `../routedeck-design-glossary.md` consistently. Label the result as a
candidate mapping until separately approved. RouteDeck extraction does not
authorize implementation.

## Working format

Use this compact structure while exploring one behavior:

```markdown
### Behavior: <short name>

**Situation:** <starting state and trigger>

**User need:** <specific desired result>

**Expected behavior:** <observable Corpus response>

**Mock product chat:**
<only if useful>

**Mock surface:**
<only if useful>

**Outcome:** <observable completion state>

**Variations:** <only meaningful branches>

**Open questions:** <unknowns requiring design judgment>
```

Do not fill every heading ceremonially. Omit chat, surface, variations, or open
questions when they add no design value.

## Session handoff

At the end of a design session, record only what the user requests. If asked to
update the design documents, preserve:

- feature and behavior being explored;
- accepted behavior;
- rejected alternatives when they prevent repeated mistakes;
- unresolved questions;
- next behavior to explore; and
- whether RouteDeck extraction has been authorized.

Do not stage, commit, push, implement, or broaden documentation ownership
without explicit user instruction.
