from fastapi.testclient import TestClient

from app.core.rate_limiter import limiter
from app.main import app
from app.schemas.answer import AskResponse

client = TestClient(app)


def test_health_endpoint_is_not_rate_limited():
    limiter.reset()

    for _ in range(15):
        response = client.get("/health")

        assert response.status_code == 200


def test_ask_endpoint_returns_429_after_rate_limit(monkeypatch):
    limiter.reset()

    def fake_answer(query: str):
        return AskResponse(
            query=query,
            answer="Python is a programming language.",
            sources=[],
        )

    monkeypatch.setattr(
        "app.api.ask.general_answer_service.answer",
        fake_answer,
    )

    for _ in range(10):
        response = client.post(
            "/ask",
            json={
                "query": "What is Python?",
                "route": "general",
            },
        )
        assert response.status_code == 200

    response = client.post(
        "/ask",
        json={
            "query": "What is Python?",
            "route": "general",
        },
    )

    assert response.status_code == 429

    limiter.reset()


def test_search_endpoint_returns_429_after_rate_limit(monkeypatch):
    limiter.reset()

    def fake_retrieve(
        query: str,
        limit: int,
        document_id: str | None = None,
        project_id: str | None = None,
    ):
        return []

    monkeypatch.setattr(
        "app.api.search.retrieval_service.retrieve",
        fake_retrieve,
    )

    for _ in range(20):
        response = client.post(
            "/search",
            json={
                "query": "What is machine learning?",
                "limit": 3,
            },
        )
        assert response.status_code == 200

    response = client.post(
        "/search",
        json={
            "query": "What is machine learning?",
            "limit": 3,
        },
    )

    assert response.status_code == 429

    limiter.reset()


def test_upload_endpoint_returns_429_after_rate_limit():
    limiter.reset()

    for _ in range(5):
        response = client.post(
            "/documents/upload",
            files={
                "file": (
                    "test.pdf",
                    b"test content",
                    "application/pdf",
                )
            },
        )

        assert response.status_code == 400

    response = client.post(
        "/documents/upload",
        files={
            "file": (
                "test.pdf",
                b"test content",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 429

    limiter.reset()
