from types import SimpleNamespace

from app.schemas.retrieval import RetrievalResult
from app.services.hybrid_retrieval_service import HybridRetrievalService

DOCUMENT_ID = "test-document-123"


def make_record(chunk_index: int, text: str):
    return SimpleNamespace(
        payload={
            "document_id": DOCUMENT_ID,
            "chunk_index": chunk_index,
            "text": text,
            "start_char": chunk_index * 100,
            "end_char": chunk_index * 100 + len(text),
        }
    )


class FakeVectorStore:
    def __init__(self, records):
        self.records = records
        self.requested_document_id = None

    def get_chunks(self, document_id=None):
        self.requested_document_id = document_id

        if document_id is None:
            return self.records

        return [
            record
            for record in self.records
            if record.payload["document_id"] == document_id
        ]


class FakeDenseRetrieval:
    def __init__(self, results):
        self.results = results
        self.was_called = False

    def retrieve(self, query, limit=3, document_id=None):
        self.was_called = True
        return self.results[:limit]


class FakeRerankingService:
    def rerank(self, query, documents):
        print(f"\nReranking candidates: {len(documents)}")

        scores = []

        for index, document in enumerate(documents):
            score = (
                10.0
                if "AWS Glue ETL pipelines" in document
                else 1.0
            )
            scores.append((index, score))

        return sorted(
            scores,
            key=lambda item: (-item[1], item[0]),
        )


def test_hybrid_retrieval_combining_rankings():
    records = [
        make_record(5, "AWS Glue ETL pipelines using PySpark"),
        make_record(6, "AWS cloud data engineering with Glue"),
        make_record(2, "Generative AI and machine learning projects"),
    ]

    dense_results = [
        RetrievalResult(
            document_id=DOCUMENT_ID,
            chunk_index=2,
            text=records[2].payload["text"],
            score=0.90,
            start_char=200,
            end_char=200 + len(records[2].payload["text"]),
        ),
        RetrievalResult(
            document_id=DOCUMENT_ID,
            chunk_index=5,
            text=records[0].payload["text"],
            score=0.85,
            start_char=500,
            end_char=500 + len(records[0].payload["text"]),
        ),
    ]

    service = HybridRetrievalService.__new__(HybridRetrievalService)
    service.vector_store = FakeVectorStore(records)
    service.dense_retrieval = FakeDenseRetrieval(dense_results)
    service.reranking_service = FakeRerankingService()

    results = service.retrieve(
        query="AWS Glue ETL pipelines",
        limit=2,
        document_id=DOCUMENT_ID,
    )

    assert len(results) == 2
    assert results[0].chunk_index == 5
    assert results[0].score > 0
    assert all(result.document_id == DOCUMENT_ID for result in results)
    assert service.dense_retrieval.was_called
    assert service.vector_store.requested_document_id == DOCUMENT_ID


def test_hybrid_retrieval_returns_empty_when_no_chunk_exist():
    service = HybridRetrievalService.__new__(HybridRetrievalService)
    service.vector_store = FakeVectorStore([])
    service.dense_retrieval = FakeDenseRetrieval([])

    results = service.retrieve(
        query="AWS Glue",
        document_id="missing-document",
    )
    assert results == []
    assert not service.dense_retrieval.was_called


def test_hybrid_retrieval_returns_empty_when_no_candidates_match():
    records = [
        make_record(0, "Electricity motoring using IoT sensors"),
        make_record(1, "Education and machine learning projects"),
    ]

    service = HybridRetrievalService.__new__(HybridRetrievalService)
    service.vector_store = FakeVectorStore(records)
    service.dense_retrieval = FakeDenseRetrieval([])
    service.reranking_service = FakeRerankingService()

    results = service.retrieve(
        query="unrelatedxyzquery123",
        limit=3,
        document_id=DOCUMENT_ID
    )

    assert results == []
    assert service.dense_retrieval.was_called
