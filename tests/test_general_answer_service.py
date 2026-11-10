from app.schemas.answer import AskResponse
from app.services.general_answer_service import GeneralAnswerService


def test_general_answer_returns_generated_response(monkeypatch):
    service = GeneralAnswerService()

    def fake_generate(prompt, system_prompt):
        assert prompt == "What is Python?"
        assert "general-purpose" in system_prompt

        return "Python is a programming language."

    monkeypatch.setattr(
        service.llm_service,
        "generate",
        fake_generate,
    )

    result = service.answer("What is Python?")

    assert isinstance(result, AskResponse)
    assert result.query == "What is Python?"
    assert result.answer == "Python is a programming language."
    assert result.sources == []
