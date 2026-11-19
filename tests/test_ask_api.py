from uuid import UUID, uuid4
from app.core.exceptions import (
    LLMServiceError,
    LLMServiceTimeoutError,
)
from app.schemas.answer import AskResponse
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.models.document import Document
from app.models.user import User
from app.main import app

test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    bind=test_engine,
    autocommit=False,
    autoflush=False,
)

Base.metadata.create_all(bind=test_engine)


@pytest.fixture
def db_session() -> Session:
    connection = test_engine.connect()
    transaction = connection.begin()

    db = TestingSessionLocal(bind=connection)

    try:
        yield db
    finally:
        db.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(db_session: Session):
    original_overrides = app.dependency_overrides.copy()

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(original_overrides)


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


def test_ask_endpoint_passes_project_id(
        client: TestClient,
        monkeypatch,
):
    token = register_and_login(client, "project-test@example.com")
    project_response = client.post(
        "/projects",
        json={"name": "Ask API Test Project"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert project_response.status_code == 201

    requested_project_id = project_response.json()["id"]

    def fake_answer(
        user_id: UUID,
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
        headers={"Authorization": f"Bearer {token}"},
    )
    print(response.json())
    assert response.status_code == 200

    body = response.json()

    assert body["query"] == "Explain the project architecture"
    assert body["answer"] == "This is a test answer."
    assert body["sources"] == []


def test_ask_endpoint_returns_general_answer(
        client: TestClient,
        monkeypatch,
):
    token = register_and_login(client, "general@example.com")

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
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    body = response.json()

    assert body["query"] == "What is Python?"
    assert body["answer"] == "Python is a programming language."
    assert body["sources"] == []


def test_project_id_overrides_general_route(
        client: TestClient,
        monkeypatch,
):
    token = register_and_login(client, "project-route@example.com")

    project_response = client.post(
        "/projects",
        json={"name": "Project Route Test"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert project_response.status_code == 201

    requested_project_id = project_response.json()["id"]

    def fake_answer(
            user_id: UUID,
            query: str,
            limit: int,
            document_id: str | None = None,
            project_id: str | None = None,
    ):
        assert project_id == requested_project_id

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
            "project_id": requested_project_id,
            "route": "general",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["answer"] == "Project-scoped answer."


def test_document_id_overrides_general_route(
        client: TestClient,
        db_session: Session,
        monkeypatch,
):
    token = register_and_login(
        client,
        "document-test@example.com",
    )

    user = db_session.query(User).filter_by(
        email="document-test@example.com"
    ).first()

    document_id = uuid4()

    document = Document(
        id=document_id,
        user_id=user.id,
        filename="test.pdf",
        content_type="application/pdf",
    )

    db_session.add(document)
    db_session.commit()

    def fake_answer(
        user_id: UUID,
        query: str,
        limit: int,
        document_id: str | None = None,
        project_id: str | None = None,
    ):
        assert document_id == str(document_id_expected)
        assert user_id == user.id

        return AskResponse(
            query=query,
            answer="Document-scoped answer.",
            sources=[],
        )

    document_id_expected = document_id

    monkeypatch.setattr(
        "app.api.ask.answer_service.answer",
        fake_answer,
    )

    response = client.post(
        "/ask",
        json={
            "query": "What is Python?",
            "document_id": str(document_id),
            "route": "general",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["answer"] == "Document-scoped answer."


def test_ask_endpoint_returns_502_for_llm_error(
        client: TestClient,
        monkeypatch,
):
    token = register_and_login(
        client,
        "llm-error@example.com",
    )

    def fake_answer(query: str):
        raise LLMServiceError("Internal provider connection details")

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
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 502
    assert response.json() == {
        "detail": "The AI service is temporarily unavailable."
    }


def test_ask_endpoint_returns_504_for_llm_timeout(
        client: TestClient,
        monkeypatch,
):
    token = register_and_login(
        client,
        "llm-timeout@example.com",
    )

    def fake_answer(query: str):
        raise LLMServiceTimeoutError("Internal timeout details")

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
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 504
    assert response.json() == {
        "detail": "The AI service request timed out. Please try again."
    }
