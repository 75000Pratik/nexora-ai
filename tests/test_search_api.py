from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_search_endpoint_validation():
    response = client.post(
        "/search",
        json={
            "query": "",
            "limit": 3,
        },
    )

    assert response.status_code == 422


def test_search_endpoint_with_fake_document_id():
    response = client.post(
        "/search",
        json={
            "query": "What machine learning projects has this person worked on?",
            "document_id": "11111111-1111-1111-1111-111111111111",
            "limit": 3,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["query"] == (
        "What machine learning projects has this person worked on?"
    )
    assert body["results"] == []


def test_search_endpoint_passes_project_id(monkeypatch):
    requested_project_id = "project-a"

    def fake_retrieve(
        query: str,
        limit: int,
        document_id: str | None = None,
        project_id: str | None = None,
    ):
        assert project_id == requested_project_id
        return []

    monkeypatch.setattr(
        "app.api.search.retrieval_service.retrieve",
        fake_retrieve,
    )

    response = client.post(
        "/search",
        json={
            "query": "Explain the project architecture",
            "project_id": requested_project_id,
            "limit": 3,
        },
    )

    assert response.status_code == 200
    assert response.json()["results"] == []
