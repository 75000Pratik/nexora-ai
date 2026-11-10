from fastapi.testclient import TestClient

from app.main import app
from app.schemas.answer import AskResponse

client = TestClient(app)


def test_ask_endpoint_passes_project_id(monkeypatch):
    requested_project_id = "project-a"

    def fake_answer(
        query: str,
        limit: int,
        document_id: str | None = None,
        project_id: str | None = None,
    ):
        assert project_id == requested_project_id

        return AskResponse(
            query=query,
            answer="This is a test answer.",
            sources=[],
        )

    monkeypatch.setattr(
        "app.api.ask.answer_service.answer",
        fake_answer,
    )

    response = client.post(
        "/ask",
        json={
            "query": "Explain the project architecture",
            "project_id": requested_project_id,
            "limit": 3,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["query"] == "Explain the project architecture"
    assert body["answer"] == "This is a test answer."
    assert body["sources"] == []


def test_ask_endpoint_returns_general_answer(monkeypatch):
    def fake_answer(query: str):
        assert query == "What is Python?"

        return AskResponse(
            query=query,
            answer="Python is a programming language.",
            sources=[],
        )

    monkeypatch.setattr(
        "app.api.ask.general_answer_service.answer",
        fake_answer,
    )

    response = client.post(
        "/ask",
        json={
            "query": "What is Python?",
            "route": "general",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["query"] == "What is Python?"
    assert body["answer"] == "Python is a programming language."
    assert body["sources"] == []


def test_project_id_overrides_general_route(monkeypatch):
    def fake_answer(
        query: str,
        limit: int,
        document_id: str | None = None,
        project_id: str | None = None,
    ):
        assert project_id == "project-a"

        return AskResponse(
            query=query,
            answer="Project-scoped answer.",
            sources=[],
        )

    monkeypatch.setattr(
        "app.api.ask.answer_service.answer",
        fake_answer,
    )

    response = client.post(
        "/ask",
        json={
            "query": "What is Python?",
            "project_id": "project-a",
            "route": "general",
        },
    )

    assert response.status_code == 200
    assert response.json()["answer"] == "Project-scoped answer."


def test_document_id_overrides_general_route(monkeypatch):
    def fake_answer(
            query: str,
            limit: int,
            document_id: str | None = None,
            project_id: str | None = None,
    ):
        assert document_id == "doc-123"

        return AskResponse(
            query=query,
            answer="Document-scoped answer.",
            sources=[],
        )

    monkeypatch.setattr(
        "app.api.ask.answer_service.answer",
        fake_answer,
    )

    response = client.post(
        "/ask",
        json={
            "query": "What is Python?",
            "document_id": "doc-123",
            "route": "general",
        },
    )

    assert response.status_code == 200
    assert response.json()["answer"] == "Document-scoped answer."
