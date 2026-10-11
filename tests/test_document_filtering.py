from app.services.retrieval_service import RetrievalService

def test_retrieval_with_fake_document_id_returns_no_results():
    service = RetrievalService()

    results = service.retrieve(
        query = "What machine learning projects has this person worked on?",
        limit = 3,
        document_id = "11111111-1111-1111-1111-111111111111",
    )

    assert results == []