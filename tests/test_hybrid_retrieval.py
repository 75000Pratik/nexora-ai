from types import SimpleNamespace

from app.schemas.retrieval import RetrievalResult
from app.services.hybrid_retrieval_service import HybridRetrievalService

DOCUMENT_ID = "test-document-123"


def make_record(
        chunk_index: int,
        text: str,
        project_id: str = "project-a",
):
    return SimpleNamespace(
        payload={
            "document_id": DOCUMENT_ID,
            "project_id": project_id,
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

    def get_chunks(self, document_id=None, project_id=None):
        self.requested_document_id = document_id
        self.requested_project_id = project_id

        records = self.records

        if document_id is not None:
            records = [
                record for record in records
                if record.payload["document_id"] == document_id
            ]

        if project_id is not None:
            records = [
                record for record in records
                if record.payload["project_id"] == project_id
            ]

        return records


class FakeDenseRetrieval:
    def __init__(self, results):
        self.results = results
        self.was_called = False

    def retrieve(self, query, limit=3, document_id=None, project_id=None):
        self.was_called = True
        self.requested_project_id = project_id
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


def test_hybrid_retrieval_filters_chunks_by_document_id():
    other_document_id = "another-document-456"

    records = [
        make_record(0, "AWS Glue ETL pipelines using PySpark"),
        SimpleNamespace(
            payload={
                "document_id": other_document_id,
                "chunk_index": 1,
                "text": "AWS Glue data engineering",
                "start_char": 100,
                "end_char": 100 + len("AWS Glue data engineering"),
            }
        ),
    ]

    service = HybridRetrievalService.__new__(HybridRetrievalService)
    service.vector_store = FakeVectorStore(records)
    service.dense_retrieval = FakeDenseRetrieval([])
    service.reranking_service = FakeRerankingService()

    results = service.retrieve(
        query="AWS Glue ETL pipelines",
        limit=3,
        document_id=DOCUMENT_ID,
    )

    assert results
    assert all(
        result.document_id == DOCUMENT_ID
        for result in results
    )
    assert service.vector_store.requested_document_id == DOCUMENT_ID


def test_hybrid_retrieval_can_disable_reranking():
    records = [
        make_record(0, "AWS Glue ETL pipelines using PySpark"),
        make_record(1, "Generative AI and machine learning projects"),
    ]

    dense_results = [
        RetrievalResult(
            document_id=DOCUMENT_ID,
            chunk_index=1,
            text=records[1].payload["text"],
            score=0.90,
            start_char=100,
            end_char=100 + len(records[1].payload["text"]),
        ),
        RetrievalResult(
            document_id=DOCUMENT_ID,
            chunk_index=0,
            text=records[0].payload["text"],
            score=0.80,
            start_char=0,
            end_char=len(records[0].payload["text"]),
        ),
    ]

    service = HybridRetrievalService.__new__(HybridRetrievalService)
    service.vector_store = FakeVectorStore(records)
    service.dense_retrieval = FakeDenseRetrieval(dense_results)

    class FailingRerankingService:
        def rerank(self, query, documents):
            raise AssertionError("Reranking should not be called")

    service.reranking_service = FailingRerankingService()

    results = service.retrieve(
        query="AWS Glue ETL pipelines",
        limit=2,
        document_id=DOCUMENT_ID,
        apply_reranking=False,
    )

    assert len(results) == 2
    assert {result.chunk_index for result in results} == {0, 1}
    assert all(result.score > 0 for result in results)


def test_hybrid_retrieval_reranking_changes_result_order():
    records = [
        make_record(0, "AWS Glue ETL pipelines using PySpark"),
        make_record(1, "Generative AI and machine learning projects"),
    ]

    dense_results = [
        RetrievalResult(
            document_id=DOCUMENT_ID,
            chunk_index=1,
            text=records[1].payload["text"],
            score=0.90,
            start_char=100,
            end_char=100 + len(records[1].payload["text"]),
        ),
        RetrievalResult(
            document_id=DOCUMENT_ID,
            chunk_index=0,
            text=records[0].payload["text"],
            score=0.80,
            start_char=0,
            end_char=len(records[0]. payload["text"]),
        ),
    ]

    service = HybridRetrievalService.__new__(HybridRetrievalService)
    service.vector_store = FakeVectorStore(records)
    service.dense_retrieval = FakeDenseRetrieval(dense_results)
    service.reranking_service = FakeRerankingService()

    baseline = service.retrieve(
        query="AWS Glue ETL pipelines",
        limit=2,
        document_id=DOCUMENT_ID,
        apply_reranking=False,
    )

    reranked = service.retrieve(
        query="AWS Glue ETL pipelines",
        limit=2,
        document_id=DOCUMENT_ID,
        apply_reranking=True,
    )

    assert len(baseline) == 2
    assert len(reranked) == 2
    assert baseline[0].chunk_index == 1
    assert reranked[0].chunk_index == 0
    assert baseline[0].chunk_index != reranked[0].chunk_index
    assert reranked[0].score == 10.0


def test_hybrid_retrieval_filters_chunks_by_project_id():
    records = [
        make_record(
            0,
            "AWS Glue ETL pipelines",
            project_id="project-a",
        ),
        make_record(
            1,
            "Generative AI and machine learning",
            project_id="project-b",
        ),
    ]

    service = HybridRetrievalService.__new__(HybridRetrievalService)
    service.vector_store = FakeVectorStore(records)
    service.dense_retrieval = FakeDenseRetrieval([])
    service.reranking_service = FakeRerankingService()

    results = service.retrieve(
        query="AWS Glue ETL pipelines",
        limit=3,
        project_id="project-a",
    )
    assert service.vector_store.requested_project_id == "project-a"
    assert service.dense_retrieval.requested_project_id == "project-a"
    assert all(
        result.document_id == DOCUMENT_ID
        for result in results
    )
    assert all(
        result.text != "Generative AI and machine learning"
        for result in results
    )
