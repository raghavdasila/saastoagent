import os

from backend.core.langsmith import configure_langsmith_environment


def test_langsmith_environment_uses_saastoagent_project(monkeypatch):
    for name in ("LANGSMITH_TRACING", "LANGCHAIN_TRACING_V2", "LANGSMITH_API_KEY", "LANGSMITH_PROJECT"):
        monkeypatch.delenv(name, raising=False)

    configure_langsmith_environment(
        tracing=True,
        api_key="test-langsmith-key",
        project="saastoagent v0.1",
        endpoint="",
    )

    assert os.environ["LANGSMITH_TRACING"] == "true"
    assert os.environ["LANGCHAIN_TRACING_V2"] == "true"
    assert os.environ["LANGSMITH_API_KEY"] == "test-langsmith-key"
    assert os.environ["LANGSMITH_PROJECT"] == "saastoagent v0.1"


def test_langsmith_environment_preserves_explicit_project(monkeypatch):
    monkeypatch.setenv("LANGSMITH_PROJECT", "explicit-project")

    configure_langsmith_environment(
        tracing=True,
        api_key="test-langsmith-key",
        project="saastoagent v0.1",
        endpoint="",
    )

    assert os.environ["LANGSMITH_PROJECT"] == "explicit-project"
