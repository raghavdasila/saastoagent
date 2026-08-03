# Corpus Basic Agent Feature Behavior Notes

Updated: 2026-07-27

Status: Owner-authored working notes. These describe the intended launch baseline and are not detailed product specifications. Each feature will be explored further before implementation.

## Minimal end-to-end behavior baseline

For launch, Corpus should prove one minimal viable path through the product:

Create an agent -> upload an API YAML file -> attach the source -> generate a RouteDeck-powered agent -> run a real sandbox interaction -> evaluate it -> deploy it to a hosted Web URL -> interact with it publicly -> inspect the interaction in Operations.

SURFACE AND CHAT BOTH SHOULD ACCOMPLISH THE BASELINE INDIVIDUALLY AS WELL AS TOGETHER (MIXED). ONLY CREDENTIALS ARE EXCLUDED FROM CHATS.
when chat and surfaces are used together, they should continue the same task and show the same current state. switching between them should not restart the work or repeat an action.

## Corpus-wide AutomationBench validation goal

AutomationBench is not a separate Corpus feature and is not part of the minimal launch pathway. It is an overall validation target for both:

- Corpus itself as an agentic system; and
- agents designed and produced through Corpus.

In either case, the system being evaluated is treated as Agent X. Agent X may internally use RouteDeck, multiple agents, RAG, memory, or other supporting components.

AutomationBench gives Agent X a business task and access to its own `api_search` and `api_fetch` tools. Agent X discovers and calls the relevant simulated APIs, while the benchmark validates whether the final application state is correct.

The benchmark does not provide its complete API catalog as one uploaded source. Corpus should therefore connect through a narrow benchmark adapter that exposes the benchmark-supplied discovery and execution tools without replacing or pre-importing its API catalog.

This evaluates whether Corpus and Corpus-produced agents can discover operations, coordinate workflows, follow policies, and complete correct multi-application outcomes. It does not validate Corpus's normal API YAML upload pathway.

## Shared Async Behaviour
for API Source, Agent Builder, Evaluation, and Deployment
one important thing is that processing/building/evaluation/deployment may take time. the user should be able to leave and come back and still see the actual status and results separately. failures must remain failures and retry should be explicit. 

## 0. Lounge

Lounge is for unauthenticated users.
Lounge has all the sign in, sign up, forgot password stuff along with general helpdesk which users can ask about the product. add this to design studio by adding the feature as well as the user stories.

Actions
- sign in
- sign up
- forgot password
- ask about the product

## 1. Workspace

A Workspace contains the user's agents, sources, and related activity.
Workspace doesnt offer functionality to add modify those agents/sources etc. but acts as like a "home page" such that agent has a place to navigate to those places easilty.
Quick actions are offered here to Manage Agents, Manage Operations etc.
For launch, one user has one Workspace. Inviting other users and supporting multi-user Workspaces are deferred.

Actions
- ask general info about what's going on in the workspace, any query
- ask general info about the platform itself
- ask to do any task literally and the agent should navigate to the correct node and continue conversation

## 2. Agents

The user can create a draft agent with a name, description, and goal.

An agent brings together:

- its identity, goals, non-goals, and other prompt/configuration inputs;
- its attached sources;
- its Agent Designer/RouteDeck configuration;
- its runnable and deployed versions; and
- its deployed URL when one is active.

Editing a source takes the user to that source. Adding a source lets the user select an existing source or upload a new one, then returns them to the agent with it attached.

Actions
- view my agents
- create an agent 
- edit agent
- archive agent
- delete agent


## 2.5

separate node for operations of a specific agent
[selected agent]
- view in agent designer
- view builds
- try in sandbox
- view evalsets


## 3. Source Hub

Source Hub is where users add, view, and manage sources that can be attached to agents.

Corpus may later support APIs, databases, knowledge sources, and MCP servers. For launch, the only source type is an API collection uploaded as a YAML file.

Actions
 - users can add API source
 - users can delete API source
 - users can upload a markdown file (with size limits) which provides helpful description about the API

## 4. API Source / API Collection

An API collection is the launch source type and is powered by ToolRouter.

The user uploads an API YAML file and can see whether it was processed successfully and is ready to use. ToolRouter inputs, outputs, and generated artifacts remain isolated by Workspace and user.
navigated ONLY from source hub.
this also must show grouping of the api collections as identified by semantic graph

actions:
- upload API file.
- configure api details such as auth, baseurl or whatever, check saastoagent earlier one
- process api collection via ToolRouter to make semantic graph, this graph must be shown to the user, toolrouter has visualizers which have node by node playback somewhere in the code which might help. if we can show live parsing as the graph develops, that would be great.

## 5. Agent Designer

Agent Designer is powered by RouteDeck. It uses the agent's goal and selected API operations to propose a runnable RouteDeck agent configuration for the user to review.

For the launch baseline, it only needs to produce a viable agent for the end-to-end API-backed pathway. Deeper design controls and planner/executor choices will be explored separately.

- miniature version of agent design studio as surfaces
- based on semantic graph groups and api anlaysis, the agent design studio appears prepopulated with how the agent should be
- navgraph is presented as well.

actions:

- user can add feature, describe behaviours, agent populates polices, capabilities and locks in the relevant api subcollections and tools based on that
- user can approve/reject/customize suggestions.
- once approved, the agent design is saved, linked with the agent selected.
- build agent (takes to agent builder)

## 6. Agent Builder
Why agent builder is separate from agent designer?  agent design is like schema saved but the agent doesn't actually run.
Agent builder actually converts the agent design into a routedeck powered agent ready to be tested in sandbox and generate evalsets.
The best way I can describe this in terms of product is this is like how a service or vps is provisioned in infra projects.
using schema, the agent can be started/stopped/paused etc.
agent builder automatically generates the evalsets too on a agent build
each built agent has its own execution runtime. its state, conversations and results remain separate from Corpus and from other agents. sandbox and deployed results are also viewed separately.
one important thing to note that is the built must be isolated [to explore]

actions
- generate build from an agent
- run build
- delete a build
- stop a build
- open in sandbox

## 7. Sandbox

Sandbox is a playground for running the actual draft agent without unintended real-world impact.

For the minimal end-to-end proof, the agent performs at least one safe real API operation. This can be a read-only operation or an action against a sandbox account supplied by the user. The user is responsible for ensuring supplied credentials belong to a real sandbox account.

API-schema-generated responses can support exploration, but they are clearly shown as simulations and do not count as proof of the real integration.

Each interaction records how the query was resolved, including the decisions and API activity involved. The detailed UI will be explored later.

one important thing to note is that the sandboxed agent has its own execution runtime. its conversations, state and results are kept separate and can be viewed separately from deployed agent activity.

- chat with agent, user can view navgraph diagnostics here fully. [NAVGRAPH FEATURE ISN'T AVAILABLE TO END USERS OF THE AGENT, ONLY THE OWNER]
- view sandbox operations traces in a separate surface


## 8. Evaluation

Users can generate and configure evalsets with ToolRouter, as well as add, remove, or edit evaluation cases.

For the baseline, an evalset runs against the exact draft agent version and produces a simple eligible or ineligible result for deployment, with basic metrics visible to the user.

Users can also create an evaluation case from a real agent interaction recorded in Operations.
evaluation's category, difficulty etc. all should be present
powered by toolrouter evalset generator

- simple list/table style surfaces allowing people to CRUD evaluations

## 9. Channels

Channels are the places where deployed agents interact with users, such as Web, embedded websites, Slack, or WhatsApp.

For launch, Corpus supports only a hosted Web channel on the Corpus platform. Other channels are deferred.

the url must be uniquely generated and should be capable of linking with some other domain [to explore]

## 10. Deployment

Deployment publishes an eligible agent version to its configured channel. conceptually it exposes a built agent online.

For the baseline, the user deploys the evaluated version to the hosted Web channel and can see which version is currently active and its public URL.

## 11. Operations

Operations shows the activity of the deployed agent.

For the baseline, a public Web interaction appears here with its result, API activity, and decision trace. The user can turn that interaction into a new evaluation case for future agent versions.
