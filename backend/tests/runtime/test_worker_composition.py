from __future__ import annotations

import base64
import importlib
import sys

from cryptography.fernet import Fernet

from corpus.app.config import RouteDeckHostSettings
from corpus.app.infrastructure import SharedInfrastructureSettings
from corpus.auth.config import AuthSettings
from corpus.credentials import CredentialVaultSettings
from corpus.features.sources.config import SourceSettings
from corpus.jobs import DurableJobSettings
from corpus.persistence.config import CorpusDatabaseSettings
from corpus.runtime.config import CorpusRuntimeSettings


def test_application_worker_registers_every_product_task_once(
    tmp_path, monkeypatch
) -> None:
    settings = CorpusRuntimeSettings(
        host=RouteDeckHostSettings(
            routedeck_database_url=(
                f"sqlite+pysqlite:///{(tmp_path / 'routedeck.sqlite3').as_posix()}"
            ),
            routedeck_state_encryption_key=Fernet.generate_key().decode("ascii"),
            routedeck_instance_id="worker-composition-test",
            routedeck_review_ttl_seconds=300,
            routedeck_resume_capability_ttl_seconds=600,
            routedeck_worker_count=1,
            routedeck_browser_origins=("http://127.0.0.1:5199",),
        ),
        database=CorpusDatabaseSettings(
            url=f"sqlite+aiosqlite:///{(tmp_path / 'corpus.sqlite3').as_posix()}",
            migration_revision="0020_sandbox_deployment_mode",
        ),
        auth=AuthSettings(
            reset_secret="r" * 40,
            verification_secret="v" * 40,
            public_frontend_url="http://127.0.0.1:5199",
        ),
        sources=SourceSettings(data_root=tmp_path / "sources"),
        infrastructure=SharedInfrastructureSettings(
            jobs=DurableJobSettings(sqlite_path=tmp_path / "jobs.sqlite3"),
            credentials=CredentialVaultSettings(
                encoded_key=base64.urlsafe_b64encode(b"k" * 32).decode("ascii")
            ),
        ),
        ollama_base_url="http://127.0.0.1:11434",
        ollama_model="gemma4:latest",
    )
    monkeypatch.setattr(
        CorpusRuntimeSettings,
        "from_env",
        classmethod(lambda cls: settings),
    )
    sys.modules.pop("corpus.app.worker", None)

    worker = importlib.import_module("corpus.app.worker")

    registered = tuple(worker.huey._registry._registry)
    expected_suffixes = (
        ".process_source_revision",
        ".assemble_agent_build",
        ".generate_build_evaluation_set",
        ".run_evaluation_case",
        ".publish_agent_build",
    )
    assert len(registered) == len(expected_suffixes)
    assert all(
        sum(name.endswith(suffix) for name in registered) == 1
        for suffix in expected_suffixes
    )

    sys.modules.pop("corpus.app.worker", None)
