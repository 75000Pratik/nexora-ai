from app.services.embedding_service import EmbeddingService

def test_embedding_dimension():
    service = EmbeddingService()

    embedding = service.embed_text("Nexora is an AI knowledge intelligence platform.")

    assert len(embedding) == 384

def test_embedding_batch_size_matches_input():
    service = EmbeddingService()

    texts = [
        "Artificial Intelligence Systems",
        "Machine Learning Engineering",
        "Vector Search",
    ]    

    embeddings = service.embed_texts(texts)

    assert len(embeddings) == len(texts)

    for embedding in embeddings:
        assert len(embedding) == 384