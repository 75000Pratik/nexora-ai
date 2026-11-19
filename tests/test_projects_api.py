import pytest

from uuid import UUID
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.models.document import Document
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


def test_create_project_successfully(client: TestClient):
    token = register_and_login(client, "project@example.com")

    response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Knowledge Base",
            "description": "My first project",
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body["name"] == "Knowledge Base"
    assert body["description"] == "My first project"
    assert "id" in body
    assert "user_id" in body


def test_create_project_rejects_whitespace_name(
        client: TestClient,
):
    token = register_and_login(
        client,
        "whitespace@example.com"
    )

    response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "   ",
            "description": "Invalid project",
        },
    )

    assert response.status_code == 422


def test_create_duplicate_project_returns_409(
    client: TestClient,
):
    token = register_and_login(client, "duplicate@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    payload = {"name": "Knowledge Base"}

    first = client.post("/projects", headers=headers, json=payload)
    second = client.post("/projects", headers=headers, json=payload)

    assert first.status_code == 201
    assert second.status_code == 409


def test_list_projects_returns_only_current_users_projects(
    client: TestClient,
):
    token_a = register_and_login(client, "usera@example.com")
    token_b = register_and_login(client, "userb@example.com")

    client.post(
        "/projects",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"name": "User A Project"},
    )

    client.post(
        "/projects",
        headers={"Authorization": f"Bearer {token_b}"},
        json={"name": "User B Project"},
    )

    response = client.get(
        "/projects",
        headers={"Authorization": f"Bearer {token_a}"},
    )

    assert response.status_code == 200

    projects = response.json()

    assert len(projects) == 1
    assert projects[0]["name"] == "User A Project"


def test_user_cannot_access_another_users_project(
    client: TestClient,
):
    token_a = register_and_login(client, "owner@example.com")
    token_b = register_and_login(client, "other@example.com")

    create_response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"name": "Private Project"},
    )

    project_id = create_response.json()["id"]

    response = client.get(
        f"/projects/{project_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )

    assert response.status_code == 404


def test_projects_require_authentication(client: TestClient):
    response = client.get("/projects")

    assert response.status_code == 401


def test_delete_empty_project_successfully(
    client: TestClient,
):
    token = register_and_login(
        client,
        "delete-empty@example.com",
    )

    headers = {"Authorization": f"Bearer {token}"}

    create_response = client.post(
        "/projects",
        headers=headers,
        json={"name": "Empty Project"},
    )

    assert create_response.status_code == 201

    project_id = create_response.json()["id"]

    response = client.delete(
        f"/projects/{project_id}",
        headers=headers,
    )

    assert response.status_code == 204

    get_response = client.get(
        f"/projects/{project_id}",
        headers=headers,
    )

    assert get_response.status_code == 404


def test_delete_project_with_documents_returns_409(
    client: TestClient,
    db_session: Session,
):
    token = register_and_login(
        client,
        "delete-with-documents@example.com",
    )

    headers = {"Authorization": f"Bearer {token}"}

    create_response = client.post(
        "/projects",
        headers=headers,
        json={"name": "Project With Documents"},
    )

    assert create_response.status_code == 201

    project_id = create_response.json()["id"]

    document = Document(
        filename="test.pdf",
        content_type="application/pdf",
        project_id=project_id,
        user_id=__import__("uuid").UUID(
            create_response.json()["user_id"]
        ),
        status="ready",
    )

    db_session.add(document)
    db_session.commit()

    response = client.delete(
        f"/projects/{project_id}",
        headers=headers,
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Cannot delete a project that contains documents. "
        "Delete its documents first."
    )
