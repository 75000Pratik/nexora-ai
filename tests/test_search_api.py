from uuid import uuid4
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def register_and_login(
    client: TestClient,
    email: str,
) -> str:
    client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "StrongPassword123!",
        },
    )

    response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": "StrongPassword123!",
        },
    )

    assert response.status_code == 200

    return response.json()["access_token"]


def test_search_endpoint_validation():
    token = register_and_login(client, "search-validation@example.com")

    response = client.post(
        "/search",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "query": "",
            "limit": 3,
        },
    )

    assert response.status_code == 422


def test_search_endpoint_with_fake_document_id():
    token = register_and_login(client, "search-document@example.com")
    response = client.post(
        "/search",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "query": "What machine learning projects has this person worked on?",
            "document_id": "11111111-1111-1111-1111-111111111111",
            "limit": 3,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Document not found."


def test_search_endpoint_passes_project_id(monkeypatch):
    token = register_and_login(client, "search-project@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    create_response = client.post(
        "/projects",
        headers=headers,
        json={
            "name": f"Search Test Project {uuid4()}",
            "description": "Project for testing search",
        },
    )

    assert create_response.status_code == 201

    requested_project_id = create_response.json()["id"]

    def fake_retrieve(
        user_id,
        query: str,
        limit: int,
        document_id: str | None = None,
        project_id: str | None = None,
    ):
        assert str(user_id) == create_response.json()["user_id"]
        assert project_id == requested_project_id
        return []

    monkeypatch.setattr(
        "app.api.search.retrieval_service.retrieve",
        fake_retrieve,
    )

    response = client.post(
        "/search",
        headers=headers,
        json={
            "query": "Explain the project architecture",
            "project_id": requested_project_id,
            "limit": 3,
        },
    )

    assert response.status_code == 200
    assert response.json()["results"] == []
