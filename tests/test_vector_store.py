import pytest 

from app.schemas.chunk import DocumentChunk
from app.services.vector_store_service import VectorStoreService

def test_store_document_chunks_rejects_length_mismatch():
    service = VectorStoreService()

    chunks = [
        DocumentChunk(
            chunk_index=0,
            text="hello",
            start_char=0,
            end_char=5,
        )
    ]

    embeddings = []

    with pytest.raises(ValueError):
        service.store_document_chunks(
            document_id="123e4567-e89b-12d3-a456-426614174000",
            chunks=chunks,
            embeddings=embeddings,
        )