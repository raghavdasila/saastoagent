from langchain_core.language_models import BaseChatModel
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

from .config import CorpusRuntimeSettings


def create_chat_model(settings: CorpusRuntimeSettings) -> BaseChatModel:
    """Create exactly the explicitly selected provider model, without fallback."""

    if settings.model_provider == "ollama":
        assert settings.ollama_base_url is not None
        assert settings.ollama_model is not None
        return ChatOllama(
            model=settings.ollama_model,
            base_url=str(settings.ollama_base_url).rstrip("/"),
            temperature=0,
        )

    assert settings.openai_api_key is not None
    assert settings.openai_model is not None
    return ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        use_responses_api=True,
        reasoning_effort=settings.openai_reasoning_effort,
    )


__all__ = ["create_chat_model"]
