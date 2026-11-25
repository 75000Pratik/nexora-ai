import json
import logging

from app.core.logging_config import JSONFormatter


def test_json_formatter_includes_request_metadata():
    formatter = JSONFormatter()

    record = logging.LogRecord(
        name="nexora.test",
        level=logging.INFO,
        pathname="test_logging_config.py",
        lineno=10,
        msg="Request completed",
        args=(),
        exc_info=None,
    )

    record.request_id = "nexora-test-123"
    record.method = "GET"
    record.path = "/health"
    record.status_code = 200
    record.duration_ms = 12.5

    result = json.loads(formatter.format(record))

    assert result["level"] == "INFO"
    assert result["logger"] == "nexora.test"
    assert result["message"] == "Request completed"
    assert result["request_id"] == "nexora-test-123"
    assert result["method"] == "GET"
    assert result["path"] == "/health"
    assert result["status_code"] == 200
    assert result["duration_ms"] == 12.5
    assert "timestamp" in result
