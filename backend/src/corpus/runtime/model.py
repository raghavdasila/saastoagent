from langchain_ollama import ChatOllama

from .config import CorpusRuntimeSettings


def create_ollama_chat_model(settings: CorpusRuntimeSettings) -> ChatOllama:
    """Create the native Ollama LangChain integration without fallback."""

    base_url = str(settings.ollama_base_url).rstrip("/")
    return ChatOllama(
        model=settings.ollama_model,
        base_url=base_url,
    )


__all__ = ["create_ollama_chat_model"]
