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


@pytest.mark.parametrize(
    "response_data",
    [
        [],
        {"message": []},
        {"message": {}},
        {"message": {"content": 123}},
        {"message": {"content": None}},
    ],
)
def test_generate_handles_malformed_response_structure(
    monkeypatch,
    response_data,
):
    service = LLMService()

    request = httpx.Request(
        "POST",
        "http://localhost:11434/api/chat",
    )
    response = httpx.Response(
        200,
        json=response_data,
        request=request,
    )

    monkeypatch.setattr(
        "app.services.llm_service.httpx.post",
        lambda *args, **kwargs: response,
    )

    with pytest.raises(LLMServiceError):
        service.generate("What is Python?")

def test_generate_sends_correct_request_payload(monkeypatch):
    service = LLMService()
    captured = {}

    request = httpx.Request(
        "POST",
        f"{service.base_url}/api/chat",
    )
    response = httpx.Response(
        200,
        json={
            "message": {
                "content": "Python is a programming language."
            }
        },
        request=request,
    )

    def fake_post(url, **kwargs):
        captured["url"] = url
        captured.update(kwargs)
        return response

    monkeypatch.setattr(
        "app.services.llm_service.httpx.post",
        fake_post,
    )

    service.generate(
        "What is Python?",
        system_prompt="You are a Python tutor.",
    )

    assert captured["url"] == f"{service.base_url}/api/chat"
    assert captured["json"]["model"] == service.model
    assert captured["json"]["messages"] == [
        {
            "role": "system",
            "content": "You are a Python tutor.",
        },
        {
            "role": "user",
            "content": "What is Python?",
        },
    ]
    assert captured["json"]["stream"] is False
    assert captured["json"]["options"]["temperature"] == 0
    assert captured["timeout"] == 120.0