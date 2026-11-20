import pytest
import jwt

from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from app.core.config import settings
from app.core.database import get_db
from app.main import app
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models.user import User

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


def test_register_user_successfully(client: TestClient):
    response = client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "password": "StrongPassword123!",
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body["email"] == "test@example.com"
    assert body["is_active"] is True
    assert "id" in body
    assert "password" not in body
    assert "password_hash" not in body

def test_register_normalizes_email(client: TestClient):
    response = client.post(
        "/auth/register",
        json={
            "email": "  TEST@EXAMPLE.COM  ",
            "password": "StrongPassword123!",
        },
    )

    assert response.status_code == 201
    assert response.json()["email"] == "test@example.com"

def test_register_duplicate_email_returns_conflict(
        client: TestClient,
):
    payload = {
        "email": "duplicate@example.com",
        "password": "StrongPassword123!",
    }

    first_response = client.post(
        "/auth/register",
        json=payload,
    )

    second_response = client.post(
        "/auth/register",
        json=payload,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409

    assert second_response.json()["detail"] == (
        "An account with this email already exists."
    )


def test_login_user_successfully(client: TestClient):
    registration_response = client.post(
        "/auth/register",
        json={
            "email": "login@example.com",
            "password": "StrongPassword123!",
        },
    )

    assert registration_response.status_code == 201

    login_response = client.post(
        "/auth/login",
        json={
            "email": "login@example.com",
            "password": "StrongPassword123!",
        },
    )

    assert login_response.status_code == 200

    body = login_response.json()

    assert "access_token" in body
    assert body["token_type"] == "bearer"
    assert len(body["access_token"]) > 0


def test_login_with_wrong_password_returns_401(
    client: TestClient,
):
    client.post(
        "/auth/register",
        json={
            "email": "wrongpass@example.com",
            "password": "StrongPassword123!",
        },
    )

    response = client.post(
        "/auth/login",
        json={
            "email": "wrongpass@example.com",
            "password": "WrongPassword123!",
        },
    )

    assert response.status_code == 401

    assert response.json()["detail"] == (
        "Invalid email or password."
    )


def test_get_current_user_with_valid_token(
    client: TestClient,
):
    client.post(
        "/auth/register",
        json={
            "email": "current@example.com",
            "password": "StrongPassword123!",
        },
    )

    login_response = client.post(
        "/auth/login",
        json={
            "email": "current@example.com",
            "password": "StrongPassword123!",
        },
    )

    access_token = login_response.json()["access_token"]

    response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert response.status_code == 200
    assert response.json()["email"] == "current@example.com"
    assert response.json()["is_active"] is True


def test_inactive_user_cannot_access_protected_endpoint(
    client: TestClient,
    db_session: Session,
):
    client.post(
        "/auth/register",
        json={
            "email": "inactive@example.com",
            "password": "StrongPassword123!",
        },
    )

    login_response = client.post(
        "/auth/login",
        json={
            "email": "inactive@example.com",
            "password": "StrongPassword123!",
        },
    )

    access_token = login_response.json()["access_token"]

    user = db_session.scalar(
        select(User).where(User.email == "inactive@example.com")
    )

    assert user is not None

    user.is_active = False
    db_session.flush()

    response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert response.status_code == 401


def test_get_current_user_without_token_returns_401(
    client: TestClient,
):
    response = client.get("/auth/me")

    assert response.status_code == 401

    assert response.json()["detail"] == (
        "Invalid or expired authentication token."
    )

    assert response.headers["www-authenticate"] == "Bearer"


def test_get_current_user_with_invalid_token_returns_401(
    client: TestClient,
):
    response = client.get(
        "/auth/me",
        headers={
            "Authorization": "Bearer invalid.jwt.token",
        },
    )

    assert response.status_code == 401

    assert response.json()["detail"] == (
        "Invalid or expired authentication token."
    )


def test_get_current_user_with_expired_token_returns_401(
    client: TestClient,
):
    expired_token = jwt.encode(
        {
            "sub": "12345678-1234-5678-1234-567812345678",
            "exp": datetime.now(timezone.utc) - timedelta(minutes=5),
        },
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {expired_token}",
        },
    )

    assert response.status_code == 401

    assert response.json()["detail"] == (
        "Invalid or expired authentication token."
    )
