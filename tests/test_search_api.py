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
