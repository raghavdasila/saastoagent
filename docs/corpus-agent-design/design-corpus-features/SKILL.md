---
name: design-corpus-features
description: Drive bottom-up design of locked Corpus product features through atomic behavior inventories, user and agent intent, behavior-based user stories, mock product chats, explicit actions, and inline mock surfaces. Use when Codex is drafting, refining, or documenting how a Corpus feature should behave for user review before cross-feature workflow design, RouteDeck candidate extraction, specification, or implementation.
---

# Design Corpus Features

Drive the design studio while the user reviews, text-edits, corrects, and
approves the work. Keep turns short, present one atomic behavior or decision at
a time, and revise directly from the user's corrections.

## Required context

Before starting feature design, read:

1. `../../../critical_prompt.md`
2. `../../../context.md`
3. `../corpus-agent-design-document.md`
4. `../feature-behavior-notes.md`
5. `../routedeck-design-glossary.md`

Before extracting RouteDeck candidates in step 10, additionally read:

6. `../routedeck-feature-and-node-design-guide.md`

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
- **Codex drives the studio; the user reviews it.** Codex maintains the behavior
  inventory, drafts the current story and supporting artifacts, and advances
  one approved step at a time. Their current conversation is not a mock product
  chat and must not be copied into a product story.
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
- **User intent** is the meaning or outcome the future user wants in the defined
  situation. It is not the user's exact wording, a button label, or a runtime
  intent classification.
- **Agent intent** is the specific outcome the responsible Corpus agent is
  expected to produce in the defined situation, together with an observable
  success condition. Keep it independent of prompts, models, tools, thresholds,
  workflow order, confidence values, and UI behavior. It is design guidance,
  not RouteDeck state or a runtime contract.
- **An action** is a direct choice or command available to the user. Record it
  separately from a surface; an action does not warrant a surface by itself.
- **A mock surface** is a disposable interaction sketch used to expose needed
  information, structured controls, state, and feedback inline immediately
  above the chat composer. It is not a dialog, modal, approved UI design, or
  implementation contract.
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

Follow the user-approved feature order. If no order exists, propose the next
locked feature for approval rather than choosing a convenient pilot or starting
with the complete launch journey.

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
- **User intent:** the meaning or outcome the future user is trying to achieve.
- **Agent intent:** the outcome the responsible Corpus agent owns and the
  observable condition that indicates success.
- **Product behavior:** what Corpus visibly does.
- **Observable outcome:** what must be true when the behavior completes.
- **Ownership:** why this feature owns the behavior.

Avoid generic "As a user" wording when a concrete actor and situation are more
informative. Intent guidance does not replace the observable story and outcome.

### 4. Create mock product interactions

Use only the artifacts that clarify the behavior:

- Write a short mock product chat when conversation is materially involved.
- Record direct user choices or commands as actions, separate from surfaces.
- Sketch a mock surface when the user must inspect state, compare information,
  provide structured input, or receive structured feedback.
- Combine chat and surface when one guides or updates the other.
- An action-only behavior has no surface. For example, `Create an agent` is an
  action unless the behavior exposes structured state or input that needs a
  surface.
- Place a mock surface inline immediately above the action row and chat
  composer. Let it grow to its content height until half the chat region, then
  scroll internally. Do not present it as a modal or dialog.
- Do not force a chat into behavior that is clearer as a direct action.
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

Present a small draft, decision, or question. Let the user review or text-edit
it. Revise before expanding.

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

Use `../routedeck-design-glossary.md` for vocabulary and
`../routedeck-feature-and-node-design-guide.md` for the extraction sequence and
review questions. Label the result as a candidate mapping until separately
approved. RouteDeck extraction does not authorize implementation. Do not add
Navgraph design to the atomic behavior workspace before this stage.

## Working format

Use this compact structure while exploring one behavior:

```markdown
### Behavior: <short name>

**Situation:** <starting state and trigger>

**User intent:** <meaning or outcome the user wants>

**Agent intent:** <responsible outcome and observable success condition>

**Expected behavior:** <observable Corpus response>

**Mock product chat:**
<only if useful>

**Actions:**
<direct choices or commands, only if useful>

**Mock surface:**
<only if useful>

**Outcome:** <observable completion state>

**Variations:** <only meaningful branches>

**Open questions:** <unknowns requiring design judgment>
```

Do not fill every heading ceremonially. Omit chat, actions, surface, variations,
or open questions when they add no design value.

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
