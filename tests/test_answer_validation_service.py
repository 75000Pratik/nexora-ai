from unittest.mock import Mock

from app.services.answer_validation_service import (
    AnswerValidationService,
)


def test_validator_accepts_supported_answer():
    service = AnswerValidationService()
    service.llm_service.generate = Mock(
        return_value="SUPPORTED"
    )

    result = service.is_supported(
        query="Which service did the RAG pipeline use?",
        answer="The RAG pipeline used Amazon Bedrock.",
        context="The RAG pipeline used Amazon Bedrock.",
    )

    assert result is True


def test_validator_rejects_unsupported_answer():
    service = AnswerValidationService()
    service.llm_service.generate = Mock(
        return_value="UNSUPPORTED"
    )

    result = service.is_supported(
        query="Which service did the RAG pipeline use?",
        answer=(
            "The RAG pipeline used Amazon Bedrock "
            "and Amazon EKS."
        ),
        context="The RAG pipeline used Amazon Bedrock.",
    )

    assert result is False


def test_validator_rejects_unexpected_verdict():
    service = AnswerValidationService()
    service.llm_service.generate = Mock(
        return_value="The answer seems correct."
    )

    result = service.is_supported(
        query="Which service did the RAG pipeline use?",
        answer="The RAG pipeline used Amazon Bedrock.",
        context="The RAG pipeline used Amazon Bedrock.",
    )

    assert result is False


def test_validator_fails_closed_on_llm_error():
    service = AnswerValidationService()
    service.llm_service.generate = Mock(
        side_effect=RuntimeError("Ollama unavailable")
    )

    result = service.is_supported(
        query="Which service did the RAG pipeline use?",
        answer="The RAG pipeline used Amazon Bedrock.",
        context="The RAG pipeline used Amazon Bedrock.",
    )

    assert result is False


def test_validator_rejects_answer_with_unsupported_service():
    service = AnswerValidationService()
    service.llm_service.generate = Mock(
        return_value="SUPPORTED"
    )

    result = service.is_supported(
        query="Which service did the RAG pipeline use?",
        answer=(
            "The RAG pipeline used Amazon Bedrock "
            "and Amazon EKS."
        ),
        context="The RAG pipeline used Amazon Bedrock.",
    )

    assert result is False


def test_validator_rejects_service_from_unrelated_project():
    service = AnswerValidationService()
    service.llm_service.generate = Mock(
        return_value="SUPPORTED"
    )

    result = service.is_supported(
        query="Which service did the RAG pipeline use?",
        answer=(
            "The RAG pipeline used Amazon Bedrock "
            "and Amazon EMR."
        ),
        context=(
            "The RAG pipeline used Amazon Bedrock. "
            "A separate project used Amazon EMR."
        ),
    )

    assert result is False


def test_validator_accepts_sentence_starting_with_the():
    service = AnswerValidationService()
    service.llm_service.generate = Mock(
        return_value="SUPPORTED"
    )

    result = service.is_supported(
        query="What does the system use?",
        answer="The system uses FastAPI.",
        context="the system uses FastAPI.",
    )

    assert result is True


def test_validator_rejects_unsupported_entity_without_calling_llm():
    service = AnswerValidationService()
    service.llm_service.generate = Mock(
        side_effect=AssertionError(
            "LLM should not be called."
        )
    )

    result = service.is_supported(
        query="Which service did the RAG pipeline use?",
        answer="The RAG pipeline used Amazon Bedrock and Amazon EKS.",
        context="The RAG pipeline used Amazon Bedrock.",
    )

    assert result is False


def test_validator_rejects_unrelated_project_entity_without_llm_call():
    service = AnswerValidationService()
    service.llm_service.generate = Mock(
        side_effect=AssertionError(
            "LLM should not be called."
        )
    )

    result = service.is_supported(
        query="Which service did the RAG pipeline use?",
        answer="The RAG pipeline used Amazon Bedrock and Amazon EMR.",
        context=(
            "The RAG pipeline used Amazon Bedrock. "
            "A separate project used Amazon EMR."
        ),
    )

    assert result is False


def test_validator_accepts_supported_verdict_with_whitespace():
    service = AnswerValidationService()
    service.llm_service.generate = Mock(
        return_value="  supported  \n"
    )

    result = service.is_supported(
        query="Which service did the RAG pipeline use?",
        answer="The RAG pipeline used Amazon Bedrock.",
        context="The RAG pipeline used Amazon Bedrock.",
    )

    assert result is True


def test_validator_rejects_empty_verdict():
    service = AnswerValidationService()
    service.llm_service.generate = Mock(
        return_value=""
    )

    result = service.is_supported(
        query="Which service did the RAG pipeline use?",
        answer="The RAG pipeline used Amazon Bedrock.",
        context="The RAG pipeline used Amazon Bedrock.",
    )

    assert result is False


def test_validator_rejects_whitespace_only_verdict():
    service = AnswerValidationService()
    service.llm_service.generate = Mock(
        return_value="   \n\t  "
    )

    result = service.is_supported(
        query="Which service did the RAG pipeline use?",
        answer="The RAG pipeline used Amazon Bedrock.",
        context="The RAG pipeline used Amazon Bedrock.",
    )

    assert result is False


def test_validator_sends_question_context_and_answer_to_llm():
    service = AnswerValidationService()
    captured = {}

    def fake_generate(prompt, system_prompt):
        captured["prompt"] = prompt
        captured["system_prompt"] = system_prompt
        return "SUPPORTED"

    service.llm_service.generate = Mock(
        side_effect=fake_generate
    )

    result = service.is_supported(
        query="Which service did the RAG pipeline use?",
        answer="The RAG pipeline used Amazon Bedrock.",
        context="The RAG pipeline used Amazon Bedrock.",
    )

    assert result is True
    assert "Which service did the RAG pipeline use?" in captured["prompt"]
    assert "Evidence context:" in captured["prompt"]
    assert "The RAG pipeline used Amazon Bedrock." in captured["prompt"]
    assert "Answer to verify:" in captured["prompt"]
    assert "strict factual claim verifier" in captured["system_prompt"]
