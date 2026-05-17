from backend.core.config import settings
from backend.services.agent.memory_service import MemoryService


def test_memory_deterministic_embedding_matches_configured_dimension():
    service = MemoryService()
    vector = service._deterministic_embedding("remember Storefront uses public API")

    assert len(vector) == settings.embedding_dimensions
    assert vector == service._deterministic_embedding("remember Storefront uses public API")
    assert vector != service._deterministic_embedding("remember Admin needs bearer auth")
