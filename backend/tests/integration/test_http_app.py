from __future__ import annotations

import asyncio
from pathlib import Path

from cryptography.fernet import Fernet
from fastapi.testclient import TestClient

from corpus.app.config import RouteDeckHostSettings
from corpus.auth.config import AuthSettings
from corpus.auth.migrations import upgrade_database
from corpus.features.sources.config import SourceSettings
from corpus.main import create_live_app
from corpus.runtime.config import CorpusRuntimeSettings
from corpus.runtime.prompt import CORPUS_AGENT_PROMPT
from routedeck_langgraph.prompt import (
    ROUTEDECK_CONTEXT_SECTION,
    ROUTEDECK_POLICY_SECTION,
)


def test_live_http_app_serves_a_bearer_selected_conversation(
    tmp_path: Path,
) -> None:
    auth_database_url = f"sqlite+aiosqlite:///{(tmp_path / 'auth.sqlite3').as_posix()}"
    asyncio.run(upgrade_database(auth_database_url))
    settings = CorpusRuntimeSettings(
        host=RouteDeckHostSettings(
            routedeck_database_url=(
                f"sqlite+pysqlite:///{(tmp_path / 'http.sqlite3').as_posix()}"
            ),
            routedeck_state_encryption_key=Fernet.generate_key().decode("ascii"),
            routedeck_instance_id="corpus-http-test",
            routedeck_review_ttl_seconds=300,
            routedeck_resume_capability_ttl_seconds=600,
            routedeck_worker_count=1,
            routedeck_browser_origins=("http://127.0.0.1:5199",),
        ),
        auth=AuthSettings(
            database_url=auth_database_url,
            migration_revision="0001_owner_auth",
            reset_secret="r" * 40,
            verification_secret="v" * 40,
            public_frontend_url="http://127.0.0.1:5199",
        ),
        sources=SourceSettings(data_root=tmp_path / "sources"),
        ollama_base_url="http://127.0.0.1:11434",
        ollama_model="gemma4:latest",
    )
    app = create_live_app(settings)

    with TestClient(app) as client:
        assert client.get("/healthz").json() == {"status": "ok"}
        assert client.get("/readyz").json() == {"status": "ready"}
        contract = client.get("/api/routedeck/contract")
        assert contract.status_code == 200
        assert contract.json()["frontend_contract"]["entry_node_id"] == "lounge.home"

        direct = client.post(
            "/api/routedeck/sessions",
            headers={"Origin": "http://127.0.0.1:5199"},
            json={"request_id": "direct-session-create"},
        )
        assert direct.status_code == 409
        assert direct.json()["code"] == "conversation_creation_required"

        anonymous = client.post(
            "/api/auth/anonymous",
            headers={"Origin": "http://127.0.0.1:5199"},
        )
        assert anonymous.status_code == 201
        assert "set-cookie" not in anonymous.headers
        access_token = anonymous.json()["access_token"]
        created = client.post(
            "/api/conversations",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Origin": "http://127.0.0.1:5199",
            },
            json={},
        )
        assert created.status_code == 201, created.text
        assert created.json()["current_node_id"] == "lounge.home"
        assert "route_session_id" not in created.text

        selected = client.get(
            "/api/routedeck/session",
            headers={
                "Authorization": f"Bearer {access_token}",
                "X-Corpus-Conversation-ID": created.json()["id"],
            },
        )
        assert selected.status_code == 200, selected.text
        assert selected.json()["projection"]["current"]["node_id"] == "lounge.home"

        inspected = client.get(
            "/api/routedeck/inspect",
            headers={
                "Authorization": f"Bearer {access_token}",
                "X-Corpus-Conversation-ID": created.json()["id"],
            },
        )
        assert inspected.status_code == 200, inspected.text
        agent_context = inspected.json()["agent_context"]
        assert agent_context["model_context"]["current_node"] == "lounge.home"
        policy_ids = {
            policy["policy_id"]
            for policy in agent_context["model_context"]["policies"]
        }
        assert "lounge.feature.public_context_only" in policy_ids
        assert agent_context["system_prompt"].startswith(CORPUS_AGENT_PROMPT)
        assert ROUTEDECK_POLICY_SECTION in agent_context["system_prompt"]
        assert ROUTEDECK_CONTEXT_SECTION in agent_context["system_prompt"]
