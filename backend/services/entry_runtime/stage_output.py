from __future__ import annotations

from typing import Any

from backend.core.schemas import EntryGraphSession, EntryUIArtifact


def stage_output_payload(updates: dict[str, Any]) -> dict[str, Any]:
    payload: dict[str, Any] = {}

    if "node" in updates:
        payload["next_node"] = updates.get("node")
    if updates.get("messages"):
        payload["messages"] = [
            message.model_dump(mode="json") for message in updates["messages"]
        ]
    if updates.get("saas_agents"):
        payload["saas_agents"] = [
            saas_agent.model_dump(mode="json") for saas_agent in updates["saas_agents"]
        ]
    if updates.get("available_actions"):
        payload["available_actions"] = [
            action.model_dump(mode="json") for action in updates["available_actions"]
        ]
    if updates.get("persistent_actions"):
        payload["persistent_actions"] = [
            action.model_dump(mode="json") for action in updates["persistent_actions"]
        ]
    if updates.get("replace_path"):
        payload["replace_path"] = updates.get("replace_path")
    if updates.get("active_saas_agent_id"):
        payload["active_saas_agent_id"] = str(updates.get("active_saas_agent_id"))
    if updates.get("active_connection_id"):
        payload["active_connection_id"] = str(updates.get("active_connection_id"))
    if updates.get("connection_draft"):
        payload["connection_draft"] = updates.get("connection_draft")
    if updates.get("entry_draft"):
        payload["entry_draft"] = updates.get("entry_draft")
    if updates.get("platform_question_context"):
        payload["platform_question_context"] = updates.get("platform_question_context")
    if updates.get("canvas_artifacts"):
        payload["canvas_artifacts"] = updates.get("canvas_artifacts")
    if updates.get("follow_up_context"):
        payload["follow_up_context"] = updates.get("follow_up_context")
    if updates.get("transition_diagnostics"):
        payload["transition_diagnostics"] = updates.get("transition_diagnostics")
    if updates.get("ui_artifacts"):
        payload["ui_artifacts"] = [
            artifact.model_dump(mode="json") for artifact in updates["ui_artifacts"]
            if isinstance(artifact, EntryUIArtifact)
        ]
    if updates.get("route_deck_snapshot"):
        payload["route_deck_snapshot"] = updates.get("route_deck_snapshot")

    session_payload = updates.get("session_payload")
    if isinstance(session_payload, EntryGraphSession):
        payload["session"] = {
            "user": session_payload.user.model_dump(mode="json"),
            "token_type": session_payload.token_type,
        }

    return payload
