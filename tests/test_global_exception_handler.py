import asyncio
import logging

from starlette.requests import Request

from app.main import unhandled_exception_handler


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

    request.state.request_id = "test-request-500"

    return request


def test_unhandled_exception_handler_logs_exception(caplog):
    request = create_test_request()
    exc = RuntimeError("Unexpected internal failure")

    with caplog.at_level(logging.ERROR):
        response = asyncio.run(
            unhandled_exception_handler(request, exc)
        )

    assert response.status_code == 500
    assert response.body == (
        b'{"detail":"An unexpected error occurred."}'
    )

    record = caplog.records[0]

    assert record.message == "Unhandled request exception"
    assert record.request_id == "test-request-500"
    assert record.method == "POST"
    assert record.path == "/ask"
    assert record.status_code == 500
    assert record.exc_info[0] is RuntimeError
