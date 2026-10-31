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


def test_delete_document_chunks(monkeypatch):
    service = VectorStoreService()

    deleted_data = {}

    def fake_delete(**kwargs):
        deleted_data.update(kwargs)

    monkeypatch.setattr(
        service.client,
        "delete",
        fake_delete,
    )

    document_id = "123e4567-e89b-12d3-a456-426614174000"

    service.delete_document_chunks(document_id)

    assert deleted_data["collection_name"] == service.collection_name
    assert deleted_data["wait"] is True

    selector = deleted_data["points_selector"]
    conditions = selector.filter.must

    assert len(conditions) == 1
    assert conditions[0].key == "document_id"
    assert conditions[0].match.value == document_id
