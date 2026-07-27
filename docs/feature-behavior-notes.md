# Corpus Basic Agent Feature Behavior Notes

Updated: 2026-07-27

Status: Owner-authored working notes. These describe the intended launch baseline and are not detailed product specifications. Each feature will be explored further before implementation.

## Minimal end-to-end behavior baseline

For launch, Corpus should prove one minimal viable path through the product:

Create an agent -> upload an API YAML file -> attach the source -> generate a RouteDeck-powered agent -> run a real sandbox interaction -> evaluate it -> deploy it to a hosted Web URL -> interact with it publicly -> inspect the interaction in Operations.

## 1. Workspace

A Workspace contains the user's agents, sources, and related activity.

For launch, one user has one Workspace. Inviting other users and supporting multi-user Workspaces are deferred.

## 2. Agents

The user can create a draft agent with a name, description, and goal.

An agent brings together:

- its identity, goals, non-goals, and other prompt/configuration inputs;
- its attached sources;
- its Agent Designer/RouteDeck configuration;
- its runnable and deployed versions; and
- its deployed URL when one is active.

Editing a source takes the user to that source. Adding a source lets the user select an existing source or upload a new one, then returns them to the agent with it attached.

## 3. Source Hub

Source Hub is where users add, view, and manage sources that can be attached to agents.

Corpus may later support APIs, databases, knowledge sources, and MCP servers. For launch, the only source type is an API collection uploaded as a YAML file.

## 4. API Source / API Collection

An API collection is the launch source type and is powered by ToolRouter.

The user uploads an API YAML file and can see whether it was processed successfully and is ready to use. ToolRouter inputs, outputs, and generated artifacts remain isolated by Workspace and user.

## 5. Agent Designer

Agent Designer is powered by RouteDeck. It uses the agent's goal and selected API operations to propose a runnable RouteDeck agent configuration for the user to review.

For the launch baseline, it only needs to produce a viable agent for the end-to-end API-backed pathway. Deeper design controls and planner/executor choices will be explored separately.

## 6. Agent Builder

Agent Builder does not need to appear as a separate user-facing feature. It can be the build step within Agent Designer.

After the user accepts the design, this step produces the runnable agent version used by Sandbox, Evaluation, and Deployment.

## 7. Sandbox

Sandbox is a playground for running the actual draft agent without unintended real-world impact.

For the minimal end-to-end proof, the agent performs at least one safe real API operation. This can be a read-only operation or an action against a sandbox account supplied by the user. The user is responsible for ensuring supplied credentials belong to a real sandbox account.

API-schema-generated responses can support exploration, but they are clearly shown as simulations and do not count as proof of the real integration.

Each interaction records how the query was resolved, including the decisions and API activity involved. The detailed UI will be explored later.

## 8. Evaluation

Users can generate and configure evalsets with ToolRouter, as well as add, remove, or edit evaluation cases.

For the baseline, an evalset runs against the exact draft agent version and produces a simple eligible or ineligible result for deployment, with basic metrics visible to the user.

Users can also create an evaluation case from a real agent interaction recorded in Operations.

## 9. Channels

Channels are the places where deployed agents interact with users, such as Web, embedded websites, Slack, or WhatsApp.

For launch, Corpus supports only a hosted Web channel on the Corpus platform. Other channels are deferred.

## 10. Deployment

Deployment publishes an eligible agent version to its configured channel.

For the baseline, the user deploys the evaluated version to the hosted Web channel and can see which version is currently active and its public URL.

## 11. Operations

Operations shows the activity of the deployed agent.

For the baseline, a public Web interaction appears here with its result, API activity, and decision trace. The user can turn that interaction into a new evaluation case for future agent versions.
