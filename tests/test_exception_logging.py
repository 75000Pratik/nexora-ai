import asyncio
import logging

from starlette.requests import Request

from app.core.exceptions import (
    LLMServiceError,
    LLMServiceTimeoutError,
)
from app.main import (
    llm_error_handler,
    llm_timeout_handler,
)


def create_test_request() -> Request:
    request = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/ask",
            "headers": [],
            "query_string": b"",
            "server": ("testserver", 80),
            "client": ("testclient", 1234),
            "scheme": "http",
            "http_version": "1.1",
        }
    )

    request.state.request_id = "test-request-123"

    return request


def test_llm_timeout_handler_logs_exception(caplog):
    request = create_test_request()
    exc = LLMServiceTimeoutError("Provider timed out")

    with caplog.at_level(logging.ERROR):
        response = asyncio.run(
            llm_timeout_handler(request, exc)
        )

    assert response.status_code == 504
    assert response.body == (
        b'{"detail":"The AI service request timed out. Please try again."}'
    )

    record = caplog.records[0]

    assert record.message == "LLM service request timed out"
    assert record.request_id == "test-request-123"
    assert record.method == "POST"
    assert record.path == "/ask"
    assert record.status_code == 504
    assert record.exc_info[0] is LLMServiceTimeoutError


def test_llm_error_handler_logs_exception(caplog):
    request = create_test_request()
    exc = LLMServiceError("Provider unavailable")

    with caplog.at_level(logging.ERROR):
        response = asyncio.run(
            llm_error_handler(request, exc)
        )

    assert response.status_code == 502
    assert response.body == (
        b'{"detail":"The AI service is temporarily unavailable."}'
    )

    record = caplog.records[0]

    assert record.message == "LLM service unavailable"
    assert record.request_id == "test-request-123"
    assert record.method == "POST"
    assert record.path == "/ask"
    assert record.status_code == 502
    assert record.exc_info[0] is LLMServiceError
