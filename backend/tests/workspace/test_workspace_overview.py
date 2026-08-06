from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from corpus.features.workspace.http import (
    WorkspaceHttpProblem,
    create_workspace_router,
    workspace_problem_response,
)
from corpus.features.workspace.models import WorkspaceOverview, WorkspaceSectionState
from corpus.features.workspace.ports import WorkspaceOverviewUnavailable
from corpus.features.workspace.service import WorkspaceService


class WorkspaceOverviewProbe:
    async def overview_for_route(self, route_session_id: str) -> WorkspaceOverview:
        if route_session_id != "owner-route":
            raise WorkspaceOverviewUnavailable("The Workspace is unavailable.")
        return self._overview()

    async def overview_for_access_token(self, access_token: str) -> WorkspaceOverview:
        if access_token != "owner-token":
            raise WorkspaceOverviewUnavailable("Authentication is required.")
        return self._overview()

    @staticmethod
    def _overview() -> WorkspaceOverview:
        return WorkspaceOverview(
            agent_count=2,
            agents=WorkspaceSectionState(
                status="available",
                message="2 active agents in this Workspace.",
            ),
            sources=WorkspaceSectionState(
                status="unavailable",
                message="Sources are not connected.",
            ),
            recent_activity=WorkspaceSectionState(
                status="unavailable",
                message="Recent activity is not recorded.",
            ),
        )


def test_workspace_overview_http_requires_auth_and_preserves_availability_truth() -> None:
    app = FastAPI()
    app.add_exception_handler(WorkspaceHttpProblem, workspace_problem_response)
    app.include_router(create_workspace_router(WorkspaceService(WorkspaceOverviewProbe())))

    with TestClient(app) as client:
        missing = client.get("/api/workspace/overview")
        assert missing.status_code == 401
        assert missing.json()["code"] == "authentication_required"

        rejected = client.get(
            "/api/workspace/overview",
            headers={"Authorization": "Bearer wrong-token"},
        )
        assert rejected.status_code == 401

        overview = client.get(
            "/api/workspace/overview",
            headers={"Authorization": "Bearer owner-token"},
        )
        assert overview.status_code == 200
        assert overview.headers["cache-control"] == "private, no-store"
        assert overview.json() == {
            "agent_count": 2,
            "agents": {
                "status": "available",
                "message": "2 active agents in this Workspace.",
            },
            "sources": {
                "status": "unavailable",
                "message": "Sources are not connected.",
            },
            "recent_activity": {
                "status": "unavailable",
                "message": "Recent activity is not recorded.",
            },
        }
