
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
