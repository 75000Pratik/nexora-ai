import httpx
import pytest

from app.core.exceptions import (
    LLMServiceError,
    LLMServiceTimeoutError,
)
from app.services.llm_service import LLMService


def test_generate_returns_successful_answer(monkeypatch):
    service = LLMService()

    request = httpx.Request(
        "POST",
        "http://localhost:11434/api/chat",
    )
    response = httpx.Response(
        200,
        json={
            "message": {
                "content": "Python is a programming language. "
            }
        },
        request=request,
    )

    monkeypatch.setattr(
        "app.services.llm_service.httpx.post",
        lambda *args, **kwargs: response,
    )

    result = service.generate("What is Python?")

    assert result == "Python is a programming language."


def test_generate_handles_connection_error(monkeypatch):
    service = LLMService()

    def fake_post(*args, **kwargs):
        raise httpx.ConnectError(
            "Connection failed",
            request=httpx.Request(
                "POST",
                "http://localhost:11434/api/chat",
            ),
        )
    monkeypatch.setattr(
        "app.services.llm_service.httpx.post",
        fake_post,
    )

    with pytest.raises(LLMServiceError):
        service.generate("What is Python?")


def test_generate_handles_timeout(monkeypatch):
    service = LLMService()

    def fake_post(*args, **kwargs):
        raise httpx.TimeoutException(
            "Request timed out",
            request=httpx.Request(
                "POST",
                "http://localhost:11434/api/chat",
            ),
        )

    monkeypatch.setattr(
        "app.services.llm_service.httpx.post",
        fake_post,
    )

    with pytest.raises(LLMServiceTimeoutError):
        service.generate("What is Python?")


def test_generate_handles_http_error(monkeypatch):
    service = LLMService()

    request = httpx.Request(
        "POST",
        "http://localhost:11434/api/chat",
    )
    response = httpx.Response(
        500,
        request=request,
    )

    def fake_post(*args, **kwargs):
        return response

    monkeypatch.setattr(
        "app.services.llm_service.httpx.post",
        fake_post,
    )

    with pytest.raises(LLMServiceError):
        service.generate("What is Python?")


def test_generate_handles_invalid_json(monkeypatch):
    service = LLMService()

    request = httpx.Request(
        "POST",
        "http://localhost:11434/api/chat",
    )
    response = httpx.Response(
        200,
        content=b"invalid json",
        request=request,
    )

    monkeypatch.setattr(
        "app.services.llm_service.httpx.post",
        lambda *args, **kwargs: response,
    )

    with pytest.raises(LLMServiceError):
        service.generate("What is Python?")


def test_generate_handles_missing_message(monkeypatch):
    service = LLMService()

    request = httpx.Request(
        "POST",
        "http://localhost:11434/api/chat",
    )
    response = httpx.Response(
        200,
        json={},
        request=request,
    )

    monkeypatch.setattr(
        "app.services.llm_service.httpx.post",
        lambda *args, **kwargs: response,
    )

    with pytest.raises(LLMServiceError):
        service.generate("What is Python?")


def test_generate_handles_empty_answer(monkeypatch):
    service = LLMService()

    request = httpx.Request(
        "POST",
        "http://localhost:11434/api/chat",
    )
    response = httpx.Response(
        200,
        json={
            "message": {
                "content": "  "
            }
        },
        request=request,
    )

    monkeypatch.setattr(
        "app.services.llm_service.httpx.post",
        lambda *args, **kwargs: response,
    )

    with pytest.raises(LLMServiceError):
        service.generate("What is Python?")
