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
