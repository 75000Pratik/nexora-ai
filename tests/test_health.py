import logging
import json

from uuid import UUID

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
