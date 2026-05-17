from backend.core.config import settings
from backend.services.agent.rag_service import RAGService


def test_rag_deterministic_embedding_matches_configured_dimension():
    service = RAGService()
    vector = service._deterministic_embedding("Generated API Catalog")

    assert len(vector) == settings.embedding_dimensions
    assert vector == service._deterministic_embedding("Generated API Catalog")
    assert vector != service._deterministic_embedding("Generated Execution Traces")


def test_rag_chunk_text_keeps_generated_catalog_searchable():
    service = RAGService()
    chunks = service._chunk_text("# Generated API Catalog\n\n## GET /store/products\n\n- Tool: list_products")

    assert chunks
    assert "GET /store/products" in chunks[0]
