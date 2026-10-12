from app.services.bm25_service import BM25Service, tokenize


def test_tokenize_text():
    text = "Python and AWS Glue!"

    tokens = tokenize(text)

    assert tokens == ["python", "and", "aws", "glue"]


def test_bm25_returns_relevant_document_first():
    documents = [
        "Machine learning models using Python.",
        "AWS Glue ETL pipelines using PySpark.",
        "Voice assistant built with WebSockets.",
        "Image classifier built using TensorFlow.",
        "Docker deployment and cloud infrastructure.",
    ]

    service = BM25Service(documents)

    results = service.search(
        query="AWS Glue ETL pipelines",
        limit=3,
    )

    assert len(results) == 3
    assert results[0][0] == (
        "AWS Glue ETL pipelines using PySpark."
    )


def test_bm25_respects_result_limit():
    documents = [
        "Python machine learning",
        "AWS Glue pipelines",
        "TensorFlow image classification",
        "Docker deployment",
    ]

    service = BM25Service(documents)

    results = service.search(
        query="AWS",
        limit=2,
    )

    assert len(results) == 2