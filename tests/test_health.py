import logging
import json

from uuid import UUID

from app.api import health

from fastapi.testclient import TestClient

from app.core.logging_config import JSONFormatter
from app.main import app


client = TestClient(app)


def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "nexora-ai",
        "environment": "development",
    }


def test_request_id_is_generated():
    response = client.get("/health")

    assert response.status_code == 200

    request_id = response.headers["X-Request-ID"]

    assert UUID(request_id)


def test_request_id_is_preserved():
    custom_request_id = "nexora-test-request-123"

    response = client.get(
        "/health",
        headers={"X-Request-ID": custom_request_id},
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == custom_request_id


def test_invalid_request_id_is_replaced():
    response = client.get(
        "/health",
        headers={"X-Request-ID": "invalid request id!"},
    )

    assert response.status_code == 200

    request_id = response.headers["X-Request-ID"]

    assert UUID(request_id)


def test_request_logging_includes_metadata(caplog):
    with caplog.at_level(
        logging.INFO,
        logger="app.core.middleware",
    ):
        response = client.get("/health")

    assert response.status_code == 200

    records = [
        record
        for record in caplog.records
        if record.name == "app.core.middleware"
        and record.getMessage() == "Request completed"
    ]

    assert len(records) == 1

    log_data = json.loads(JSONFormatter().format(records[0]))

    assert log_data["request_id"] == response.headers["X-Request-ID"]
    assert log_data["method"] == "GET"
    assert log_data["path"] == "/health"
    assert log_data["status_code"] == 200
    assert log_data["duration_ms"] >= 0


def test_readiness_check_when_dependencies_are_available(monkeypatch):
    class FakeConnection:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            pass

        def execute(self, statement):
            return 1

    class FakeResponse:
        def raise_for_status(self):
            pass

    monkeypatch.setattr(
        health.engine,
        "connect",
        lambda: FakeConnection(),
    )

    monkeypatch.setattr(
        health.vector_store.client,
        "get_collections",
        lambda timeout: [],
    )

    monkeypatch.setattr(
        health.httpx,
        "get",
        lambda url, timeout: FakeResponse(),
    )

    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "checks": {
            "database": True,
            "qdrant": True,
            "ollama": True,
        },
    }


def test_readiness_check_when_qdrant_is_unavailable(monkeypatch):
    class FakeConnection:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            pass

        def execute(self, statement):
            return 1

    class FakeResponse:
        def raise_for_status(self):
            pass

    monkeypatch.setattr(
        health.engine,
        "connect",
        lambda: FakeConnection(),
    )

    def raise_qdrant_error(timeout):
        raise RuntimeError("Qdrant unavailable")

    monkeypatch.setattr(
        health.vector_store.client,
        "get_collections",
        raise_qdrant_error,
    )

    monkeypatch.setattr(
        health.httpx,
        "get",
        lambda url, timeout: FakeResponse(),
    )

    response = client.get("/ready")

    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
        "checks": {
            "database": True,
            "qdrant": False,
            "ollama": True,
        },
    }
